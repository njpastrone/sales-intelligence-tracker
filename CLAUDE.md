# Sales Intelligence Tracker

AI-powered dashboard for identifying IR team pain signals and prioritizing sales outreach.

## Architecture

```
Frontend (React)         Backend (FastAPI)        Database (Supabase)
┌──────────────┐        ┌──────────────┐         ┌──────────────┐
│ Vite + React │───────▶│ Python API   │────────▶│ PostgreSQL   │
│ TanStack     │  JSON  │ ETL Pipeline │         │              │
│ Tailwind CSS │        │ Claude Haiku │         │              │
└──────────────┘        └──────────────┘         └──────────────┘
     Render                  Render                 Supabase
   Static Site            Web Service               Free Tier
```

## Project Structure

```
sales-intelligence-tracker/
├── backend/
│   ├── main.py           # FastAPI routes
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/   # CompanyTable, Filters, Sidebar, etc.
│   │   ├── api/client.ts
│   │   └── types/index.ts
│   ├── package.json
│   └── vite.config.ts
├── db.py                 # Database operations (shared)
├── etl.py                # Data pipeline (shared)
├── config.py             # Constants, prompts (shared)
├── schema.sql            # Database schema
├── app.py                # Legacy Streamlit app
└── docs/archive/         # Old planning documents
```

## File Ownership

| File | Responsibility |
|------|---------------|
| `backend/main.py` | FastAPI routes, request handling |
| `frontend/src/App.tsx` | Main React app, state management |
| `frontend/src/components/` | UI components (table, filters, sidebar) |
| `frontend/src/api/client.ts` | API client functions |
| `db.py` | Database operations - CRUD, queries |
| `etl.py` | Data pipeline - fetch, classify, transform |
| `config.py` | Constants, settings, AI prompts |

## Key Constraints

1. **Cost-conscious**: ~$5/month total (Render free/starter + Supabase free)
2. **1000 company scale**: Designed for hundreds of companies, not millions
3. **Single user**: No auth, no multi-tenancy
4. **Daily batch**: ETL runs on-demand, not real-time
5. **Claude Haiku only**: Don't upgrade to Sonnet unless necessary

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/companies` | GET | List companies |
| `/api/companies` | POST | Add company |
| `/api/companies/summary` | GET | Pain summary for dashboard |
| `/api/financials` | GET | Stock data |
| `/api/signals` | GET | Signals with filters |
| `/api/outreach` | POST | Log outreach action |
| `/api/outreach/hidden` | GET | Hidden company IDs |
| `/api/pipeline/run` | POST | Run ETL pipeline |
| `/api/pipeline/financials` | POST | Refresh stock data |

## Development

### Local Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Backend auto-loads secrets from `.streamlit/secrets.toml` for local dev.

### Environment Variables

**Backend** (Render or `.env`):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ANTHROPIC_API_KEY`

**Frontend** (Render or `.env`):
- `VITE_API_URL` - Backend URL (no trailing slash)

## Deployment (Render)

**Backend (Web Service)**:
- Root: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Frontend (Static Site)**:
- Root: `frontend`
- Build: `npm install && npm run build`
- Publish: `dist`

## Performance Goals

Current pain points to address:
- [ ] Initial load time (data fetching)
- [ ] Table rendering with many signals
- [ ] Pipeline execution speed
- [ ] API response times

## UI/UX Goals

Areas for improvement:
- [ ] More polished visual design
- [ ] Better loading states
- [ ] Mobile responsiveness
- [ ] Keyboard navigation
- [ ] Dark mode support

## Database Schema

See `schema.sql` for full schema. Key tables:
- `companies` - Watchlist
- `articles` - Fetched news
- `signals` - AI-classified signals with pain scores
- `company_financials` - Stock data from yfinance
- `outreach_actions` - Contact/snooze tracking

## Testing

- Manual testing for MVP
- Test with browser dev tools Network tab
- Backend: `curl http://localhost:8000/api/health`
- Check Supabase dashboard for data issues

## Cost Monitoring

Target: **Under $5/month** total
- Claude API: ~$2-3/month for 1000 companies
- Render: Free tier (with spin-down) or $7/month starter
- Supabase: Free tier
