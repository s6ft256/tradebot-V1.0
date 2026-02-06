#!/usr/bin/env python3
"""
PythonAnywhere startup script for trading bot.
This handles the specific environment and limitations.
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, '/home/yourusername/tradebot-V1.0/src')

# Set environment variables for PythonAnywhere
os.environ['PAPER_TRADING'] = 'true'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['MAX_RISK_PER_TRADE'] = '1.0'
os.environ['MAX_DAILY_LOSS'] = '3.0'
os.environ['MAX_DRAWDOWN'] = '10.0'

# Import and run the bot
try:
    from main import AutonomousTradingBot
    
    # Create and run bot with reduced frequency for PythonAnywhere
    bot = AutonomousTradingBot()
    
    # Override loop interval to be PythonAnywhere-friendly
    bot.config = bot.config._replace(loop_interval_seconds=300)  # 5 minutes
    
    print("Starting trading bot in PythonAnywhere mode...")
    print(f"Loop interval: {bot.config.loop_interval_seconds} seconds")
    
    # Run for a limited time (PythonAnywhere has CPU limits)
    import time
    start_time = time.time()
    max_runtime = 300  # 5 minutes max runtime
    
    while time.time() - start_time < max_runtime:
        try:
            bot.run_iteration()
            print(f"Iteration completed. Sleeping for {bot.config.loop_interval_seconds}s...")
            time.sleep(bot.config.loop_interval_seconds)
        except KeyboardInterrupt:
            print("Bot stopped by user")
            break
        except Exception as e:
            print(f"Error in iteration: {e}")
            time.sleep(60)  # Wait 1 minute on error
    
    print("Bot session completed")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install fastapi uvicorn pydantic httpx ccxt sqlalchemy asyncpg cryptography python-dotenv orjson numpy")
    
except Exception as e:
    print(f"Bot startup error: {e}")
    import traceback
    traceback.print_exc()
