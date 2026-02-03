# Sales Intelligence Tracker

A tool for tracking IR (Investor Relations) pain signals at public companies to support sales outreach. Monitors news for events that indicate when IR teams might be receptive to vendor outreach.

## What It Does

1. **Monitors news** for a watchlist of public companies via Google News RSS
2. **Classifies signals** using Claude AI to identify IR team pain points
3. **Scores pain level** to prioritize outreach opportunities
4. **Tracks financials** using yfinance for stock performance context
5. **Manages outreach** with contact/snooze workflow

## IR Pain Signals

The tool identifies moments when IR teams are likely under pressure:

| Signal Type | Examples | Why They'd Take a Call |
|-------------|----------|------------------------|
| Activist Risk | 13-D filings, ownership shake-ups | "We can help you monitor/respond" |
| Analyst Negative | Downgrades, coverage drops | "We can help with messaging" |
| Earnings Miss | Missed expectations, guidance cuts | "We can help with narrative" |
| Leadership Change | New CEO, CFO, IRO | New leader = vendor evaluation |
| Governance Issue | Proxy fights, ISS against | "We can help with narrative" |
| ESG Negative | Rating downgrades, controversies | "We can help with ESG story" |
| Stock Pressure | Sharp drops, short interest | "We can help stabilize base" |
| Capital Stress | Failed offerings, debt downgrades | "We can help with positioning" |
| Peer Pressure | Competitor wins, market share loss | "We can help differentiate" |

## Tech Stack

- **Frontend**: React + Vite + TanStack Table + Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI Classification**: Claude 3.5 Haiku
- **Database**: Supabase (PostgreSQL)
- **Financial Data**: yfinance
- **Hosting**: Render (backend + frontend)

## Project Structure

```
sales-intelligence-tracker/
├── backend/
│   ├── main.py           # FastAPI routes
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx       # Main app
│   │   ├── components/   # Table, filters, sidebar
│   │   ├── api/          # API client
│   │   └── types/        # TypeScript types
│   └── package.json
├── db.py                 # Database operations
├── etl.py                # News fetching + AI classification
├── config.py             # Settings, prompts
├── schema.sql            # Database schema
└── app.py                # Legacy Streamlit app
```

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `.streamlit/secrets.toml` (backend reads this for local dev):
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

## Database Setup

Run `schema.sql` in Supabase SQL Editor to create tables:
- `companies` - Watchlist
- `articles` - Fetched news
- `signals` - AI-classified signals
- `company_financials` - Stock data
- `outreach_actions` - Contact tracking

## Deployment (Render)

**Backend (Web Service)**:
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment: `SUPABASE_URL`, `SUPABASE_KEY`, `ANTHROPIC_API_KEY`

**Frontend (Static Site)**:
- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Environment: `VITE_API_URL` (your backend URL)

## Usage

1. Add companies to your watchlist (sidebar)
2. Click "Run Pipeline" to fetch and classify news
3. View companies sorted by pain score
4. Expand rows to see signals and talking points
5. Mark as contacted or snooze to manage workflow

## Performance

Fast and efficient:
- Batch article classification (8 articles per API call)
- Parallel company processing (5 concurrent workers)
- Typical run: Process 3 companies in ~5 seconds

## Cost

~$5/month total:
- Claude API: ~$0.25-0.50/month for 1000 companies (batch optimized)
- Render: Free tier or $7/month for always-on
- Supabase: Free tier

## License

MIT
