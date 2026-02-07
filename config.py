# config.py - Constants, settings, and prompts
# No logic or side effects here

# Signal types for IR pain detection
SIGNAL_TYPES = {
    "activist_risk": "13-D filings, ownership changes, activist campaigns",
    "analyst_negative": "Downgrades, coverage drops, estimate cuts",
    "earnings_miss": "Missed expectations, guidance cuts",
    "leadership_change": "New CEO, CFO, IRO, board changes",
    "governance_issue": "Proxy fights, ISS against, shareholder proposals",
    "esg_negative": "ESG rating downgrades, controversies",
    "stock_pressure": "Sharp drops, high short interest",
    "capital_stress": "Failed offerings, debt downgrades, dividend cuts",
    "peer_pressure": "Competitor wins, market share loss",
    "neutral": "General news, not a pain signal",
}

# Signal type icons for UI display
SIGNAL_ICONS = {
    "activist_risk": "🦈",
    "analyst_negative": "📉",
    "earnings_miss": "❌",
    "leadership_change": "🔄",
    "governance_issue": "⚔️",
    "esg_negative": "🌍",
    "stock_pressure": "📊",
    "capital_stress": "💸",
    "peer_pressure": "🏃",
    "neutral": "📰",
}

# Google News RSS
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

# Claude settings
CLAUDE_MODEL = "claude-3-5-haiku-20241022"
CLAUDE_MAX_TOKENS = 500
CLAUDE_TEMPERATURE = 0.1

# Keywords that indicate non-IR news (HR, legal, operational matters)
# Headlines matching these patterns are overridden to neutral regardless of model output
NON_IR_KEYWORDS = [
    "discrimination", "eeoc", "dei policy", "dei policies", "dei program",
    "workplace bias", "bias against", "labor dispute", "employee lawsuit",
    "workers' comp", "harassment", "wrongful termination", "nlrb",
    "union vote", "product recall", "food safety", "customer complaint",
]

# Classification prompt for IR pain detection
SIGNAL_CLASSIFICATION_PROMPT = """<role>
You are an Investor Relations signal analyst. Your job is to determine whether a news headline creates work for a company's IR team — the people who manage relationships with investors, analysts, and the capital markets.
</role>

<first_check>
BEFORE analyzing, check: does the headline involve any of these topics?
- Discrimination, DEI, EEOC, workplace bias, employment lawsuits, labor disputes, HR investigations
- Product launches, marketing campaigns, sponsorships, partnerships
- Customer service, product quality, recalls (unless SEC-reportable)

If YES → immediately classify as "neutral" with ir_pain_score 0.0. These are HR, legal, or operational matters that do not create IR team work, regardless of media attention or government involvement.

If NO → proceed with full analysis below.
</first_check>

<ir_relevance_criteria>
IR-relevant news directly affects a company's relationship with investors, analysts, or the capital markets. This includes:
- Stock price catalysts (earnings surprises, guidance changes, analyst actions)
- Ownership and governance changes (activist stakes, board shakeups, proxy fights)
- Capital structure events (offerings, buybacks, dividend changes, debt actions)
- Regulatory filings with market impact (8-K events, SEC inquiries, restatements)
- Competitive dynamics that analysts will ask about (peer M&A, market share shifts)
- Senior leadership changes that investors care about (CEO, CFO, IRO departures)

News that does NOT create IR team work (classify as "neutral", ir_pain_score 0.0):
- Employment discrimination claims, EEOC probes, DEI-related investigations, workplace lawsuits — these are HR/legal matters even when government agencies are involved or media coverage is heavy
- Product recalls or quality issues (unless material enough for an 8-K)
- Corporate culture, workplace environment, or diversity program stories
- Marketing campaigns, partnerships, sponsorships, or product launches
- Customer complaints or service issues
- Routine operational updates with no market impact

IMPORTANT: Do not confuse government employment investigations (EEOC, DOL, NLRB) with SEC or financial regulatory actions. An EEOC discrimination probe is an HR matter, not a governance issue. Only SEC enforcement, shareholder lawsuits, or proxy contests qualify as governance_issue.

When a headline falls outside IR relevance, classify as "neutral" with ir_pain_score 0.0.
</ir_relevance_criteria>

<input_data>
Company: {company_name}
Headline: {title}
Source: {source}
</input_data>

<signal_types>
- activist_risk: Ownership changes, 13-D filings, activist involvement
- analyst_negative: Downgrades, price target cuts, coverage drops
- earnings_miss: Missed estimates, guidance cuts, disappointing results
- leadership_change: New CEO, CFO, IRO, or major board changes
- governance_issue: Proxy fights, adverse proxy advisor recommendations
- esg_negative: ESG rating downgrades, sustainability controversies
- stock_pressure: Sharp stock drops, short interest spikes
- capital_stress: Failed offerings, credit downgrades, dividend cuts
- peer_pressure: Competitor outperformance, market share losses
- neutral: News that does not create IR team work
</signal_types>

<examples>
Example 1 — IR-relevant, high pain:
Headline: "Morgan Stanley downgrades Nike to Underweight, cuts PT to $65"
Output:
{{"summary": "Morgan Stanley downgraded Nike, cutting price target to $65. IR team faces investor inquiries and must prepare counter-narrative.", "signal_type": "analyst_negative", "relevance_score": 0.95, "ir_pain_score": 0.85}}

Example 2 — Not IR-relevant, neutral (government employment probe is HR, not governance):
Headline: "EEOC alleges anti-white discrimination at Nike, seeks court enforcement of subpoena"
Output:
{{"summary": "EEOC employment discrimination probe — this is an HR/legal matter, not a governance or capital markets event.", "signal_type": "neutral", "relevance_score": 0.9, "ir_pain_score": 0.0}}

Example 3 — Borderline, moderate pain:
Headline: "Nike CFO Matt Friend to step down effective April 2026"
Output:
{{"summary": "CFO departure creates IR workload: analyst calls, investor reassurance, and transition messaging.", "signal_type": "leadership_change", "relevance_score": 0.95, "ir_pain_score": 0.6}}
</examples>

<scoring_guide>
ir_pain_score reflects how much new work this creates for the IR team:
- 0.8-1.0: Acute — activist attack, major downgrade, CEO fired, earnings restatement
- 0.5-0.7: Moderate — earnings miss, analyst concern, CFO departure, ESG controversy with investor attention
- 0.2-0.4: Minor — routine negative coverage, peer outperformance
- 0.0: No IR work — internal HR matters, product issues, marketing news, operational updates

If the headline is not actually about {company_name}, set relevance_score below 0.3.
</scoring_guide>

Before responding, ask: "Would the IR team need to brief investors or analysts about this?" If no, set signal_type to "neutral" and ir_pain_score to 0.0. Employment disputes, EEOC probes, and DEI investigations are handled by HR and legal — the IR team does not brief investors on these.

Respond with ONLY this JSON (no other text):
{{
    "summary": "1-2 sentence summary focused on IR impact",
    "signal_type": "one of the signal types above",
    "relevance_score": 0.0-1.0,
    "ir_pain_score": 0.0-1.0
}}"""

# Talking points prompt for outreach openers (one per company, based on top signals)
TALKING_POINTS_PROMPT = """<role>
You are a senior IR services consultant drafting an outreach opener for a salesperson.
</role>

<task>
Write a single 1-2 sentence outreach opener for {company_name} based on their most pressing IR situation. Pick the single most compelling pain point from the signals below and reference it specifically.
</task>

<signals>
{signals_block}
</signals>

<style>
Write as a busy professional sending a quick note between meetings. Reference a specific IR-facing situation (stock impact, analyst sentiment, governance concern, leadership transition) rather than general company news. Keep it empathetic and low-pressure.
</style>

Return ONLY the talking point text, no quotes or labels."""

# Talking points settings
TALKING_POINTS_MIN_PAIN = 0.5  # Only generate for signals with pain >= this threshold

# Batch classification prompt (combines classification + talking point)
BATCH_CLASSIFICATION_PROMPT = """<role>
You are an Investor Relations signal analyst. Determine whether each headline creates work for {company_name}'s IR team — the people who manage relationships with investors, analysts, and the capital markets.
</role>

<first_check>
BEFORE analyzing each headline, check: does it involve any of these topics?
- Discrimination, DEI, EEOC, workplace bias, employment lawsuits, labor disputes, HR investigations
- Product launches, marketing campaigns, sponsorships, partnerships
- Customer service, product quality, recalls (unless SEC-reportable)

If YES → immediately classify as "neutral" with ir_pain_score 0.0. These are HR, legal, or operational matters that do not create IR team work, regardless of media attention or government involvement.

If NO → proceed with full analysis below.
</first_check>

<ir_relevance_criteria>
IR-relevant news directly affects investor/analyst relationships:
- Stock price catalysts, earnings surprises, guidance changes, analyst actions
- Ownership/governance changes, activist stakes, proxy fights
- Capital structure events, offerings, buybacks, dividend/debt changes
- Regulatory filings with market impact, SEC inquiries, restatements
- Competitive dynamics analysts will ask about, senior leadership changes

Classify as "neutral" with ir_pain_score 0.0 when news does not create IR work:
- Employment discrimination claims, EEOC probes, DEI investigations, workplace lawsuits — HR/legal matters even when government agencies are involved or media coverage is heavy
- Product recalls or quality issues (unless 8-K material)
- Corporate culture, workplace environment, diversity program stories
- Marketing, partnerships, sponsorships, product launches
- Customer complaints, routine operational updates

IMPORTANT: Do not confuse government employment investigations (EEOC, DOL, NLRB) with SEC or financial regulatory actions. An EEOC discrimination probe is an HR matter, not a governance issue. Only SEC enforcement, shareholder lawsuits, or proxy contests qualify as governance_issue.
</ir_relevance_criteria>

<input_data>
Company: {company_name}
Headlines to analyze:
{headlines_block}
</input_data>

<signal_types>
activist_risk | analyst_negative | earnings_miss | leadership_change | governance_issue | esg_negative | stock_pressure | capital_stress | peer_pressure | neutral
</signal_types>

<example>
Headline: "EEOC alleges anti-white discrimination at Company, seeks court enforcement of subpoena"
→ signal_type: "neutral", ir_pain_score: 0.0 (EEOC probe is an employment/HR matter, not governance)

Headline: "Goldman Sachs downgrades Company to Sell, cuts PT 20%"
→ signal_type: "analyst_negative", ir_pain_score: 0.85 (IR team must respond to investor inquiries)
</example>

<scoring>
0.8-1.0: Acute — activist attack, major downgrade, CEO fired, restatement
0.5-0.7: Moderate — earnings miss, CFO departure, ESG controversy with investor attention
0.2-0.4: Minor — routine negative coverage, peer outperformance
0.0: No IR work — internal HR, product issues, marketing, operational updates

If a headline is not actually about {company_name}, set relevance_score below 0.3.
</scoring>

Before responding, ask for each headline: "Would the IR team need to brief investors or analysts about this?" If no, set signal_type to "neutral" and ir_pain_score to 0.0. Employment disputes, EEOC probes, and DEI investigations are handled by HR and legal — the IR team does not brief investors on these.

Respond with ONLY this JSON:
{{
  "results": [
    {{
      "headline_index": 0,
      "summary": "1-2 sentence summary focused on IR impact",
      "signal_type": "type from above",
      "relevance_score": 0.0-1.0,
      "ir_pain_score": 0.0-1.0
    }}
  ]
}}
"""

# Earnings urgency settings
EARNINGS_URGENCY_DAYS = 14  # Boost urgency if earnings within this window

# Pipeline settings
MAX_ARTICLES_PER_COMPANY = 10  # Limit RSS results to reduce API calls
BATCH_CLASSIFICATION_SIZE = 8  # Articles per Claude API call
COMPANY_PARALLELISM = 5  # Concurrent company processing

# Dashboard settings
DEFAULT_RELEVANCE_THRESHOLD = 0.5
ARTICLES_PER_PAGE = 50

# Time window options for filtering signals
TIME_WINDOW_OPTIONS = [7, 14, 30]
DEFAULT_TIME_WINDOW = 7

# Urgency thresholds for outreach prioritization
# hot: high pain + recent signal, warm: moderate pain or recent, cold: otherwise
URGENCY_THRESHOLDS = {
    "hot": {"min_pain": 0.7, "max_hours": 48},
    "warm": {"min_pain": 0.5, "max_hours": 168},  # 7 days
}

# Urgency display settings
URGENCY_DISPLAY = {
    "hot": {"icon": "🔥", "label": "Call today", "color": "#dc3545"},
    "warm": {"icon": "🟡", "label": "Call this week", "color": "#fd7e14"},
    "cold": {"icon": "⚪", "label": "Monitor", "color": "#6c757d"},
}

# Database table names
TABLE_COMPANIES = "companies"
TABLE_ARTICLES = "articles"
TABLE_SIGNALS = "signals"
TABLE_FINANCIALS = "company_financials"

# Market cap tiers (in USD)
MARKET_CAP_TIERS = {
    "small": 2_000_000_000,    # < $2B
    "mid": 10_000_000_000,     # $2B - $10B
    "large": float('inf'),     # > $10B
}

# Price change display settings
PRICE_CHANGE_ICONS = {
    "up": "📈",
    "down": "📉",
    "flat": "➡️",
}

# Financials refresh interval (hours) - don't refresh more than once per day
FINANCIALS_REFRESH_HOURS = 24

# Outreach workflow settings
SNOOZE_DURATION_DAYS = 7
CONTACTED_HIDE_DAYS = 7

# Table name for outreach actions
TABLE_OUTREACH = "outreach_actions"

# Action types for outreach
OUTREACH_ACTION_TYPES = {
    "contacted": {"icon": "✅", "label": "Contacted"},
    "snoozed": {"icon": "😴", "label": "Snoozed"},
    "note": {"icon": "📝", "label": "Note"},
}
