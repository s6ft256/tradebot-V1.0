# 24/7 Deployment Guide

## Overview
To run your trading bot 24/7, you need a server that's always online. Here are your options:

## Option 1: Cloud VPS (Recommended)

Providers: DigitalOcean, AWS, Linode, Vultr (~$5-20/month)

### Quick Setup:

```bash
# 1. Create a VPS (Ubuntu 22.04 recommended)
# 2. SSH into your server
ssh root@your-server-ip

# 3. Install dependencies
apt update && apt install -y git python3 python3-pip docker docker-compose

# 4. Clone your repo
git clone https://github.com/s6ft256/tradebot-V1.0.git
cd tradebot-V1.0

# 5. Run with Docker (EASIEST)
docker-compose -f docker-compose.prod.yml up -d

# 6. Check logs
docker logs -f tradebot
```

### Using Systemd (Alternative):

```bash
# 1. Create user
useradd -m tradebot

# 2. Copy files
mkdir -p /opt/tradebot
cp -r src /opt/tradebot/
chown -R tradebot:tradebot /opt/tradebot

# 3. Install Python deps
pip3 install fastapi uvicorn pydantic httpx ccxt sqlalchemy asyncpg cryptography python-dotenv orjson numpy

# 4. Copy service file
cp deploy/tradebot.service /etc/systemd/system/

# 5. Edit service file with your API keys
nano /etc/systemd/system/tradebot.service

# 6. Start service
systemctl daemon-reload
systemctl enable tradebot
systemctl start tradebot

# 7. Check status
systemctl status tradebot
journalctl -u tradebot -f
```

## Option 2: PythonAnywhere (Free tier available)

1. Sign up at https://www.pythonanywhere.com
2. Upload your code
3. Create a "Always-on task"
4. Set environment variables in the dashboard

## Option 3: Raspberry Pi (Home server)

```bash
# On your Raspberry Pi
sudo apt update
sudo apt install python3-pip git

# Clone and setup
git clone https://github.com/s6ft256/tradebot-V1.0.git
cd tradebot-V1.0
pip3 install -r requirements.txt  # if you have one

# Create a simple runner script
#!/bin/bash
while true; do
    cd ~/tradebot-V1.0/src
    PAPER_TRADING=true python3 main.py
    sleep 10
done
```

## Monitoring Your Bot

### 1. Telegram Bot Alerts
Add this to get notifications:
```python
# In alerts.py, add Telegram webhook
```

### 2. Vercel Dashboard
Deploy the frontend to Vercel to monitor remotely:
```bash
cd frontend
npx vercel --prod
```

### 3. Log Monitoring
```bash
# Watch logs in real-time
docker logs -f tradebot

# Or with systemd
journalctl -u tradebot -f
```

## Security Checklist

- [ ] Use paper trading first
- [ ] API keys have NO withdrawal permissions
- [ ] VPS has firewall enabled (ufw)
- [ ] SSH key authentication only (no passwords)
- [ ] Regular backups of trade data
- [ ] Monitor for unexpected behavior

## Cost Comparison

| Provider | Cost/Month | Reliability | Best For |
|----------|-----------|-------------|----------|
| DigitalOcean | $6 | High | Production |
| AWS Lightsail | $5 | High | Production |
| PythonAnywhere | $0-12 | Medium | Testing |
| Raspberry Pi | $0 | Low | Home use |

## Recommended Setup for Beginners

1. **Start with paper trading** on PythonAnywhere (free)
2. **Test for 1-2 weeks** to verify strategy
3. **Move to VPS** ($5-6/month) when ready for live trading
4. **Deploy dashboard** to Vercel for remote monitoring

## Emergency Stop

If something goes wrong:

```bash
# Docker
docker stop tradebot

# Systemd
systemctl stop tradebot

# Or manually kill
pkill -f "python main.py"
```

## Next Steps

1. Choose your deployment method
2. Set up monitoring (Telegram/Discord alerts)
3. Test with paper trading for 1 week minimum
4. Only then consider live trading
5. Start with small amounts ($100-500)

**Remember: SURVIVABILITY > AGGRESSIVENESS**
