#!/usr/bin/env bash
set -e
source "$(dirname "$0")/progress.sh"

PROJECT_DIR="/opt/tenderbot"
cd "$PROJECT_DIR"

section "Запуск TenderBot"

if [ ! -f ".env" ]; then
  printf "${R}❌ Файл .env не найден!${N}\n"
  printf "Создай его командой: ${Y}cp .env.example .env && nano .env${N}\n"
  exit 1
fi

step "Проверяю виртуальное окружение" test -f venv/bin/python
step "Проверяю подключение к ЕИС" curl -s -o /dev/null -w "%{http_code}" https://zakupki.gov.ru | grep -q "200\|301\|302\|434"

printf "${Y}⏳ Запускаю бота…${N}\n"
source .env
exec venv/bin/python run.py
