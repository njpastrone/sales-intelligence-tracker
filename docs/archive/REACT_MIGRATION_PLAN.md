# React Migration Plan: Sales Intelligence Tracker

## Overview

Migrate from Streamlit to a **React + FastAPI** architecture to achieve a professional, interactive data grid UI with expandable rows, sorting, filtering, and cell-level interactions.

---

## Target UI

A single unified data table where:
- Each row is a company
- Columns: Company, Stock 7d, Market Cap, Next Earnings, Pain Score, Signals, Urgency, Actions
- Click row to expand → see all news items with clickable sources
- Sort by any column
- Filter by urgency, hide contacted/snoozed
- Action buttons inline: Contacted, Snooze, Add Note

---

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | React + TypeScript | Industry standard, huge ecosystem |
| **Data Grid** | TanStack Table | Free, lightweight (15KB), handles expandable rows perfectly |
| **Styling** | Tailwind CSS | Rapid styling, professional look, no custom CSS files |
| **API** | FastAPI | Already using Python, minimal migration from db.py |
| **Database** | Supabase (unchanged) | Keep existing schema and data |
| **Frontend Hosting** | Vercel | Free tier, automatic GitHub deploys |
| **Backend Hosting** | Railway | $5/mo hobby tier, easy Python deployment |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Vercel (Free)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   React Frontend                       │  │
│  │  - TanStack Table (data grid)                         │  │
│  │  - Tailwind CSS (styling)                             │  │
│  │  - React Query (data fetching + caching)              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS / JSON
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Railway ($5/mo)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   FastAPI Backend                      │  │
│  │  - /api/companies (GET, POST)                         │  │
│  │  - /api/signals (GET)                                 │  │
│  │  - /api/outreach (POST)                               │  │
│  │  - /api/pipeline/run (POST)                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Supabase SDK
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supabase (Free Tier)                     │
│  - companies, articles, signals, outreach_actions tables   │
│  - No schema changes required                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
sales-intelligence-tracker/
├── backend/                    # FastAPI (Python)
│   ├── main.py                 # FastAPI app, routes
│   ├── db.py                   # Database operations (reuse existing)
│   ├── etl.py                  # Pipeline logic (reuse existing)
│   ├── config.py               # Settings (reuse existing)
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # For Railway deployment
│
├── frontend/                   # React (TypeScript)
│   ├── src/
│   │   ├── App.tsx             # Main app component
│   │   ├── components/
│   │   │   ├── CompanyTable.tsx    # Main data grid
│   │   │   ├── ExpandedRow.tsx     # Signal details when expanded
│   │   │   ├── ActionButtons.tsx   # Contacted/Snooze/Note
│   │   │   ├── Filters.tsx         # Time window, hide filters
│   │   │   └── Sidebar.tsx         # Company management
│   │   ├── hooks/
│   │   │   └── useCompanies.ts     # React Query data fetching
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   └── api/
│   │       └── client.ts           # API client
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts          # Vite for fast builds
│
├── schema.sql                  # Database schema (unchanged)
└── README.md
```

---

## Phase 1: Backend API (FastAPI)

**Goal**: Convert existing db.py functions to REST endpoints.

### Endpoints

| Method | Endpoint | Description | Maps to |
|--------|----------|-------------|---------|
| GET | `/api/companies` | List all companies | `db.get_companies()` |
| POST | `/api/companies` | Add company | `db.add_company()` |
| GET | `/api/companies/summary` | Company pain summary | `db.get_company_pain_summary()` |
| GET | `/api/financials` | All company financials | `db.get_company_financials()` |
| POST | `/api/outreach` | Log outreach action | `db.add_outreach_action()` |
| GET | `/api/outreach/{company_id}` | Get outreach history | `db.get_outreach_actions()` |
| GET | `/api/outreach/hidden` | Get companies to hide | `db.get_companies_to_hide()` |
| POST | `/api/pipeline/run` | Run news pipeline | `etl.run_pipeline()` |
| POST | `/api/pipeline/financials` | Refresh financials | `etl.refresh_financials()` |
| DELETE | `/api/signals` | Clear all signals | `db.clear_signals_and_articles()` |

### main.py Structure

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import db
import etl
import config

app = FastAPI(title="Sales Intelligence API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---

class CompanyCreate(BaseModel):
    name: str
    ticker: str | None = None

class OutreachAction(BaseModel):
    company_id: str
    action_type: str  # 'contacted', 'snoozed', 'note'
    note: str | None = None

# --- Routes ---

@app.get("/api/companies")
def list_companies():
    return db.get_companies()

@app.post("/api/companies")
def add_company(company: CompanyCreate):
    try:
        return db.add_company(company.name, company.ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/companies/summary")
def get_company_summary(days: int = 7):
    return db.get_company_pain_summary(days=days)

@app.get("/api/financials")
def get_financials():
    return db.get_company_financials()

@app.post("/api/outreach")
def log_outreach(action: OutreachAction):
    return db.add_outreach_action(
        action.company_id,
        action.action_type,
        action.note
    )

@app.get("/api/outreach/{company_id}")
def get_outreach_history(company_id: str, limit: int = 10):
    return db.get_outreach_actions(company_id, limit)

@app.get("/api/outreach/hidden")
def get_hidden_companies(contacted_days: int = 7, snoozed_days: int = 7):
    return list(db.get_companies_to_hide(contacted_days, snoozed_days))

@app.post("/api/pipeline/run")
def run_pipeline():
    return etl.run_pipeline()

@app.post("/api/pipeline/financials")
def refresh_financials():
    return etl.refresh_financials()

@app.delete("/api/signals")
def clear_signals():
    return db.clear_signals_and_articles()
```

### requirements.txt (backend)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
supabase==2.3.0
anthropic==0.18.0
feedparser==6.0.10
yfinance==0.2.36
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deliverable

- FastAPI app with all endpoints
- Tested locally with `uvicorn main:app --reload`
- All existing db.py/etl.py logic preserved

---

## Phase 2: React Frontend Setup

**Goal**: Scaffold React app with TanStack Table and Tailwind.

### Initialize Project

```bash
cd sales-intelligence-tracker
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @tanstack/react-table @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### TypeScript Interfaces (types/index.ts)

```typescript
export interface Company {
  id: string;
  name: string;
  ticker: string | null;
  active: boolean;
  created_at: string;
}

export interface Signal {
  id: string;
  article_id: string;
  company_id: string;
  summary: string;
  signal_type: string;
  relevance_score: number;
  sales_relevance: number;
  talking_point: string | null;
  created_at: string;
  articles: Article;
}

export interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string;
}

export interface CompanySummary {
  company_id: string;
  name: string;
  ticker: string | null;
  max_pain_score: number;
  max_pain_summary: string;
  signal_count: number;
  newest_signal_age_hours: number;
  signals: Signal[];
}

export interface Financials {
  company_id: string;
  price_change_7d: number | null;
  price_change_30d: number | null;
  market_cap: number | null;
  market_cap_tier: string | null;
  next_earnings: string | null;
  last_earnings: string | null;
}

export interface OutreachAction {
  id: string;
  company_id: string;
  action_type: 'contacted' | 'snoozed' | 'note';
  note: string | null;
  created_at: string;
}
```

### API Client (api/client.ts)

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Companies
  getCompanies: () => fetchJSON<Company[]>('/api/companies'),
  addCompany: (name: string, ticker?: string) =>
    fetchJSON<Company>('/api/companies', {
      method: 'POST',
      body: JSON.stringify({ name, ticker }),
    }),
  getCompanySummary: (days: number) =>
    fetchJSON<CompanySummary[]>(`/api/companies/summary?days=${days}`),

  // Financials
  getFinancials: () => fetchJSON<Financials[]>('/api/financials'),

  // Outreach
  logOutreach: (companyId: string, actionType: string, note?: string) =>
    fetchJSON('/api/outreach', {
      method: 'POST',
      body: JSON.stringify({
        company_id: companyId,
        action_type: actionType,
        note,
      }),
    }),
  getOutreachHistory: (companyId: string) =>
    fetchJSON<OutreachAction[]>(`/api/outreach/${companyId}`),
  getHiddenCompanies: (contactedDays: number, snoozedDays: number) =>
    fetchJSON<string[]>(
      `/api/outreach/hidden?contacted_days=${contactedDays}&snoozed_days=${snoozedDays}`
    ),

  // Pipeline
  runPipeline: () => fetchJSON('/api/pipeline/run', { method: 'POST' }),
  refreshFinancials: () =>
    fetchJSON('/api/pipeline/financials', { method: 'POST' }),
  clearSignals: () => fetchJSON('/api/signals', { method: 'DELETE' }),
};
```

### Deliverable

- React + TypeScript app scaffolded
- Tailwind configured
- API client ready
- Type definitions matching backend

---

## Phase 3: Data Table Component

**Goal**: Build the main company table with TanStack Table.

### CompanyTable.tsx

```typescript
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getExpandedRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  ExpandedState,
} from '@tanstack/react-table';
import { useState, useMemo } from 'react';
import { CompanySummary, Financials } from '../types';
import ExpandedRow from './ExpandedRow';
import ActionButtons from './ActionButtons';

interface Props {
  data: CompanySummary[];
  financials: Record<string, Financials>;
  onOutreachAction: (companyId: string, action: string, note?: string) => void;
}

export default function CompanyTable({ data, financials, onOutreachAction }: Props) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'max_pain_score', desc: true },
  ]);
  const [expanded, setExpanded] = useState<ExpandedState>({});

  const columns = useMemo<ColumnDef<CompanySummary>[]>(
    () => [
      {
        id: 'expander',
        header: () => null,
        cell: ({ row }) => (
          <button
            onClick={() => row.toggleExpanded()}
            className="p-1 hover:bg-gray-100 rounded"
          >
            {row.getIsExpanded() ? '▼' : '▶'}
          </button>
        ),
      },
      {
        accessorKey: 'name',
        header: 'Company',
        cell: ({ row }) => {
          const ticker = row.original.ticker;
          return (
            <span className="font-medium">
              {row.original.name}
              {ticker && <span className="text-gray-500 ml-1">({ticker})</span>}
            </span>
          );
        },
      },
      {
        id: 'stock_7d',
        header: 'Stock 7d',
        cell: ({ row }) => {
          const fin = financials[row.original.company_id];
          const change = fin?.price_change_7d;
          if (change == null) return <span className="text-gray-400">—</span>;
          const color = change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : '';
          const sign = change > 0 ? '+' : '';
          return <span className={color}>{sign}{(change * 100).toFixed(1)}%</span>;
        },
      },
      {
        id: 'market_cap',
        header: 'Market Cap',
        cell: ({ row }) => {
          const tier = financials[row.original.company_id]?.market_cap_tier;
          const labels: Record<string, string> = {
            small: 'Small',
            mid: 'Mid',
            large: 'Large',
          };
          return <span>{labels[tier || ''] || '—'}</span>;
        },
      },
      {
        id: 'next_earnings',
        header: 'Earnings',
        cell: ({ row }) => {
          const date = financials[row.original.company_id]?.next_earnings;
          return <span>{date || '—'}</span>;
        },
      },
      {
        accessorKey: 'max_pain_score',
        header: 'Pain Score',
        cell: ({ getValue }) => {
          const score = getValue() as number;
          const pct = Math.round(score * 100);
          const bg = score >= 0.7 ? 'bg-red-100' : score >= 0.5 ? 'bg-yellow-100' : 'bg-gray-100';
          return (
            <span className={`px-2 py-1 rounded ${bg}`}>
              {pct}%
            </span>
          );
        },
      },
      {
        accessorKey: 'signal_count',
        header: 'Signals',
      },
      {
        id: 'urgency',
        header: 'Urgency',
        cell: ({ row }) => {
          const urgency = computeUrgency(
            row.original.max_pain_score,
            row.original.newest_signal_age_hours
          );
          return (
            <span className={`px-2 py-1 rounded ${urgency.bgColor}`}>
              {urgency.icon} {urgency.label}
            </span>
          );
        },
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <ActionButtons
            companyId={row.original.company_id}
            onAction={onOutreachAction}
          />
        ),
      },
    ],
    [financials, onOutreachAction]
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting, expanded },
    onSortingChange: setSorting,
    onExpandedChange: setExpanded,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowCanExpand: () => true,
  });

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getIsSorted() === 'asc' && ' ↑'}
                  {header.column.getIsSorted() === 'desc' && ' ↓'}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row) => (
            <>
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3 whitespace-nowrap text-sm">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
              {row.getIsExpanded() && (
                <tr key={`${row.id}-expanded`}>
                  <td colSpan={columns.length} className="px-4 py-4 bg-gray-50">
                    <ExpandedRow signals={row.original.signals} />
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function computeUrgency(painScore: number, ageHours: number) {
  if (painScore >= 0.7 && ageHours <= 48) {
    return { icon: '🔥', label: 'Call today', bgColor: 'bg-red-100 text-red-800' };
  } else if (painScore >= 0.5 || ageHours <= 168) {
    return { icon: '🟡', label: 'This week', bgColor: 'bg-yellow-100 text-yellow-800' };
  }
  return { icon: '⚪', label: 'Monitor', bgColor: 'bg-gray-100 text-gray-600' };
}
```

### ExpandedRow.tsx

```typescript
import { Signal } from '../types';

const SIGNAL_ICONS: Record<string, string> = {
  activist_risk: '🦈',
  analyst_negative: '📉',
  earnings_miss: '❌',
  leadership_change: '🔄',
  governance_issue: '⚔️',
  esg_negative: '🌍',
  stock_pressure: '📊',
  capital_stress: '💸',
  peer_pressure: '🏃',
  neutral: '📰',
};

interface Props {
  signals: Signal[];
}

export default function ExpandedRow({ signals }: Props) {
  return (
    <div className="space-y-3">
      <h4 className="font-medium text-gray-700">News & Signals</h4>
      {signals.map((signal) => (
        <div key={signal.id} className="flex items-start gap-3 p-3 bg-white rounded border">
          <span className="text-xl">{SIGNAL_ICONS[signal.signal_type] || '📰'}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-600 uppercase">
                {signal.signal_type.replace('_', ' ')}
              </span>
              <span className="text-sm text-gray-400">
                {Math.round(signal.sales_relevance * 100)}% pain
              </span>
            </div>
            <p className="text-sm text-gray-800 mt-1">{signal.summary}</p>
            {signal.talking_point && (
              <p className="text-sm text-blue-600 mt-2 italic">
                💬 {signal.talking_point}
              </p>
            )}
            <a
              href={signal.articles.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-500 hover:underline mt-2 inline-block"
            >
              {signal.articles.source} • {signal.articles.published_at?.slice(0, 10)}
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### ActionButtons.tsx

```typescript
import { useState } from 'react';

interface Props {
  companyId: string;
  onAction: (companyId: string, action: string, note?: string) => void;
}

export default function ActionButtons({ companyId, onAction }: Props) {
  const [showNote, setShowNote] = useState(false);
  const [note, setNote] = useState('');

  const handleNote = () => {
    if (note.trim()) {
      onAction(companyId, 'note', note);
      setNote('');
      setShowNote(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onAction(companyId, 'contacted')}
        className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
        title="Mark contacted"
      >
        ✅
      </button>
      <button
        onClick={() => onAction(companyId, 'snoozed')}
        className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
        title="Snooze"
      >
        😴
      </button>
      <button
        onClick={() => setShowNote(!showNote)}
        className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        title="Add note"
      >
        📝
      </button>
      {showNote && (
        <div className="flex gap-1">
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="px-2 py-1 text-xs border rounded w-32"
            placeholder="Add note..."
            onKeyDown={(e) => e.key === 'Enter' && handleNote()}
          />
          <button
            onClick={handleNote}
            className="px-2 py-1 text-xs bg-blue-500 text-white rounded"
          >
            Save
          </button>
        </div>
      )}
    </div>
  );
}
```

### Deliverable

- Full data table with sorting, expandable rows
- Action buttons working
- Signal details displayed in expanded view
- Professional styling with Tailwind

---

## Phase 4: Filters & Sidebar

**Goal**: Add filtering UI and company management sidebar.

### Filters.tsx

```typescript
interface Props {
  timeWindow: number;
  onTimeWindowChange: (days: number) => void;
  hideContacted: boolean;
  onHideContactedChange: (hide: boolean) => void;
  hideSnoozed: boolean;
  onHideSnoozedChange: (hide: boolean) => void;
}

export default function Filters({
  timeWindow,
  onTimeWindowChange,
  hideContacted,
  onHideContactedChange,
  hideSnoozed,
  onHideSnoozedChange,
}: Props) {
  return (
    <div className="flex items-center gap-6 p-4 bg-gray-50 rounded-lg mb-4">
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-600">Time window:</label>
        <select
          value={timeWindow}
          onChange={(e) => onTimeWindowChange(Number(e.target.value))}
          className="px-3 py-1.5 border rounded text-sm"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={hideContacted}
          onChange={(e) => onHideContactedChange(e.target.checked)}
          className="rounded"
        />
        Hide contacted
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={hideSnoozed}
          onChange={(e) => onHideSnoozedChange(e.target.checked)}
          className="rounded"
        />
        Hide snoozed
      </label>
    </div>
  );
}
```

### Sidebar.tsx

```typescript
import { useState } from 'react';
import { Company } from '../types';

interface Props {
  companies: Company[];
  onAddCompany: (name: string, ticker?: string) => void;
  onRunPipeline: () => void;
  onRefreshFinancials: () => void;
  onClearSignals: () => void;
  isLoading: boolean;
}

export default function Sidebar({
  companies,
  onAddCompany,
  onRunPipeline,
  onRefreshFinancials,
  onClearSignals,
  isLoading,
}: Props) {
  const [name, setName] = useState('');
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onAddCompany(name.trim(), ticker.trim() || undefined);
      setName('');
      setTicker('');
    }
  };

  return (
    <aside className="w-64 bg-white border-r p-4 flex flex-col h-screen">
      <h2 className="text-lg font-semibold mb-4">Companies</h2>

      <form onSubmit={handleSubmit} className="space-y-2 mb-6">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Company name"
          className="w-full px-3 py-2 border rounded text-sm"
        />
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Ticker (optional)"
          className="w-full px-3 py-2 border rounded text-sm"
        />
        <button
          type="submit"
          className="w-full px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          Add Company
        </button>
      </form>

      <div className="flex-1 overflow-auto">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Watchlist</h3>
        {companies.length === 0 ? (
          <p className="text-sm text-gray-400">No companies yet</p>
        ) : (
          <ul className="space-y-1">
            {companies.map((c) => (
              <li key={c.id} className="text-sm">
                {c.name}
                {c.ticker && <span className="text-gray-400 ml-1">({c.ticker})</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="border-t pt-4 space-y-2">
        <button
          onClick={onRunPipeline}
          disabled={isLoading || companies.length === 0}
          className="w-full px-3 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:opacity-50"
        >
          🔄 Run Pipeline
        </button>
        <button
          onClick={onRefreshFinancials}
          disabled={isLoading || companies.length === 0}
          className="w-full px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50"
        >
          📈 Refresh Financials
        </button>
        <button
          onClick={onClearSignals}
          disabled={isLoading}
          className="w-full px-3 py-2 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300 disabled:opacity-50"
        >
          🗑️ Clear Signals
        </button>
      </div>
    </aside>
  );
}
```

### Deliverable

- Filter bar with time window and hide toggles
- Sidebar with company management
- Pipeline/refresh buttons

---

## Phase 5: Integration & Polish

**Goal**: Wire everything together, add loading states, error handling.

### App.tsx

```typescript
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api/client';
import CompanyTable from './components/CompanyTable';
import Filters from './components/Filters';
import Sidebar from './components/Sidebar';
import { Financials } from './types';

export default function App() {
  const queryClient = useQueryClient();
  const [timeWindow, setTimeWindow] = useState(7);
  const [hideContacted, setHideContacted] = useState(false);
  const [hideSnoozed, setHideSnoozed] = useState(false);

  // Queries
  const companiesQuery = useQuery({
    queryKey: ['companies'],
    queryFn: api.getCompanies,
  });

  const summaryQuery = useQuery({
    queryKey: ['summary', timeWindow],
    queryFn: () => api.getCompanySummary(timeWindow),
  });

  const financialsQuery = useQuery({
    queryKey: ['financials'],
    queryFn: api.getFinancials,
  });

  const hiddenQuery = useQuery({
    queryKey: ['hidden', hideContacted, hideSnoozed],
    queryFn: () =>
      api.getHiddenCompanies(
        hideContacted ? 7 : 0,
        hideSnoozed ? 7 : 0
      ),
    enabled: hideContacted || hideSnoozed,
  });

  // Mutations
  const addCompanyMutation = useMutation({
    mutationFn: ({ name, ticker }: { name: string; ticker?: string }) =>
      api.addCompany(name, ticker),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
  });

  const outreachMutation = useMutation({
    mutationFn: ({
      companyId,
      action,
      note,
    }: {
      companyId: string;
      action: string;
      note?: string;
    }) => api.logOutreach(companyId, action, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hidden'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
    },
  });

  const pipelineMutation = useMutation({
    mutationFn: api.runPipeline,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['summary'] }),
  });

  const financialsMutation = useMutation({
    mutationFn: api.refreshFinancials,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['financials'] }),
  });

  const clearMutation = useMutation({
    mutationFn: api.clearSignals,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['summary'] }),
  });

  // Process data
  const financialsMap: Record<string, Financials> = {};
  financialsQuery.data?.forEach((f) => {
    financialsMap[f.company_id] = f;
  });

  const hiddenSet = new Set(hiddenQuery.data || []);
  const filteredData =
    summaryQuery.data?.filter((c) => !hiddenSet.has(c.company_id)) || [];

  const isLoading =
    pipelineMutation.isPending ||
    financialsMutation.isPending ||
    clearMutation.isPending;

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar
        companies={companiesQuery.data || []}
        onAddCompany={(name, ticker) => addCompanyMutation.mutate({ name, ticker })}
        onRunPipeline={() => pipelineMutation.mutate()}
        onRefreshFinancials={() => financialsMutation.mutate()}
        onClearSignals={() => clearMutation.mutate()}
        isLoading={isLoading}
      />

      <main className="flex-1 p-6 overflow-auto">
        <h1 className="text-2xl font-bold mb-6">📊 Sales Intelligence Tracker</h1>

        <Filters
          timeWindow={timeWindow}
          onTimeWindowChange={setTimeWindow}
          hideContacted={hideContacted}
          onHideContactedChange={setHideContacted}
          hideSnoozed={hideSnoozed}
          onHideSnoozedChange={setHideSnoozed}
        />

        {summaryQuery.isLoading ? (
          <div className="text-center py-10 text-gray-500">Loading...</div>
        ) : filteredData.length === 0 ? (
          <div className="text-center py-10 text-gray-500">
            No signals found. Add companies and run the pipeline.
          </div>
        ) : (
          <CompanyTable
            data={filteredData}
            financials={financialsMap}
            onOutreachAction={(companyId, action, note) =>
              outreachMutation.mutate({ companyId, action, note })
            }
          />
        )}
      </main>
    </div>
  );
}
```

### Deliverable

- Fully functional app
- Loading states
- Error handling
- Data refetching on mutations

---

## Phase 6: Deployment

### Backend (Railway)

1. Create Railway account at railway.app
2. Connect GitHub repo
3. Set root directory to `/backend`
4. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ANTHROPIC_API_KEY`
5. Deploy automatically on push

### Frontend (Vercel)

1. Create Vercel account at vercel.com
2. Import GitHub repo
3. Set root directory to `/frontend`
4. Add environment variable:
   - `VITE_API_URL=https://your-backend.railway.app`
5. Deploy automatically on push

### Cost

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Vercel | Hobby | $0 |
| Railway | Hobby | $5 |
| Supabase | Free | $0 |
| **Total** | | **$5/month** |

---

## Migration Timeline

| Phase | Description | Effort |
|-------|-------------|--------|
| 1 | Backend API | 2-3 hours |
| 2 | React Setup | 1-2 hours |
| 3 | Data Table | 3-4 hours |
| 4 | Filters & Sidebar | 2-3 hours |
| 5 | Integration | 2-3 hours |
| 6 | Deployment | 1-2 hours |
| **Total** | | **12-17 hours** |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Learning curve (React/TypeScript) | Start with working examples, iterate |
| CORS issues | Configure FastAPI CORS middleware properly |
| Two deployments to manage | GitHub Actions can deploy both on push |
| Losing Streamlit's quick iteration | Vite hot reload is very fast |
| Breaking existing functionality | Keep Streamlit app until React is ready |

---

## Success Criteria

After migration:

- [ ] Single unified data table with all company info
- [ ] Expandable rows showing news/signals
- [ ] Sort by any column
- [ ] Filter by urgency, time window, contacted/snoozed status
- [ ] Action buttons work inline
- [ ] Professional, polished appearance
- [ ] Load time under 2 seconds
- [ ] Mobile-responsive
- [ ] Deployed and accessible via public URL
- [ ] Total cost $5/month or less

---

## Next Steps

1. **Confirm this plan** - Any changes before we start?
2. **Phase 1** - Create FastAPI backend in `/backend` directory
3. **Test locally** - Backend + existing Streamlit (parallel operation)
4. **Phase 2-5** - Build React frontend incrementally
5. **Phase 6** - Deploy both services
6. **Cutover** - Retire Streamlit app
