# Sales Intelligence Tracker

AI-powered dashboard for identifying IR team pain points and prioritizing sales outreach. Built collaboratively by a human and Claude AI.

**Last updated: 2026-02-07**

## Recent Updates

### Profile / Territory System (2026-02-07)

**Multi-salesperson support** without auth — each salesperson maintains their own territory (set of companies) with independent outreach tracking, while sharing the underlying news/signal data.

- `profiles` table + `profile_companies` junction table in schema
- `profile_id` column on `outreach_actions` for profile-scoped outreach
- Dropdown profile selector in header, stored in localStorage
- Auto-creates "Default" profile on first load if none exist
- Same company can exist in multiple profiles (shared via junction table)
- Pipeline/financials scoped to selected profile's companies
- All `profile_id` params are optional — backward compatible
- **Details**: See "Profile / Territory System" section below

### IR Relevance Filtering & Talking Point Consolidation (2026-02-07)

**Classification Prompt Refinement**:
- Restructured `SIGNAL_CLASSIFICATION_PROMPT` and `BATCH_CLASSIFICATION_PROMPT` with XML tags (`<role>`, `<ir_relevance_criteria>`, `<first_check>`, `<examples>`, `<scoring_guide>`)
- Added explicit IR relevance gate defining what creates IR team work vs. what doesn't
- Added few-shot examples: analyst downgrade (high pain), EEOC probe (neutral), CFO departure (moderate)
- Added chain-of-thought instruction: "Would the IR team need to brief investors about this?"

**Code-Level Keyword Override**:
- `config.NON_IR_KEYWORDS` — list of keywords (discrimination, EEOC, DEI, harassment, etc.) that force headlines to neutral
- `etl._is_non_ir_headline()` — deterministic filter applied after model classification in both single and batch paths
- Needed because Claude Haiku ignores prompt-level exclusions when signal words like "federal probe" or "EEOC" are strong
- **Details**: See "IR Relevance Filtering" section below

**One Talking Point Per Company**:
- Removed `talking_point` from `BATCH_CLASSIFICATION_PROMPT` output (fewer output tokens per batch)
- `generate_talking_point()` now takes a list of signals (top 3 by pain) and produces one company-level opener
- Talking point attached to the highest-pain signal for each company
- `TALKING_POINTS_PROMPT` rewritten with XML structure to accept `{signals_block}` instead of single signal
- **Details**: See "Talking Point Generation" section below

### MVP Complete (2026-02-03)

**IR Cycle Feature**:
- Added IR Cycle column calculating stage from earnings dates
- Stages: Open Window (high opportunity), Mid-Quarter (medium), Earnings Week (low), Quiet Period (low)
- Filter by IR Cycle stage
- Info tooltips explaining each stage with criteria

**UI Overhaul**:
- Blue/white color scheme throughout
- Renamed "Signals" to "Pain Points" everywhere
- Removed all emojis for cleaner look
- Improved filter labels for clarity
- Added stock movement filter (positive/negative movers)
- Fixed action button overflow on small screens

**Pipeline Improvements**:
- "Update Everything" button combines pipeline + financials refresh
- Auto-fetch financials when adding new companies
- Fixed earnings date fetching from yfinance

### ETL Performance Optimization (2026-02-03)
- Implemented batch article classification (8 articles per API call)
- Added parallel company processing (5 concurrent workers)
- Added batch database inserts for signals
- **Result**: 7x faster pipeline execution, 95% reduction in Claude API costs
- **Details**: See "ETL Pipeline Optimization" section below

### Frontend Data Fixes (2026-02-03)
- Fixed financials not updating after refresh (refetchQueries vs invalidateQueries)
- Made ticker field mandatory for all companies (required for stock data)
- **Details**: See "Frontend Improvements" section below

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
│   │   ├── components/   # CompanyTable, Filters, Sidebar, ProfileSelector, etc.
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
3. **Multi-user via profiles**: No auth, profile selector in header, localStorage persistence
4. **Daily batch**: ETL runs on-demand, not real-time
5. **Claude Haiku only**: Don't upgrade to Sonnet unless necessary

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/profiles` | GET | List all profiles |
| `/api/profiles` | POST | Create profile |
| `/api/profiles/{id}` | DELETE | Delete profile (cascades junction + outreach) |
| `/api/companies` | GET | List companies (`profile_id` optional) |
| `/api/companies` | POST | Add company (`profile_id` in body for junction link) |
| `/api/companies/summary` | GET | Pain summary (`profile_id` optional) |
| `/api/init` | GET | Combined initial load (`profile_id` optional) |
| `/api/financials` | GET | Stock data (`profile_id` optional) |
| `/api/signals` | GET | Signals with filters |
| `/api/outreach` | POST | Log outreach action (`profile_id` in body) |
| `/api/outreach/hidden` | GET | Hidden company IDs (`profile_id` optional) |
| `/api/pipeline/run` | POST | Run ETL pipeline (`profile_id` optional) |
| `/api/pipeline/financials` | POST | Refresh stock data (`profile_id` optional) |
| `/api/pipeline/update-all` | POST | Run pipeline + refresh financials (`profile_id` optional) |

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

## ETL Pipeline Optimization

The pipeline was optimized for performance using batch processing and parallelization.

### Performance Strategy

1. **Batch Classification**: Group multiple articles into a single Claude API call
2. **Parallel Processing**: Process multiple companies concurrently
3. **Batch Database Operations**: Insert multiple signals in one query

### Key Changes

**config.py - Batch Processing Constants**:
- `BATCH_CLASSIFICATION_SIZE = 8` - Articles per Claude API call
- `COMPANY_PARALLELISM = 5` - Concurrent company processing
- `BATCH_CLASSIFICATION_PROMPT` - Classification-only prompt (talking points generated separately)
- `NON_IR_KEYWORDS` - Keyword list for deterministic non-IR headline filtering

**etl.py - Core Pipeline Functions**:
- `batch_classify_articles()` - Classifies up to 8 articles in one Claude API call
  - Returns list with article indices for mapping (no talking points)
- `_parse_batch_response()` - Parses batch classification JSON response
- `_is_non_ir_headline()` - Keyword-based override for non-IR headlines
- `generate_talking_point()` - One call per company using top 3 signals
- `process_company()` - Batch classify → keyword override → one talking point per company
- `run_pipeline()` - Uses `ThreadPoolExecutor` with 5 workers for parallel company processing

**db.py - Batch Database Operations**:
- `add_signals_batch()` - Inserts multiple signals in a single database call
  - Falls back to individual inserts if batch fails

### Performance Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Time for 3 companies | ~37+ seconds | ~5 seconds | 7x faster |
| API calls per article | 1-2 calls | ~0.125 calls | 8-16x reduction |
| Processing model | Sequential | Parallel | Scales with cores |

### Fallback Strategy

If batch processing fails:
1. Batch classification falls back to individual `classify_article()` calls
2. Talking point still generated once per company from available signals
3. Batch signal insert falls back to individual `add_signal()` calls

This ensures robustness while maintaining performance gains in the happy path.

## IR Relevance Filtering

Classification prompts include an IR relevance gate, but Claude Haiku ignores prompt-level exclusions when headlines contain strong signal words (e.g., "federal probe", "EEOC", "government investigation"). A code-level keyword override provides a deterministic fallback.

### How It Works

1. **Prompt-level**: `<ir_relevance_criteria>` and `<first_check>` sections in both classification prompts define what's IR-relevant vs. internal matters
2. **Code-level**: After model classification, `_is_non_ir_headline()` checks headlines against `config.NON_IR_KEYWORDS`
3. **Override**: If a keyword matches and `signal_type != "neutral"`, forces `signal_type = "neutral"` and `ir_pain_score = 0.0`

### Adding New Keywords

To exclude a new category of non-IR news, add keywords to `NON_IR_KEYWORDS` in `config.py`:

```python
NON_IR_KEYWORDS = [
    "discrimination", "eeoc", "dei policy", "dei policies", "dei program",
    "workplace bias", "bias against", "labor dispute", "employee lawsuit",
    # ... add new keywords here
]
```

### Why Both Prompt + Code?

- Prompts handle the general case well (most neutral news is classified correctly)
- Code override handles edge cases where the model's bias toward "governance_issue" or "esg_negative" overrides instructions
- Lesson: For hard classification boundaries with smaller models, use deterministic filters

## Talking Point Generation

One talking point per company, generated after all article classification is complete.

### Pipeline Flow

1. Batch classify all articles for a company (no talking points in batch output)
2. Collect qualifying signals (`ir_pain_score >= 0.5`)
3. Call `generate_talking_point()` once per company with top 3 signals
4. Attach the talking point to the highest-pain signal in the database

### Prompt Design

`TALKING_POINTS_PROMPT` receives a `{signals_block}` with the top 3 signals formatted as:
```
- [analyst_negative] (pain 0.85) Summary of the signal...
- [stock_pressure] (pain 0.65) Summary of the signal...
```

The model picks the most compelling pain point and writes a single outreach opener.

## Profile / Territory System

Lightweight multi-salesperson support. Each profile is a territory — a set of companies with independent outreach tracking. No authentication; profile selection stored in localStorage.

### Data Model

- **Global (shared)**: `companies`, `articles`, `signals`, `company_financials` — all profiles see the same news/signals for a given company
- **Profile-scoped**: `outreach_actions.profile_id` — each profile tracks contacted/snoozed independently
- **Junction**: `profile_companies` — maps profiles to their companies (many-to-many)

### Key Behaviors

- **Shared companies**: When Profile B adds a ticker that already exists, the existing company record is reused and a new junction link is created (no duplicate company)
- **Orphan cleanup**: When the last profile unlinks a company, the company + cascaded data (articles, signals, financials) is deleted
- **Pipeline scoping**: `run_pipeline(profile_id=...)` only processes that profile's companies; `process_company()` is profile-agnostic (URL dedup prevents duplicate articles/signals)
- **Backward compat**: All `profile_id` params are optional — the app works without profiles as a fallback

### Frontend Flow

1. On load, fetch profiles (`GET /api/profiles`)
2. If no profiles exist, auto-create "Default"
3. If saved `profileId` in localStorage is stale (deleted), auto-select first profile
4. All queries include `profile_id` — init data, mutations, pipeline runs
5. `ProfileSelector` component in header: dropdown + inline create + delete

### Key Functions

**db.py — Profile CRUD**:
- `create_profile(name)` — insert, raise ValueError on duplicate
- `get_profiles()` — all profiles, ordered by name
- `delete_profile(profile_id)` — CASCADE removes junction + outreach

**db.py — Junction helpers**:
- `link_company_to_profile(profile_id, company_id)` — insert, ignore duplicates
- `unlink_company_from_profile(profile_id, company_id)` — delete junction row
- `get_profile_company_ids(profile_id)` — list of company_id strings
- `is_company_orphaned(company_id)` — check if any junction links remain

**db.py — Modified functions** (all accept optional `profile_id`):
- `add_company()` — reuses existing company if ticker matches + profile_id given
- `get_companies()` — filters by junction when profile_id provided
- `delete_company()` — unlinks from profile; only deletes company if orphaned
- `get_company_pain_summary()` — filters signals to profile's companies
- `get_company_financials()` — filters by profile's company IDs
- `get_financials_needing_refresh()` — scopes to profile's companies
- `add_outreach_action()` — includes profile_id in insert
- `get_companies_to_hide()`, `delete_outreach_action()`, `get_outreach_details()` — filter by profile_id

### Migration SQL

For existing deployments, run after creating tables:
```sql
INSERT INTO profiles (name) VALUES ('Default') ON CONFLICT (name) DO NOTHING;
INSERT INTO profile_companies (profile_id, company_id)
SELECT p.id, c.id FROM profiles p, companies c WHERE p.name = 'Default';
UPDATE outreach_actions SET profile_id = (SELECT id FROM profiles WHERE name = 'Default')
WHERE profile_id IS NULL;
```

## Performance Goals

Current pain points addressed:
- [x] Pipeline execution speed - Optimized with batching and parallelization

Remaining improvements:
- [ ] Initial load time (data fetching)
- [ ] Table rendering with many signals
- [ ] API response times

## Frontend Improvements

Recent fixes to improve data consistency and user experience.

### Recent Fixes

**App.tsx - Financials Refresh Fix**:
- Changed `invalidateQueries` to `refetchQueries` for financial data refresh
- Ensures data is fully loaded before showing success message
- Prevents stale data being displayed after refresh operation

**Sidebar.tsx - Mandatory Ticker Field**:
- Ticker field is now required (was optional)
- Added helper text: "Required for stock data"
- Rationale: yfinance requires ticker symbols to fetch financial data
- Prevents adding companies without financial data capability

### Implementation Details

```typescript
// Before: Data might not be loaded when success shows
await queryClientInstance.invalidateQueries({ queryKey: ['financials'] });

// After: Wait for data to fully load
await queryClientInstance.refetchQueries({ queryKey: ['financials'] });
```

## UI/UX Goals

Recent improvements:
- [x] Better loading states for financial refresh
- [x] Blue/white color scheme
- [x] IR Cycle column with tooltips
- [x] Improved filter labels and options
- [x] Renamed "Signals" to "Pain Points" for clarity
- [x] Action button layout fixes

Areas for improvement:
- [ ] Mobile responsiveness (ProfileSelector overflows on narrow screens)
- [ ] Keyboard navigation
- [ ] Dark mode support

## Database Schema

See `schema.sql` for full schema. Key tables:
- `companies` - Watchlist (global, shared across profiles)
- `articles` - Fetched news (global)
- `signals` - AI-classified signals with pain scores (global)
- `company_financials` - Stock data from yfinance (global)
- `profiles` - Salesperson territories
- `profile_companies` - Junction: which companies belong to which profiles
- `outreach_actions` - Contact/snooze tracking (profile-scoped via `profile_id`)

## Testing

- Manual testing for MVP
- Test with browser dev tools Network tab
- Backend: `curl http://localhost:8000/api/health`
- Check Supabase dashboard for data issues

## Cost Monitoring

Target: **Under $5/month** total

**Current Costs**:
- Claude API: ~$0.25-0.50/month for 1000 companies (after batch optimization)
  - Batch processing reduces API calls by 8-16x
  - ~0.125 API calls per article vs 1-2 calls before
- Render: Free tier (with spin-down) or $7/month starter
- Supabase: Free tier

**Cost Optimization**:
- Batch classification saves ~87.5% on Claude API costs
- With 1000 companies averaging 5 new articles/week = 5000 articles/week
- Before: 5000-10000 API calls/week = ~$10-20/month
- After: ~625 API calls/week = ~$0.25-0.50/month
- Total savings: ~95%+ on AI costs
