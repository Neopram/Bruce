# Bruce AI - Oracle Cloud Free Tier Deployment

Deploy Bruce AI on Oracle Cloud's Always Free Tier for a permanently free, 24/7 AI assistant.

## What You Get (Free Forever)

- **4 ARM CPU cores** (Ampere A1)
- **24 GB RAM** (enough for Ollama + 7B model + Bruce)
- **200 GB storage**
- No expiration, no surprise charges

## Step-by-Step Guide

### 1. Create Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and click "Sign Up"
2. Provide email, name, and a credit card (verification only, you will not be charged)
3. Select your **Home Region** (choose the closest one; it cannot be changed later)
4. Wait for account activation (usually a few minutes)

### 2. Create the Always Free ARM VM

1. Go to **Compute > Instances > Create Instance**
2. Configure:
   - **Name**: `bruce-ai`
   - **Image**: Ubuntu 22.04 (Canonical)
   - **Shape**: Click "Change Shape" > Ampere (ARM) > `VM.Standard.A1.Flex`
     - OCPUs: **4**
     - Memory: **24 GB**
   - **Networking**: Use default VCN or create one. Ensure "Assign a public IPv4 address" is checked
   - **SSH Key**: Upload your public key or let Oracle generate one (save the private key!)
   - **Boot Volume**: 200 GB (max free tier)
3. Click **Create** and wait for it to start (may take a few minutes; if capacity is unavailable, try a different availability domain or retry later)

### 3. Configure Network Security

In the Oracle Cloud Console:

1. Go to **Networking > Virtual Cloud Networks > your VCN > Security Lists > Default Security List**
2. Add **Ingress Rules**:

| Source CIDR   | Protocol | Dest Port | Description      |
|---------------|----------|-----------|------------------|
| 0.0.0.0/0     | TCP      | 80        | HTTP             |
| 0.0.0.0/0     | TCP      | 443       | HTTPS            |
| 0.0.0.0/0     | TCP      | 8000      | Bruce API direct |

Port 22 (SSH) should already be open by default.

### 4. SSH Into Your VM

```bash
ssh -i /path/to/your/private_key ubuntu@YOUR_PUBLIC_IP
```

### 5. Run the Setup Script

```bash
# Download and run
curl -fsSL https://raw.githubusercontent.com/Neopram/Bruce/main/deploy/oracle_setup.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

Or if you have the repo cloned locally:

```bash
git clone https://github.com/Neopram/Bruce.git /opt/bruce
cd /opt/bruce/deploy
chmod +x oracle_setup.sh
./oracle_setup.sh
```

The setup takes approximately 10-15 minutes (mostly downloading the Qwen2.5 model).

### 6. Configure Environment

```bash
nano /opt/bruce/.env
```

Fill in your actual values:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=your_numeric_chat_id
```

To get these:
1. Message [@BotFather](https://t.me/BotFather) on Telegram, create a bot, copy the token
2. Message [@userinfobot](https://t.me/userinfobot) to get your chat ID

Then restart the Telegram service:

```bash
sudo systemctl restart bruce-telegram
```

### 7. Verify Deployment

```bash
# Check all services
sudo systemctl status bruce-backend bruce-telegram bruce-scheduler ollama nginx

# Run the health monitor
/opt/bruce/deploy/monitor.sh

# Check API
curl http://localhost:8000/health

# View logs
journalctl -u bruce-backend -f
```

Access Bruce at: `http://YOUR_PUBLIC_IP`

## Maintenance

### Update Bruce

```bash
cd /opt/bruce/deploy
./update.sh
```

### Monitor Health

```bash
# One-time check
./monitor.sh

# Set up automatic monitoring (every 5 minutes)
crontab -e
# Add this line:
# */5 * * * * /opt/bruce/deploy/monitor.sh --quiet >> /var/log/bruce-monitor.log 2>&1
```

### View Logs

```bash
# Backend
journalctl -u bruce-backend -f

# Telegram bot
journalctl -u bruce-telegram -f

# Scheduler
journalctl -u bruce-scheduler -f

# Ollama
journalctl -u ollama -f
```

### Restart Services

```bash
sudo systemctl restart bruce-backend
sudo systemctl restart bruce-telegram
sudo systemctl restart bruce-scheduler
```

## Resource Usage (Approximate)

| Component       | RAM    | CPU   |
|-----------------|--------|-------|
| Ollama + Qwen2.5 7B | ~6 GB  | Bursts |
| Bruce Backend   | ~300 MB | Low   |
| Telegram Bot    | ~100 MB | Low   |
| Scheduler       | ~100 MB | Low   |
| Nginx           | ~50 MB  | Low   |
| **Total**       | **~7 GB** | Comfortable on 4 cores |

With 24 GB RAM, you have plenty of headroom.

## Troubleshooting

**VM creation fails with "Out of Capacity"**
Oracle Free Tier ARM instances are popular. Retry at different times or use a different availability domain.

**Services fail to start**
Check logs: `journalctl -u bruce-backend -n 100 --no-pager`

**Ollama model download fails**
Retry: `ollama pull qwen2.5:7b`. Ensure you have disk space: `df -h`

**Cannot reach the server from outside**
Verify Oracle Cloud Security List ingress rules include ports 80 and 8000. Also check `sudo iptables -L -n` on the VM.

**High memory usage**
The 7B model uses about 6 GB. If memory is tight, consider `qwen2.5:3b` instead.
