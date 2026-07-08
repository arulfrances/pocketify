# Deploying Pocketify on Oracle Cloud (Always Free)

Oracle's "Always Free" tier includes a compute shape that never expires and
never charges you (as opposed to the 30-day free trial credits). This runs
both the FastAPI dashboard and the Telegram signal bot as real background
services with no cold starts and no sleep-on-idle.

## 1. Create the account (one-time, in your browser)

1. Go to https://www.oracle.com/cloud/free/ and sign up. A card is required
   for identity verification but the Always Free shapes are never billed.
2. Pick your home region carefully - **you cannot change it later** and
   Always Free resources are tied to it. Any region works; pick one close to
   India for lower latency (e.g. Mumbai/Hyderabad if available in your
   signup flow).
3. Wait for the account to finish provisioning (a few minutes to a few hours).

## 2. Create the VM

In the OCI Console: **Compute -> Instances -> Create Instance**

- **Name**: `pocketify`
- **Image**: Canonical Ubuntu 22.04 (or 24.04)
- **Shape**: click "Change shape" -> Ampere -> **VM.Standard.A1.Flex** -> set
  2 OCPU / 12 GB memory (the Always Free allowance is up to 4 OCPU / 24GB
  total, shareable across instances). If A1 capacity is unavailable in your
  region, `VM.Standard.E2.1.Micro` (AMD, always free, 1 OCPU/1GB) also works,
  just less headroom for the ML model.
- **Networking**: keep the default VCN, and make sure "Assign a public IPv4
  address" is checked.
- **Add SSH keys**: generate a keypair if you don't have one:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/pocketify_oci
  ```
  Paste the contents of `~/.ssh/pocketify_oci.pub` into the console.
- Click **Create**. Note the public IP once it's running.

## 3. Open the firewall (the most common Oracle Cloud gotcha)

OCI blocks traffic in two places - you must open **both**:

1. **VCN Security List** (console): Networking -> Virtual Cloud Networks ->
   your VCN -> Security Lists -> Default Security List -> Add Ingress Rules:
   - Source CIDR `0.0.0.0/0`, IP Protocol TCP, Destination Port `80`
2. **Host firewall (ufw)**: handled automatically by `setup.sh` below.

Skipping step 1 is the #1 reason people can't reach their OCI web server.

## 4. Deploy the app

SSH into the instance and run the setup script:

```bash
ssh -i ~/.ssh/pocketify_oci ubuntu@<your-vm-public-ip>
curl -fsSL https://raw.githubusercontent.com/arulfrances/pocketify/main/deploy/oracle-cloud/setup.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

This installs Python/nginx, clones the repo to `/opt/pocketify`, creates a
venv, installs dependencies, and sets up two systemd services
(`pocketify-api`, `pocketify-bot`) plus an nginx reverse proxy on port 80.

## 5. Add real credentials and train the model

```bash
sudo nano /opt/pocketify/.env   # fill in broker keys, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_SECRET
sudo -u pocketify /opt/pocketify/venv/bin/python /opt/pocketify/main_pipeline.py
sudo systemctl restart pocketify-api pocketify-bot
```

Visit `http://<your-vm-public-ip>/` - the dashboard should be live.

## Operating it afterwards

```bash
sudo systemctl status pocketify-api pocketify-bot   # check health
sudo journalctl -u pocketify-api -f                 # tail API logs
sudo journalctl -u pocketify-bot -f                 # tail bot logs
sudo ./setup.sh                                     # re-run anytime to pull latest code + restart
```

## Optional: HTTPS with a free domain

If you point a domain at the VM's public IP, add HTTPS with Certbot:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```
