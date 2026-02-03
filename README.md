# Sales Intelligence Tracker

AI-powered dashboard for identifying IR (Investor Relations) pain points at public companies and prioritizing sales outreach. Built collaboratively by a human and Claude AI.

## What It Does

1. **Monitors news** for a watchlist of public companies via Google News RSS
2. **Classifies pain points** using Claude AI to identify IR team challenges
3. **Scores pain level** to prioritize outreach opportunities
4. **Tracks financials** using yfinance for stock performance and earnings dates
5. **Calculates IR Cycle** to identify optimal outreach timing
6. **Manages outreach** with contact/snooze workflow

## IR Cycle Timing

The tool calculates where each company is in their IR cycle to optimize outreach timing:

| Stage | Timing | Outreach Opportunity |
|-------|--------|---------------------|
| **Open Window** | 8-45 days post-earnings | High - IR team actively engaging investors |
| **Mid-Quarter** | >45 days post-earnings | Medium - Between cycles, strategic planning |
| **Earnings Week** | 0-7 days post-earnings | Low - Busy with calls and follow-up |
| **Quiet Period** | 0-14 days pre-earnings | Low - Limited external communications |

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

1. Add companies to your watchlist (sidebar with ticker symbol)
2. Click "Update Everything" to fetch news, classify pain points, and update financials
3. View companies sorted by pain score
4. Filter by IR Pain Point type, Stock movement, or IR Cycle stage
5. Expand rows to see pain points, talking points, and financial details
6. Mark as contacted or snooze to manage workflow

## Filters

- **Pain points from**: Time window (7, 14, 30 days)
- **IR Pain Point**: Filter by specific pain point type
- **Stock (7D)**: Positive or negative movers
- **IR Cycle**: Filter by cycle stage (Open Window, Mid-Quarter, etc.)
- **Include hidden**: Show contacted/snoozed companies

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
