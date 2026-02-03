# Implementation Plan: Company-Centric Dashboard

## Overview

Transform the dashboard from a **signal-centric** view (one row per article) to a **company-centric** view (one row per company) that enables quick prioritization of sales outreach.

---

## Target Table Structure

| Column | Source | Description |
|--------|--------|-------------|
| Company | DB | Name (ticker) |
| Stock Trend | yfinance | +/- % over configurable window |
| Market Cap | yfinance | Small (<$2B) / Mid ($2-10B) / Large (>$10B) |
| Last Earnings | yfinance | Date of most recent earnings |
| Next Earnings | yfinance | Date of upcoming earnings |
| IR Pain | Computed | Max pain score + brief reason (e.g., "0.85 - analyst downgrade") |
| Signal Count | Computed | # of pain signals in selected period |
| Urgency | Computed | 🔥 Hot / 🟡 Warm / ⚪ Monitor |
| AI Summary | Claude | Aggregated summary, expandable to see individual articles |
| Talking Points | Claude | Suggested outreach opener based on signal type |
| Actions | DB | Contacted / Snooze / Notes |

---

## Phase 1: Company-Centric UI Restructure

**Goal**: Replace current UI with company-centric table using existing data.

### Changes

**app.py** (complete rewrite of main area):
- Remove "IR Teams in Pain" cards section
- Remove "Company Overview" cards section
- Remove "All Signals" per-signal table
- Add single company table with columns:
  - Company, IR Pain, Signal Count, Urgency, AI Summary (expandable)
- Add configurable time window filter (7d / 14d / 30d)
- Keep sidebar as-is (company management, pipeline trigger)

**db.py**:
- Add `get_company_pain_summary(days=7)` - returns aggregated data per company:
  - company_id, company_name, ticker
  - max_pain_score, max_pain_reason (summary from highest pain signal)
  - signal_count
  - signals list (for expandable detail)

**config.py**:
- Add `URGENCY_THRESHOLDS` dict
- Add `TIME_WINDOW_OPTIONS` list

**Files unchanged**: etl.py, schema.sql, requirements.txt

### Urgency Logic

```
if max_pain >= 0.7 AND newest_signal < 48hrs:
    🔥 Hot - "Call today"
elif max_pain >= 0.5 OR newest_signal < 7 days:
    🟡 Warm - "Call this week"
else:
    ⚪ Monitor
```

### Deliverable

Working company table with:
- Sortable by IR Pain score
- Expandable rows showing individual signals
- Time window filter
- CSV export of company-level data

---

## Phase 2: Financial Data Integration

**Goal**: Add stock trend, market cap, and earnings dates via yfinance.

### Changes

**requirements.txt**:
- Add `yfinance`

**etl.py**:
- Add `fetch_company_financials(ticker)` function:
  - Returns: price_change_pct, market_cap, last_earnings, next_earnings
- Modify `run_pipeline()` to optionally refresh financials

**db.py**:
- Add `upsert_company_financials()` function
- Add `get_company_financials()` function

**schema.sql**:
- Add `company_financials` table:
  ```sql
  CREATE TABLE company_financials (
      company_id UUID PRIMARY KEY REFERENCES companies(id),
      price_change_7d REAL,
      price_change_30d REAL,
      market_cap BIGINT,
      market_cap_tier TEXT,  -- 'small', 'mid', 'large'
      last_earnings DATE,
      next_earnings DATE,
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```

**config.py**:
- Add `MARKET_CAP_TIERS` thresholds
- Add `PRICE_CHANGE_WINDOW` default

**app.py**:
- Add Stock Trend column (color-coded: green positive, red negative)
- Add Market Cap column
- Add Last/Next Earnings columns
- Add "Refresh Financials" button in sidebar

### Deliverable

Complete "at a glance" table with financial context for each company.

---

## Phase 3: Talking Points & Enhanced Urgency

**Goal**: Add AI-generated talking points and refined urgency indicator.

### Changes

**config.py**:
- Add `TALKING_POINTS_TEMPLATES` dict keyed by signal_type:
  ```python
  TALKING_POINTS_TEMPLATES = {
      "analyst_negative": "We noticed the recent analyst {action}. We help IR teams rebuild analyst relationships and improve targeting...",
      "leadership_change": "Congratulations on the new {role}. Leadership transitions are often a good time to evaluate IR partners...",
      ...
  }
  ```
- Add `TALKING_POINTS_PROMPT` for Claude to customize template with specifics

**etl.py**:
- Add `generate_talking_point(signal_type, summary, company_name)` function
- Modify signal creation to generate and store talking point

**db.py**:
- Modify `add_signal()` to accept `talking_point` field

**schema.sql**:
- Add `talking_point TEXT` column to signals table

**app.py**:
- Add Talking Points column (truncated, expandable)
- Refine urgency indicator with earnings proximity:
  - If next_earnings < 14 days AND has pain signal → boost urgency

### Deliverable

Actionable outreach suggestions for each company.

---

## Phase 4: Outreach Actions & Workflow

**Goal**: Track outreach status (contacted, snoozed, notes).

### Changes

**schema.sql**:
- Add `outreach_actions` table:
  ```sql
  CREATE TABLE outreach_actions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
      action_type TEXT NOT NULL,  -- 'contacted', 'snoozed', 'note'
      note TEXT,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```

**db.py**:
- Add `add_outreach_action(company_id, action_type, note)`
- Add `get_outreach_actions(company_id)`
- Add `get_last_contact(company_id)`

**app.py**:
- Add Actions column with buttons:
  - ✅ Mark Contacted (logs timestamp)
  - 😴 Snooze (hides for X days)
  - 📝 Add Note (text input modal)
- Add filter: "Hide contacted" / "Hide snoozed"
- Show last contacted date if exists

**config.py**:
- Add `SNOOZE_DURATION_DAYS` default

### Deliverable

Complete outreach workflow tracking within the app.

---

## File Change Summary

| File | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| app.py | ✏️ Major | ✏️ Add cols | ✏️ Add cols | ✏️ Add actions |
| db.py | ✏️ Add func | ✏️ Add funcs | ✏️ Modify | ✏️ Add funcs |
| etl.py | - | ✏️ Add func | ✏️ Add func | - |
| config.py | ✏️ Add constants | ✏️ Add constants | ✏️ Add templates | ✏️ Add constant |
| schema.sql | - | ✏️ Add table | ✏️ Add column | ✏️ Add table |
| requirements.txt | - | ✏️ Add yfinance | - | - |

---

## Success Criteria

After all phases:

1. **One glance prioritization**: Sort by IR Pain, see who to call first
2. **Full context**: Stock trend, earnings timing, pain signals all visible
3. **Actionable**: Talking points ready, click to mark contacted
4. **Scalable**: Works with 100+ companies, table is scannable
5. **Cost efficient**: Still under $5/month target

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| yfinance breaks (unofficial API) | Graceful fallback, show "N/A" for financial cols |
| Too many Claude calls for talking points | Generate only for high-pain signals, cache aggressively |
| Table too wide on mobile | Responsive design, hide low-priority cols on small screens |
| Slow load with many companies | Pagination, lazy-load expanded details |

---

# Phase 1 Detailed Plan

## Objective

Replace current signal-centric UI with company-centric table using only existing data (no new APIs or schema changes).

---

## Step 1: Update config.py

Add new constants:

```python
# Time window options for filtering
TIME_WINDOW_OPTIONS = [7, 14, 30]  # days
DEFAULT_TIME_WINDOW = 7

# Urgency thresholds
URGENCY_THRESHOLDS = {
    "hot": {"min_pain": 0.7, "max_age_hours": 48},
    "warm": {"min_pain": 0.5, "max_age_hours": 168},  # 7 days
}

# Urgency display
URGENCY_DISPLAY = {
    "hot": {"icon": "🔥", "label": "Call today", "color": "#dc3545"},
    "warm": {"icon": "🟡", "label": "Call this week", "color": "#fd7e14"},
    "monitor": {"icon": "⚪", "label": "Monitor", "color": "#6c757d"},
}
```

---

## Step 2: Update db.py

Add new function `get_company_pain_summary(days=7)`:

```python
def get_company_pain_summary(days: int = 7) -> list:
    """
    Get aggregated pain data per company for the specified time window.

    Returns list of dicts:
        - company_id, company_name, ticker
        - max_pain_score, max_pain_signal_type, max_pain_summary
        - signal_count
        - newest_signal_age_hours
        - signals (list of all signals for expansion)
    """
```

Implementation approach:
1. Query signals joined with companies, filtered by created_at >= now - days
2. Group by company in Python (Supabase free tier limitation)
3. For each company, compute: max pain, count, newest signal age
4. Return sorted by max_pain_score descending

---

## Step 3: Rewrite app.py Main Area

### Remove:
- "🎯 IR Teams in Pain" section (lines 89-121)
- "📋 Company Overview" section (lines 123-150)
- "📰 All Signals" section (lines 152-220)

### Add:

**Filters row:**
```python
col1, col2 = st.columns([1, 3])
with col1:
    time_window = st.selectbox(
        "Time Window",
        options=config.TIME_WINDOW_OPTIONS,
        format_func=lambda x: f"Last {x} days"
    )
```

**Company table:**
```python
st.header("🎯 Companies to Contact")

company_data = db.get_company_pain_summary(days=time_window)

if company_data:
    for company in company_data:
        with st.expander(
            f"{company['ticker'] or ''} **{company['company_name']}** | "
            f"Pain: {company['max_pain_score']:.0%} | "
            f"{company['signal_count']} signals | "
            f"{urgency_icon}"
        ):
            # Show max pain reason
            st.write(f"**Top Signal:** {company['max_pain_summary']}")

            # Show all signals in a mini-table
            for signal in company['signals']:
                st.write(f"- {signal['signal_type']}: {signal['summary']}")
```

**Alternative: Use st.dataframe with row selection** (cleaner but less expandable)

### Keep sidebar unchanged

---

## Step 4: Update CSV Export

Change export to company-level data:

```python
export_data = []
for company in company_data:
    export_data.append({
        "Company": company['company_name'],
        "Ticker": company['ticker'],
        "IR Pain Score": company['max_pain_score'],
        "Top Signal": company['max_pain_summary'],
        "Signal Count": company['signal_count'],
        "Urgency": urgency_label,
    })

df = pd.DataFrame(export_data)
```

---

## Step 5: Compute Urgency

Add helper function in app.py:

```python
def compute_urgency(max_pain: float, newest_signal_age_hours: float) -> dict:
    """Returns urgency dict with icon, label, color."""
    thresholds = config.URGENCY_THRESHOLDS
    display = config.URGENCY_DISPLAY

    if (max_pain >= thresholds["hot"]["min_pain"] and
        newest_signal_age_hours <= thresholds["hot"]["max_age_hours"]):
        return display["hot"]
    elif (max_pain >= thresholds["warm"]["min_pain"] or
          newest_signal_age_hours <= thresholds["warm"]["max_age_hours"]):
        return display["warm"]
    else:
        return display["monitor"]
```

---

## Testing Plan

1. **Add 3-5 test companies** with known recent news
2. **Run pipeline** to fetch and classify signals
3. **Verify table shows**:
   - One row per company (not per signal)
   - Correct max pain score
   - Correct signal count
   - Expandable details with all signals
4. **Verify sorting**: Highest pain companies at top
5. **Verify time window filter**: Changing window updates counts
6. **Verify CSV export**: Company-level data exports correctly

---

## Acceptance Criteria

- [ ] Single table with one row per company
- [ ] Columns: Company, IR Pain (score + reason), Signal Count, Urgency
- [ ] Expandable rows show all signals for that company
- [ ] Sortable by IR Pain score (default: descending)
- [ ] Time window filter (7/14/30 days)
- [ ] CSV export at company level
- [ ] No new dependencies or schema changes
- [ ] Sidebar unchanged (company management still works)

---

## Estimated Changes

| File | Lines Changed | Complexity |
|------|---------------|------------|
| config.py | +15 | Low |
| db.py | +40 | Medium |
| app.py | -100, +80 | Medium (net reduction) |

Total: ~2-3 hours of implementation

---

# Phase 4 Detailed Plan

## Objective

Add outreach workflow tracking so users can mark companies as contacted, snooze them, and add notes - all within the app.

---

## Step 1: Update schema.sql

Add new table for tracking outreach actions:

```sql
-- Outreach actions (contacted, snoozed, notes)
CREATE TABLE IF NOT EXISTS outreach_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,  -- 'contacted', 'snoozed', 'note'
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_company ON outreach_actions(company_id);
CREATE INDEX IF NOT EXISTS idx_outreach_type ON outreach_actions(action_type);
```

---

## Step 2: Update config.py

Add outreach workflow constants:

```python
# Outreach workflow settings
SNOOZE_DURATION_DAYS = 7  # Default snooze period
CONTACTED_HIDE_DAYS = 7   # Hide contacted companies for this many days

# Outreach action types
OUTREACH_ACTION_TYPES = {
    "contacted": {"icon": "✅", "label": "Contacted"},
    "snoozed": {"icon": "😴", "label": "Snoozed"},
    "note": {"icon": "📝", "label": "Note"},
}
```

---

## Step 3: Update db.py

Add new functions:

```python
def add_outreach_action(company_id: str, action_type: str, note: str = None) -> dict:
    """Log an outreach action for a company."""
    client = get_client()
    data = {
        "company_id": company_id,
        "action_type": action_type,
        "note": note,
    }
    result = client.table("outreach_actions").insert(data).execute()
    return result.data[0] if result.data else None


def get_outreach_actions(company_id: str, limit: int = 10) -> list:
    """Get recent outreach actions for a company."""
    client = get_client()
    result = client.table("outreach_actions").select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).limit(limit).execute()
    return result.data


def get_last_contact(company_id: str) -> dict:
    """Get most recent 'contacted' action for a company."""
    client = get_client()
    result = client.table("outreach_actions").select("*").eq(
        "company_id", company_id
    ).eq("action_type", "contacted").order("created_at", desc=True).limit(1).execute()
    return result.data[0] if result.data else None


def get_companies_to_hide(contacted_days: int = 7, snoozed_days: int = 7) -> set:
    """Get company IDs that should be hidden (recently contacted or snoozed)."""
    client = get_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(contacted_days, snoozed_days))

    result = client.table("outreach_actions").select(
        "company_id, action_type, created_at"
    ).in_("action_type", ["contacted", "snoozed"]).gte(
        "created_at", cutoff.isoformat()
    ).execute()

    hide_ids = set()
    now = datetime.now(timezone.utc)

    for action in result.data:
        created = datetime.fromisoformat(action["created_at"].replace("Z", "+00:00"))
        age_days = (now - created).days

        if action["action_type"] == "contacted" and age_days < contacted_days:
            hide_ids.add(action["company_id"])
        elif action["action_type"] == "snoozed" and age_days < snoozed_days:
            hide_ids.add(action["company_id"])

    return hide_ids
```

---

## Step 4: Update app.py

### Add filter checkboxes (below time window filter):

```python
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    time_window = st.selectbox(...)
with col2:
    hide_contacted = st.checkbox("Hide contacted", value=True)
    hide_snoozed = st.checkbox("Hide snoozed", value=True)
```

### Get companies to hide:

```python
# Load companies to hide based on filters
companies_to_hide = set()
if hide_contacted or hide_snoozed:
    companies_to_hide = db.get_companies_to_hide(
        contacted_days=config.CONTACTED_HIDE_DAYS if hide_contacted else 0,
        snoozed_days=config.SNOOZE_DURATION_DAYS if hide_snoozed else 0,
    )
```

### Filter company list:

```python
for company in company_summaries:
    # Skip hidden companies
    if company["company_id"] in companies_to_hide:
        continue
    ...
```

### Add action buttons inside each expander:

```python
with st.expander(header):
    # ... existing content ...

    st.divider()

    # Action buttons row
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button("✅ Contacted", key=f"contact_{company_id}"):
            db.add_outreach_action(company_id, "contacted")
            st.success("Marked as contacted")
            st.rerun()

    with btn_col2:
        if st.button("😴 Snooze", key=f"snooze_{company_id}"):
            db.add_outreach_action(company_id, "snoozed")
            st.success(f"Snoozed for {config.SNOOZE_DURATION_DAYS} days")
            st.rerun()

    with btn_col3:
        note = st.text_input("Add note", key=f"note_input_{company_id}")
        if st.button("📝 Save", key=f"note_{company_id}"):
            if note:
                db.add_outreach_action(company_id, "note", note)
                st.success("Note saved")
                st.rerun()

    # Show last contact and notes
    last_contact = db.get_last_contact(company_id)
    if last_contact:
        contact_date = last_contact["created_at"][:10]
        st.caption(f"Last contacted: {contact_date}")

    actions = db.get_outreach_actions(company_id)
    notes = [a for a in actions if a["action_type"] == "note" and a.get("note")]
    if notes:
        st.markdown("**Notes:**")
        for n in notes[:3]:
            st.caption(f"• {n['note']} ({n['created_at'][:10]})")
```

---

## Testing Plan

1. **Run schema migration** in Supabase SQL Editor
2. **Test contacted button**: Click, verify company hides when filter is on
3. **Test snooze button**: Click, verify company hides, reappears after duration
4. **Test notes**: Add note, verify it displays and persists
5. **Test filters**: Toggle checkboxes, verify correct companies show/hide
6. **Test persistence**: Refresh page, verify actions are saved

---

## Acceptance Criteria

- [ ] `outreach_actions` table created
- [ ] "✅ Contacted" button logs action and hides company (when filter on)
- [ ] "😴 Snooze" button hides company for configured duration
- [ ] "📝 Add Note" saves and displays notes
- [ ] Filter checkboxes work correctly
- [ ] Last contacted date displays
- [ ] Recent notes display (max 3)
- [ ] Actions persist across sessions

---

## Estimated Changes

| File | Lines Changed | Complexity |
|------|---------------|------------|
| schema.sql | +10 | Low |
| config.py | +10 | Low |
| db.py | +50 | Medium |
| app.py | +60 | Medium |

Total: ~2-3 hours of implementation
