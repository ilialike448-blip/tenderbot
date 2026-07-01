#!/bin/bash
# Запуск Cloudflare Tunnel в фоне как systemd-сервис
# Для "моста на домен": когда купишь домен — просто замени PORTAL_BASE_URL в .env
# и перенастрой Cloudflare через dashboard.cloudflare.com (без изменений кода)

cat > /etc/systemd/system/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel for TenderPortal
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:8000 --no-autoupdate
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cloudflared
systemctl start cloudflared

echo "Туннель запущен. Смотри URL в логах:"
echo "  journalctl -u cloudflared -f"
echo ""
echo "Как только увидишь URL вида https://xxx.trycloudflare.com:"
echo "  nano /opt/tenderbot/.env  # → PORTAL_BASE_URL=https://xxx.trycloudflare.com"
echo "  systemctl restart tenderportal"
