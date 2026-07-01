#!/bin/bash
# Установка и запуск TenderPortal на сервере Timeweb
# Запускать из /opt/tenderbot после git pull

set -e

echo "=== 1. Обновление Python-зависимостей ==="
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "=== 2. Сборка Mini App ==="
cd miniapp
if ! command -v node &>/dev/null; then
    echo "Устанавливаю Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
npm install --silent
npm run build
cd ..

echo "=== 3. Cloudflare Tunnel ==="
if ! command -v cloudflared &>/dev/null; then
    echo "Устанавливаю cloudflared..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
         -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
fi

echo ""
echo "=== ВАЖНО: Запусти туннель и скопируй URL ==="
echo "Команда для запуска туннеля:"
echo "  cloudflared tunnel --url http://localhost:8000"
echo ""
echo "Ты увидишь строку вида:"
echo "  https://abc-xyz.trycloudflare.com"
echo ""
echo "Этот URL нужно:"
echo "  1. Записать в .env:  PORTAL_BASE_URL=https://abc-xyz.trycloudflare.com"
echo "  2. Установить в BotFather: /setmenubutton → выбери @tender1212bot → URL приложения"
echo "  3. Перезапустить портал: systemctl restart tenderportal"
echo ""
echo "=== 4. Настройка systemd ==="
cp deploy/tenderportal.service /etc/systemd/system/tenderportal.service
systemctl daemon-reload
systemctl enable tenderportal
systemctl start tenderportal

echo ""
echo "=== Готово! ==="
echo "Статус портала: systemctl status tenderportal"
echo "Логи портала:   journalctl -u tenderportal -f"
