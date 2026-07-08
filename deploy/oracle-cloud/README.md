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

Two Always Free-eligible paths - pick one (the console labels the eligible
option "Always Free-eligible" directly under the shape, which is the
authoritative confirmation, since Oracle has changed these numbers before):

**Option A - Ampere A1.Flex (more headroom, recommended if available)**
- **Image**: Canonical Ubuntu 22.04 (or 24.04)
- **Shape**: "Change shape" -> Ampere -> `VM.Standard.A1.Flex` -> set
  **2 OCPU / 12 GB memory**. As of June 2026 Oracle halved this tier's total
  Always Free allowance from 4 OCPU/24GB to **2 OCPU/12GB total** - so this
  configuration uses the *entire* free allowance; don't create a second A1
  instance on top of it. If A1 capacity is unavailable in your region, use
  Option B.
- Use `setup.sh` (below) after creation.

**Option B - E2.1.Micro (always available, less headroom)**
- **Image**: Oracle Linux 9 (or Ubuntu, if you prefer - just match the script)
- **Shape**: `VM.Standard.E2.1.Micro` - 1 OCPU / 1 GB RAM, "Always
  Free-eligible". You can run up to 2 of these free.
- 1GB RAM is tight for pandas/xgboost/scikit-learn running alongside nginx -
  use `cloud-init-oraclelinux9.sh` (below), which adds a 2GB swap file.

For either option:
- **Networking**: keep the default VCN, and make sure "Assign a public IPv4
  address" is checked (leave it as ephemeral, not reserved - simpler and free).
- **Add SSH keys**: generate a keypair if you don't have one:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/pocketify_oci
  ```
  Paste the contents of `~/.ssh/pocketify_oci.pub` into the console.
- Leave the boot volume at its default size (~50GB) - Always Free includes
  200GB of combined block storage, so the default is well within budget.
- **Optional shortcut for Option B**: paste the full contents of
  `cloud-init-oraclelinux9.sh` into the "Paste cloud-init script" field
  during creation - it runs automatically on first boot and does everything
  in steps 4-5 below for you, except the two manual steps it prints at the
  end (VCN firewall rule + real credentials).
- Click **Create**. Note the public IP once it's running.

## 3. Open the firewall (the most common Oracle Cloud gotcha)

OCI blocks traffic in two places - you must open **both**:

1. **VCN Security List** (console): Networking -> Virtual Cloud Networks ->
   your VCN -> Security Lists -> Default Security List -> Add Ingress Rules:
   - Source CIDR `0.0.0.0/0`, IP Protocol TCP, Destination Port `80`
2. **Host firewall**: handled automatically by `setup.sh` (ufw, Ubuntu) or
   `cloud-init-oraclelinux9.sh` (firewalld, Oracle Linux) below.

Skipping step 1 is the #1 reason people can't reach their OCI web server.

## 4. Deploy the app

If you used the cloud-init paste option for Option B, this already happened
at first boot - skip to step 5. Otherwise, SSH in and run the setup script
that matches your image:

**Ubuntu (Option A or a Ubuntu-based Option B):**
```bash
ssh -i ~/.ssh/pocketify_oci ubuntu@<your-vm-public-ip>
curl -fsSL https://raw.githubusercontent.com/arulfrances/pocketify/main/deploy/oracle-cloud/setup.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

**Oracle Linux 9 (Option B), if you didn't use the cloud-init paste:**
```bash
ssh -i ~/.ssh/pocketify_oci opc@<your-vm-public-ip>
curl -fsSL https://raw.githubusercontent.com/arulfrances/pocketify/main/deploy/oracle-cloud/cloud-init-oraclelinux9.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

Either script installs Python/nginx, clones the repo to `/opt/pocketify`,
creates a venv, installs dependencies, and sets up two systemd services
(`pocketify-api`, `pocketify-bot`) plus an nginx reverse proxy on port 80.
The Oracle Linux variant also adds a 2GB swap file and configures
firewalld/SELinux instead of ufw.

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
