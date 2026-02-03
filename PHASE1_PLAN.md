# Phase 1: Company-Centric UI Restructure

## Objective

Replace current signal-centric UI with company-centric table using only existing data (no new APIs or schema changes).

---

## Target UI

| Company | IR Pain | Signal Count | Urgency | Details |
|---------|---------|--------------|---------|---------|
| Apple (AAPL) | 85% - analyst downgrade | 3 | 🔥 Call today | [expand] |
| Microsoft (MSFT) | 62% - earnings miss | 2 | 🟡 Call this week | [expand] |
| Tesla (TSLA) | 41% - peer pressure | 1 | ⚪ Monitor | [expand] |

Clicking expand shows all signals for that company with article details.

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
1. Query signals joined with companies, filtered by `created_at >= now - days`
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

**Company table with expanders:**
```python
st.header("🎯 Companies to Contact")

company_data = db.get_company_pain_summary(days=time_window)

if company_data:
    for company in company_data:
        urgency = compute_urgency(
            company['max_pain_score'],
            company['newest_signal_age_hours']
        )

        with st.expander(
            f"{company['ticker'] or ''} **{company['company_name']}** | "
            f"Pain: {company['max_pain_score']:.0%} | "
            f"{company['signal_count']} signals | "
            f"{urgency['icon']} {urgency['label']}"
        ):
            # Show max pain reason
            st.write(f"**Top Signal:** {company['max_pain_summary']}")

            # Show all signals in a mini-table
            for signal in company['signals']:
                icon = config.SIGNAL_ICONS.get(signal['signal_type'], '📰')
                st.write(f"- {icon} {signal['signal_type']}: {signal['summary']}")
                if signal.get('url'):
                    st.caption(f"Source: {signal['source']} | [Article]({signal['url']})")
```

### Keep sidebar unchanged

---

## Step 4: Add Urgency Helper Function

Add to app.py:

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

## Step 5: Update CSV Export

Change export to company-level data:

```python
export_data = []
for company in company_data:
    urgency = compute_urgency(
        company['max_pain_score'],
        company['newest_signal_age_hours']
    )
    export_data.append({
        "Company": company['company_name'],
        "Ticker": company['ticker'],
        "IR Pain Score": f"{company['max_pain_score']:.0%}",
        "Top Signal": company['max_pain_summary'],
        "Signal Count": company['signal_count'],
        "Urgency": urgency['label'],
    })

df = pd.DataFrame(export_data)
st.download_button(
    label="📥 Export to CSV",
    data=df.to_csv(index=False),
    file_name="companies_to_contact.csv",
    mime="text/csv",
)
```

---

## Files Changed

| File | Changes |
|------|---------|
| `config.py` | Add TIME_WINDOW_OPTIONS, URGENCY_THRESHOLDS, URGENCY_DISPLAY |
| `db.py` | Add `get_company_pain_summary()` function |
| `app.py` | Remove 3 sections, add company table with expanders |

**No changes to:** etl.py, schema.sql, requirements.txt

---

## Testing Plan

1. **Add 3-5 test companies** with known recent news (e.g., Apple, Tesla, Microsoft)
2. **Run pipeline** to fetch and classify signals
3. **Verify table shows**:
   - One row per company (not per signal)
   - Correct max pain score
   - Correct signal count
   - Expandable details with all signals
4. **Verify sorting**: Highest pain companies at top
5. **Verify time window filter**: Changing window updates counts
6. **Verify CSV export**: Company-level data exports correctly
7. **Verify urgency**:
   - High pain + recent signal = 🔥
   - Medium pain or older signal = 🟡
   - Low pain + old signal = ⚪

---

## Acceptance Criteria

- [ ] Single table with one row per company
- [ ] Columns: Company, IR Pain (score + reason), Signal Count, Urgency
- [ ] Expandable rows show all signals for that company
- [ ] Sorted by IR Pain score descending (highest pain first)
- [ ] Time window filter (7/14/30 days)
- [ ] CSV export at company level
- [ ] No new dependencies or schema changes
- [ ] Sidebar unchanged (company management still works)

---

## Estimated Scope

| File | Lines Changed | Complexity |
|------|---------------|------------|
| config.py | +15 | Low |
| db.py | +40 | Medium |
| app.py | -100, +80 | Medium (net simpler) |
