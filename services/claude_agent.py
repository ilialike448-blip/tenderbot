import os
import json
import re
import anthropic
from app.models import AnalysisResult

_client: anthropic.Anthropic | None = None

TRIAGE_MODEL = os.getenv("CLAUDE_MODEL_TRIAGE", "claude-haiku-4-5")
FINAL_MODEL = os.getenv("CLAUDE_MODEL_FINAL", "claude-sonnet-4-6")

RATING_EMOJI = {
    "fire": "🔥",
    "ok": "✅",
    "warn": "⚠️",
    "bad": "❌",
}

BUSINESS_PROFILE = """
Профиль бизнеса:
- Статус: ИП, карго-доставка товаров из Китая
- Цель: маржа от 30% чистыми
- Приоритет регионов: ЦФО, СЗФО, ПФО, ЮФО, СКФО
- Берём только ПОСТАВКУ ТОВАРОВ (не услуги, не работы)
- Исключаем: питание, медицину, фармацевтику, вооружение, IT-разработку, строительство
"""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.proxyapi.ru/anthropic"),
        )
    return _client


def triage_tender(title: str, nmc: float) -> bool:
    """Быстрый предфильтр через Haiku. Дёшево — 1-2 токена в ответе."""
    client = _get_client()
    prompt = (
        f'Тендер: "{title}", НМЦ: {nmc:,.0f} ₽.\n'
        f"{BUSINESS_PROFILE}\n"
        f"Подходит ли этот тендер? Ответь ТОЛЬКО одним словом: да или нет."
    )
    resp = client.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=5,
        messages=[{"role": "user", "content": prompt}],
    )
    return "да" in resp.content[0].text.lower()


def analyze_tender(
    number: str,
    title: str,
    nmc: float,
    customer: str,
    region: str,
) -> AnalysisResult:
    """Детальный анализ через Sonnet. Вызывается только для прошедших триаж."""
    client = _get_client()
    prompt = f"""Проанализируй тендер для ИП (карго-доставка товаров из Китая).

Данные тендера:
- Номер: {number}
- Название: {title}
- НМЦ: {nmc:,.0f} ₽
- Заказчик: {customer}
- Регион: {region}

{BUSINESS_PROFILE}

Рассчитай:
1. Себестоимость: закупка в Китае (~50% НМЦ) + таможня 15% + карго 8% + логистика 5% + накладные 5%
2. Маржу в % от НМЦ
3. Главные риски (сертификация, конкуренция, сроки)
4. Рейтинг: fire (маржа >40%), ok (30-40%), warn (20-30%), bad (<20% или нельзя участвовать)

Ответь строго в формате JSON (без лишнего текста):
{{
  "cost_estimate": число_рублей,
  "margin_percent": число,
  "rating": "fire|ok|warn|bad",
  "risks": ["риск1", "риск2", "риск3"],
  "summary": "2-3 предложения: вывод и рекомендация"
}}"""

    resp = client.messages.create(
        model=FINAL_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    text = resp.content[0].text
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if not json_match:
        raise ValueError(f"Claude не вернул JSON. Ответ: {text[:200]}")

    data = json.loads(json_match.group())

    return AnalysisResult(
        tender_number=number,
        cost_estimate=float(data["cost_estimate"]),
        margin_percent=float(data["margin_percent"]),
        rating=data["rating"],
        risks=data.get("risks", []),
        summary=data.get("summary", ""),
    )
