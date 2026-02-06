# PythonAnywhere Setup Guide

## Step 1: Create Account
1. Go to https://www.pythonanywhere.com
2. Click "Create free account"
3. Choose "Free" tier
4. Verify email

## Step 2: Upload Your Code

### Option A: Git Clone (Recommended)
```bash
# In PythonAnywhere console
git clone https://github.com/s6ft256/tradebot-V1.0.git
cd tradebot-V1.0
```

### Option B: Manual Upload
1. Download your code as ZIP
2. In PythonAnywhere: Files → Upload a file
3. Upload and extract

## Step 3: Install Dependencies

In PythonAnywhere console:
```bash
cd tradebot-V1.0
pip install fastapi uvicorn pydantic httpx ccxt sqlalchemy asyncpg cryptography python-dotenv orjson numpy
```

## Step 4: Set Environment Variables

1. Go to: Web → Web tab
2. Click "Add a new web app"
3. Choose "Manual configuration" → Python 3.11
4. In "WSGI configuration file", set:
```python
import os
os.environ['PAPER_TRADING'] = 'true'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['MAX_RISK_PER_TRADE'] = '1.0'
os.environ['MAX_DAILY_LOSS'] = '3.0'
os.environ['MAX_DRAWDOWN'] = '10.0'

# Add your Binance keys if you have testnet keys
# os.environ['BINANCE_API_KEY'] = 'your_key'
# os.environ['BINANCE_API_SECRET'] = 'your_secret'
# os.environ['BINANCE_TESTNET'] = 'true'
```

## Step 5: Create Always-On Task

1. Go to: Tasks → Always-on tasks tab
2. Click "Add an always-on task"
3. Set:
   - Command: `cd tradebot-V1.0/src && python main.py`
   - Description: "Trading Bot"
   - Schedule: "Every 1 minute"
4. Click "Create"

## Step 6: Test the Bot

1. Go to: Tasks → Always-on tasks
2. Click the "Run" button next to your task
3. Check logs: Click the task name → "Logs"

## Step 7: Monitor

1. Check logs regularly in the "Logs" section
2. View trade data in Files → tradebot-V1.0/data/
3. Set up email alerts (optional)

## Important Notes:

### Free Tier Limitations:
- **CPU time**: 100 seconds per day
- **RAM**: 512MB
- **Storage**: 512MB
- **No external connections** to Binance (paper trading only)

### For Paper Trading:
The free tier is perfect for testing your strategy without real money.

### For Live Trading:
You'll need to upgrade to a paid plan ($5-10/month) for:
- More CPU time
- External API connections
- Better reliability

## Troubleshooting:

### If task fails:
1. Check logs for errors
2. Make sure all dependencies are installed
3. Verify environment variables

### If bot stops:
1. Check if you hit CPU limit
2. Upgrade to paid plan if needed
3. Consider longer intervals (every 5 minutes)

## Next Steps:

1. **Paper trade for 1-2 weeks** on free tier
2. **Monitor performance** and P&L
3. **If profitable**, upgrade to paid plan
4. **Add real API keys** for live trading

## Security Reminder:
- Never share your API keys
- Use testnet keys for testing
- Start with small amounts if going live
