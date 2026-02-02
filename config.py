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

# Classification prompt for IR pain detection
SIGNAL_CLASSIFICATION_PROMPT = """You are helping salespeople identify when IR teams might need help.

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

Respond in JSON only (no other text):
{{
    "summary": "1-2 sentence summary of the signal",
    "signal_type": "one of the types above",
    "relevance_score": 0.0-1.0 (is this actually about {company_name}?),
    "ir_pain_score": 0.0-1.0 (how much pain is the IR team likely feeling?)
}}

IR pain scoring guide:
- 0.8-1.0: Acute pain (activist attack, major downgrade, CEO fired)
- 0.5-0.7: Moderate pain (earnings miss, analyst concern, ESG issue)
- 0.2-0.4: Minor pain (routine negative news, peer doing well)
- 0.0-0.2: No pain (neutral or positive news)

If the headline is not about {company_name}, set relevance_score below 0.3.
"""

# Pipeline settings
MAX_ARTICLES_PER_COMPANY = 10  # Limit RSS results to reduce API calls

# Dashboard settings
DEFAULT_RELEVANCE_THRESHOLD = 0.5
ARTICLES_PER_PAGE = 50

# Database table names
TABLE_COMPANIES = "companies"
TABLE_ARTICLES = "articles"
TABLE_SIGNALS = "signals"
