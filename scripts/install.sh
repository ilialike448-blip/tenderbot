#!/usr/bin/env bash
set -e
source "$(dirname "$0")/progress.sh"

PROJECT_DIR="/opt/tenderbot"

section "Установка TenderBot на сервере"

step "Обновляю список пакетов" apt-get update -q
step "Ставлю Python 3.11 и pip" apt-get install -y -q python3.11 python3.11-venv python3-pip
step "Создаю папку проекта" mkdir -p "$PROJECT_DIR"

section "Клонирование репозитория"
if [ -d "$PROJECT_DIR/.git" ]; then
  step "Обновляю код из GitHub" git -C "$PROJECT_DIR" pull origin main
else
  printf "${Y}⏳ Клонирую репозиторий…${N}\n"
  git clone https://github.com/ВАШЕ_ИМЯ/tenderbot.git "$PROJECT_DIR"
  printf "${G}✅ Репозиторий склонирован${N}\n"
fi

cd "$PROJECT_DIR"
step "Создаю виртуальное окружение" python3.11 -m venv venv

section "Установка зависимостей"
printf "${Y}⏳ Устанавливаю Python-библиотеки…${N}\n"
"$PROJECT_DIR/venv/bin/pip" install --upgrade pip -q
"$PROJECT_DIR/venv/bin/pip" install -r requirements.txt
printf "${G}✅ Зависимости установлены${N}\n"

section "Настройка автозапуска (systemd)"
step "Копирую service-файл" cp deploy/tender_bot.service /etc/systemd/system/
step "Перечитываю конфигурацию systemd" systemctl daemon-reload
step "Включаю автозапуск" systemctl enable tender_bot

section "Готово ✅"
printf "\nДальше:\n"
printf "  1. Создай файл .env: ${Y}nano $PROJECT_DIR/.env${N}\n"
printf "  2. Запусти бота:    ${Y}systemctl start tender_bot${N}\n"
printf "  3. Проверь статус:  ${Y}systemctl status tender_bot${N}\n"
