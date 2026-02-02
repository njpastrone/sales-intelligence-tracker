# Plan: IR Pain Signal Detection for Sales Outreach

## Goal

Transform the signal classification to identify **moments when IR teams are likely in pain** and receptive to sales outreach.

---

## The Insight

| What IROs Care About | Pain Signal to Flag | Why They'd Take a Call |
|---------------------|---------------------|------------------------|
| Activist defense | 13-D filing, ownership shake-up | "We can help you monitor/respond" |
| Analyst relations | Downgrade, coverage drop, missed estimates | "We can help with messaging/targeting" |
| Peer benchmarking | Competitor outperforming, losing market share | "We can help you tell a better story" |
| ESG/governance | Rating downgrade, proxy fight, ISS against | "We can help with ESG narrative" |
| Stock volatility | Big price drop, high short interest | "We can help stabilize investor base" |
| Leadership transition | New CFO, new IRO, CEO change | "New leader = new vendor evaluation" |
| Capital markets | Failed offering, debt downgrade | "We can help with investor outreach" |

---

## Implementation Plan

### 1. Update Signal Categories (config.py)

Replace current categories with IR-pain-focused types:

```python
SIGNAL_TYPES = {
    "activist_risk": "13-D filings, ownership changes, activist campaigns",
    "analyst_negative": "Downgrades, coverage drops, estimate cuts, price target cuts",
    "earnings_miss": "Missed expectations, guidance cuts, revenue decline",
    "leadership_change": "New CEO, CFO, IRO, board shakeups",
    "governance_issue": "Proxy fights, ISS/GL against, shareholder proposals",
    "esg_negative": "ESG rating downgrades, controversies, sustainability issues",
    "stock_pressure": "Sharp price drops, high short interest, volatility spikes",
    "capital_stress": "Failed offerings, debt downgrades, dividend cuts",
    "peer_pressure": "Competitor wins, market share loss, sector underperformance",
    "neutral": "General news, not a pain signal",
}
```

### 2. Update Classification Prompt (config.py)

New prompt focused on identifying IR pain:

```
You are helping salespeople identify when IR teams might need help.

Analyze this headline about {company_name} and determine if it signals IR team pain.

Headline: {title}
Source: {source}

Pain signal types (flag these - IR team likely needs help):
- activist_risk: Ownership changes, 13-D filings, activist involvement
- analyst_negative: Downgrades, price target cuts, coverage drops
- earnings_miss: Missed estimates, guidance cuts, disappointing results
- leadership_change: New CEO, CFO, IRO, or major board changes
- governance_issue: Proxy fights, adverse proxy advisor recommendations
- esg_negative: ESG rating downgrades, sustainability controversies
- stock_pressure: Sharp stock drops, short interest spikes
- capital_stress: Failed offerings, credit downgrades, dividend cuts
- peer_pressure: Competitor outperformance, market share losses

Use "neutral" for general news that doesn't indicate IR pain.

Respond in JSON only:
{
    "summary": "1-2 sentence summary of the signal",
    "signal_type": "one of the types above",
    "relevance_score": 0.0-1.0 (is this actually about the company?),
    "ir_pain_score": 0.0-1.0 (how much pain is the IR team likely feeling?)
}

IR pain scoring:
- 0.8-1.0: Acute pain (activist attack, major downgrade, CEO fired)
- 0.5-0.7: Moderate pain (earnings miss, analyst concern, ESG issue)
- 0.2-0.4: Minor pain (routine negative news, peer doing well)
- 0.0-0.2: No pain (neutral or positive news)
```

### 3. Update Database (db.py)

- Rename `sales_relevance` → `ir_pain_score` (or keep column name, just use differently)
- Update `get_hot_signals()` to sort by `ir_pain_score`

### 4. Update ETL (etl.py)

- Parse `ir_pain_score` from Claude response
- Map to database field

### 5. Update Dashboard (app.py)

**Hot Signals section rename:**
- "🔥 Hot Signals" → "🎯 IR Teams in Pain"
- Show signals with high `ir_pain_score`
- Add context: "These companies may be receptive to outreach"

**Signal type icons:**
```python
SIGNAL_ICONS = {
    "activist_risk": "🦈",      # Shark circling
    "analyst_negative": "📉",   # Downward trend
    "earnings_miss": "❌",      # Miss
    "leadership_change": "🔄",  # Change/transition
    "governance_issue": "⚔️",   # Conflict
    "esg_negative": "🌍",       # ESG
    "stock_pressure": "📊",     # Stock chart
    "capital_stress": "💸",     # Money flying away
    "peer_pressure": "🏃",      # Competitor running ahead
    "neutral": "📰",            # General news
}
```

**Company cards:**
- Show pain signal breakdown per company
- Highlight companies with multiple pain signals (compounding problems = more receptive)

**Table updates:**
- Rename "Sales" column → "Pain Score"
- Color code: Red (high pain) → Yellow → Gray (neutral)

---

## Files to Modify

| File | Changes |
|------|---------|
| `config.py` | New SIGNAL_TYPES, SIGNAL_ICONS, updated prompt |
| `etl.py` | Parse ir_pain_score, validate signal types |
| `db.py` | Update get_hot_signals sort, minor renames |
| `app.py` | Rename sections, update icons, color coding |

---

## Verification

After implementation:
1. Clear existing signals
2. Run pipeline with test companies
3. Verify pain signals are being classified correctly:
   - Downgrade news → `analyst_negative` with high pain score
   - CEO departure → `leadership_change` with high pain score
   - Routine product news → `neutral` with low pain score
4. Check dashboard shows pain signals prominently

---

## Example Output

**Before (sales-focused):**
```
🔥 HOT SIGNALS
👔 AAPL: New CFO announced - leadership (85% sales relevance)
```

**After (IR-pain-focused):**
```
🎯 IR TEAMS IN PAIN
🔄 AAPL: CFO departure after 2 years - leadership_change (90% pain)
   → New CFO = vendor evaluation window, reach out now
```

---

## Constraints

- Still 4 core files
- Still Claude Haiku
- Same API cost (just better prompt)
- No new data sources (still Google News RSS)

---

## Future Enhancements (Not Now)

- Add SEC EDGAR RSS for 13-D/8-K filings (better activist/regulatory signals)
- Add analyst rating feed (direct downgrade data)
- Multi-signal scoring (company with 3 pain signals > company with 1)
