# config.py - Constants, settings, and prompts
# No logic or side effects here

# Google News RSS
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

# Claude settings
CLAUDE_MODEL = "claude-3-5-haiku-20241022"
CLAUDE_MAX_TOKENS = 500
CLAUDE_TEMPERATURE = 0.1

# Classification prompt
SIGNAL_CLASSIFICATION_PROMPT = """Analyze this news article about {company_name} and extract key information.

Article Title: {title}
Source: {source}

Respond in JSON format:
{{
    "summary": "1-2 sentence summary of the news event",
    "relevance_score": 0.0-1.0 (how confident this is actually about {company_name}, not a different company or topic),
    "signal_type": "general"
}}

If the article is not relevant to {company_name}, set relevance_score below 0.3.
"""

# Dashboard settings
DEFAULT_RELEVANCE_THRESHOLD = 0.5
ARTICLES_PER_PAGE = 50

# Database table names
TABLE_COMPANIES = "companies"
TABLE_ARTICLES = "articles"
TABLE_SIGNALS = "signals"
