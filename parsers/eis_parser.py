import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from tqdm import tqdm
from app.models import Tender

EIS_SEARCH_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

SEARCH_PARAMS = {
    "morphology": "on",
    "search-filter": "Дате размещения",
    "pageNumber": "1",
    "sortDirection": "false",
    "recordsPerPage": "_20",
    "showLotsInfoHidden": "false",
    "sortBy": "UPDATE_DATE",
    "fz44": "on",
    "priceFromGeneral": "5000000",
    "priceToGeneral": "20000000",
    "currencyIdGeneral": "-1",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

STOP_WORDS = [
    "услуги", "работы", "питание", "медицин", "фармацев",
    "вооружени", "разработк", "строительств", "ремонт",
    "лекарств", "хирург", "монтаж", "обслуживани",
]


def _passes_stop_words(title: str) -> bool:
    t = title.lower()
    for word in STOP_WORDS:
        if word in t:
            return False
    return True


def _parse_price(text: str) -> float:
    cleaned = (
        text.replace("\xa0", "")
            .replace(" ", "")
            .replace(" ", "")
            .replace(",", ".")
            .replace("₽", "")
            .strip()
    )
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


async def _fetch_page(session: aiohttp.ClientSession, page: int) -> str:
    params = {**SEARCH_PARAMS, "pageNumber": str(page)}
    try:
        async with session.get(
            EIS_SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status == 434:
                raise ConnectionError(
                    "ЕИС заблокировал IP с кодом 434.\n"
                    "Парсер нужно запускать только на российском сервере (Timeweb)."
                )
            if resp.status != 200:
                raise ConnectionError(f"ЕИС вернул неожиданный код {resp.status}")
            return await resp.text(encoding="utf-8", errors="replace")
    except aiohttp.ClientConnectorError as e:
        raise ConnectionError(f"Не удалось подключиться к zakupki.gov.ru: {e}")


def _parse_cards(html: str) -> list[Tender]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div.registry-entry__form")
    result = []

    for card in cards:
        try:
            number_el = card.select_one(".registry-entry__header-mid__number a")
            if not number_el:
                continue
            number = number_el.get_text(strip=True).replace("№", "").strip()

            title_el = card.select_one(".registry-entry__body-value")
            title = title_el.get_text(strip=True) if title_el else "Без названия"

            nmc_el = card.select_one(".price-block__value")
            nmc_text = nmc_el.get_text(strip=True) if nmc_el else "0"
            nmc = _parse_price(nmc_text)

            if nmc < 5_000_000 or nmc > 20_000_000:
                continue
            if not _passes_stop_words(title):
                continue

            customer_els = card.select(".registry-entry__body-href")
            customer = customer_els[0].get_text(strip=True) if customer_els else "Не указан"

            region_els = card.select(".registry-entry__body-block .registry-entry__body-value")
            region = region_els[-1].get_text(strip=True) if region_els else "Не указан"

            date_els = card.select(".data-block__value")
            publish_date = date_els[0].get_text(strip=True) if date_els else datetime.now().strftime("%d.%m.%Y")
            end_date = date_els[1].get_text(strip=True) if len(date_els) > 1 else None

            href = number_el.get("href", "")
            url = f"https://zakupki.gov.ru{href}" if href else (
                f"https://zakupki.gov.ru/epz/order/notice/ep44/view/common-info.html?regNumber={number}"
            )

            result.append(Tender(
                number=number,
                title=title,
                nmc=nmc,
                customer=customer,
                region=region,
                publish_date=publish_date,
                end_date=end_date,
                url=url,
            ))
        except Exception:
            continue

    return result


async def parse_eis(pages: int = 3) -> list[Tender]:
    """
    Загружает тендеры с zakupki.gov.ru.
    Вызывает ConnectionError при блокировке — никогда не возвращает фейковые данные.
    """
    print(f"⏳ 1/3: Подключаюсь к ЕИС zakupki.gov.ru…", flush=True)

    all_tenders: list[Tender] = []
    async with aiohttp.ClientSession() as session:
        for page in tqdm(range(1, pages + 1), desc="Страницы ЕИС", unit="стр"):
            html = await _fetch_page(session, page)
            page_tenders = _parse_cards(html)
            all_tenders.extend(page_tenders)
            if page < pages:
                await asyncio.sleep(1.5)

    print(f"✅ 3/3: Получено {len(all_tenders)} тендеров после фильтрации", flush=True)
    return all_tenders
