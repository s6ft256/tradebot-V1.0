# paid-trading-bot

Backend + frontend architecture skeleton for a rule-based crypto trading bot with AI-assisted advisory.

## Running the Application

### Backend (FastAPI)
```bash
# Install Python dependencies
pip install -e .

# Run the backend server
uvicorn paid_trading_bot.api.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev
```

The UI will be available at `http://localhost:3000` and will proxy API requests to the backend at `http://localhost:8000`.
