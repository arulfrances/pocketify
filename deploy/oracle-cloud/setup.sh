#!/usr/bin/env bash
# Sets up Pocketify (ProStock) on a fresh Oracle Cloud Always Free VM
# (tested against Ubuntu 22.04/24.04 images).
#
# Usage (as a user with sudo, e.g. the default 'ubuntu' user):
#   curl -fsSL https://raw.githubusercontent.com/arulfrances/pocketify/main/deploy/oracle-cloud/setup.sh -o setup.sh
#   chmod +x setup.sh
#   sudo ./setup.sh
#
# Safe to re-run: pulls latest code and restarts services each time.

set -euo pipefail

REPO_URL="https://github.com/arulfrances/pocketify.git"
BRANCH="main"
APP_DIR="/opt/pocketify"
APP_USER="pocketify"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this with sudo: sudo ./setup.sh" >&2
    exit 1
fi

echo "==> Installing system packages"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git nginx ufw

echo "==> Creating service user '$APP_USER'"
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --create-home --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
fi

echo "==> Fetching application code"
if [ -d "$APP_DIR/.git" ]; then
    sudo -u "$APP_USER" git -C "$APP_DIR" fetch origin "$BRANCH"
    sudo -u "$APP_USER" git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
    sudo -u "$APP_USER" git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

echo "==> Creating virtualenv and installing dependencies"
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install gunicorn

if [ ! -f "$APP_DIR/.env" ]; then
    echo "==> Creating .env from .env.example - EDIT THIS with real credentials before going live"
    sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
fi

echo "==> Installing systemd services"
cp "$APP_DIR/deploy/oracle-cloud/pocketify-api.service" /etc/systemd/system/pocketify-api.service
cp "$APP_DIR/deploy/oracle-cloud/pocketify-bot.service" /etc/systemd/system/pocketify-bot.service
systemctl daemon-reload
systemctl enable pocketify-api pocketify-bot
systemctl restart pocketify-api pocketify-bot

echo "==> Configuring nginx reverse proxy (port 80 -> 127.0.0.1:8000)"
cp "$APP_DIR/deploy/oracle-cloud/nginx-pocketify.conf" /etc/nginx/sites-available/pocketify
ln -sf /etc/nginx/sites-available/pocketify /etc/nginx/sites-enabled/pocketify
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "==> Configuring host firewall (ufw)"
ufw allow OpenSSH
ufw allow "Nginx HTTP"
ufw --force enable

echo ""
echo "=========================================================================="
echo "Done. Remaining manual steps:"
echo "1. Edit $APP_DIR/.env with your real broker/Telegram credentials, then:"
echo "     sudo systemctl restart pocketify-api pocketify-bot"
echo "2. In the OCI console, open an ingress rule for TCP port 80 on this"
echo "   instance's subnet Security List (Networking -> Virtual Cloud Networks"
echo "   -> your VCN -> Security Lists -> Add Ingress Rule -> 0.0.0.0/0, TCP, 80)."
echo "   ufw alone is not enough - OCI blocks at the VCN level too."
echo "3. Once a model is trained (run: sudo -u $APP_USER $APP_DIR/venv/bin/python"
echo "   $APP_DIR/main_pipeline.py), the dashboard at http://<your-vm-public-ip>/"
echo "   will show live predictions."
echo "=========================================================================="