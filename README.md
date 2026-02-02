# Sales Intelligence Tracker

A lightweight tool for tracking IR (Investor Relations) pain signals at public companies to support sales outreach. Monitors news for events that indicate when IR teams might be receptive to vendor outreach.

## What It Does

1. **Monitors news** for a watchlist of public companies via Google News RSS
2. **Classifies signals** using Claude AI to identify IR team pain points
3. **Scores pain level** to prioritize outreach opportunities
4. **Surfaces actionable signals** in a simple Streamlit dashboard

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

- **News Source**: Google News RSS (free, no API limits)
- **AI Classification**: Claude 3.5 Haiku (~$2/month for 1000 companies)
- **Database**: Supabase (free tier)
- **UI**: Streamlit (free hosting)

## Project Structure

```
sales-intelligence-tracker/
├── app.py          # Streamlit dashboard
├── etl.py          # News fetching + AI classification
├── db.py           # Database operations
├── config.py       # Settings, prompts, constants
├── requirements.txt
└── .streamlit/
    └── secrets.toml  # API keys (not committed)
```

## Setup

1. **Clone the repo**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets** in `.streamlit/secrets.toml`:
   ```toml
   ANTHROPIC_API_KEY = "sk-..."
   SUPABASE_URL = "https://xxx.supabase.co"
   SUPABASE_KEY = "eyJ..."
   ```

4. **Create database tables** in Supabase:
   - `companies` (id, name, ticker, aliases, active, created_at)
   - `articles` (id, company_id, title, url, source, published_at, fetched_at)
   - `signals` (id, article_id, company_id, summary, signal_type, relevance_score, sales_relevance, created_at)

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Usage

1. Add companies to your watchlist (sidebar)
2. Click "Run Pipeline" to fetch and classify news
3. View "IR Teams in Pain" for top outreach opportunities
4. Filter and export signals to CSV

## Cost

~$2/month for 1000 companies at daily refresh rate.

## License

MIT
