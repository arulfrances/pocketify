#!/bin/bash
# Cloud-init user-data for Oracle Linux 9 on a VM.Standard.E2.1.Micro
# (1 OCPU / 1GB RAM) Always Free instance. Paste this whole file into the
# "Paste cloud-init script" field when creating the instance in the OCI
# console - it runs once automatically on first boot.
set -euo pipefail
exec > /var/log/pocketify-cloudinit.log 2>&1

REPO_URL="https://github.com/arulfrances/pocketify.git"
BRANCH="main"
APP_DIR="/opt/pocketify"
APP_USER="pocketify"

# 1GB RAM is tight for pandas/xgboost/scikit-learn - add 2GB swap.
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

dnf install -y python3 python3-pip git nginx firewalld policycoreutils-python-utils
systemctl enable --now firewalld

id "$APP_USER" &>/dev/null || useradd --system --create-home --home-dir "$APP_DIR" --shell /sbin/nologin "$APP_USER"

sudo -u "$APP_USER" git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" gunicorn

sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

cat > /etc/systemd/system/pocketify-api.service <<'EOF'
[Unit]
Description=Pocketify FastAPI dashboard/API
After=network.target

[Service]
Type=simple
User=pocketify
Group=pocketify
WorkingDirectory=/opt/pocketify
EnvironmentFile=/opt/pocketify/.env
ExecStart=/opt/pocketify/venv/bin/gunicorn -w 1 -k uvicorn.workers.UvicornWorker src.api.monitor_api:app --bind 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/pocketify-bot.service <<'EOF'
[Unit]
Description=Pocketify Telegram signal alert bot
After=network.target

[Service]
Type=simple
User=pocketify
Group=pocketify
WorkingDirectory=/opt/pocketify
EnvironmentFile=/opt/pocketify/.env
ExecStart=/opt/pocketify/venv/bin/python signal_alert_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/nginx/conf.d/pocketify.conf <<'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

# SELinux blocks nginx from proxying to a backend port unless told otherwise.
setsebool -P httpd_can_network_connect 1

systemctl daemon-reload
systemctl enable --now pocketify-api pocketify-bot nginx

firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload

echo "Pocketify cloud-init setup complete."
echo "Remaining manual steps: open TCP/80 in the OCI VCN Security List (console-level, this script cannot do it), then edit /opt/pocketify/.env with real credentials and run: systemctl restart pocketify-api pocketify-bot"
