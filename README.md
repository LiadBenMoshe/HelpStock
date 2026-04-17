# HelpStock

HelpStock is a stock analysis web application built with FastAPI on the backend and pure HTML, CSS, and vanilla JavaScript on the frontend.

It provides a dashboard for:
- support and resistance levels
- insider activity
- quarterly revenue growth
- P/E analysis
- Google Trends
- analyst price targets
- VIX status
- news summaries
- partnerships and contracts
- product relevance
- company overview

The UI supports both English and Hebrew.

## Tech Stack

- Backend: FastAPI
- Frontend: HTML, CSS, vanilla JavaScript
- Data sources: Yahoo Finance, Finnhub, NewsAPI, Google Trends
- Caching: in-memory TTL cache

## Project Structure

```text
app/
  core/
  models/
  routers/
  services/
  static/
  main.py
requirements.txt
.env.example
```

## Local Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create your environment file:

```powershell
Copy-Item .env.example .env
```

4. Fill in your API keys in `.env`.

## Environment Variables

Supported variables:

- `APP_NAME`
- `ENVIRONMENT`
- `LOG_LEVEL`
- `CACHE_TTL_SECONDS`
- `ALLOWED_ORIGINS`
- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `NEWSAPI_API_KEY`

## Run Locally

Start the app with:

```powershell
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## API

### Health check

```text
GET /health
```

### Analyze a stock

```text
GET /analyze/{symbol}
GET /analyze/{symbol}?lang=en
GET /analyze/{symbol}?lang=he
```

Example:

```text
GET /analyze/AAPL?lang=he
```

## Deploy on Render

Create a new `Web Service` on Render and use:

- Build Command:

```text
pip install -r requirements.txt
```

- Start Command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these environment variables in Render:

- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `NEWSAPI_API_KEY`
- optional app settings like `APP_NAME`, `LOG_LEVEL`, and `CACHE_TTL_SECONDS`

## Notes

- Free Render services may spin down after inactivity.
- Some external APIs can be rate-limited or temporarily unavailable.
- Local filesystem storage is not persistent in free cloud deployments.

## Author

All Rights Reserved to Liad Ben Moshe
