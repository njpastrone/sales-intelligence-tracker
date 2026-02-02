# db.py - Database operations (CRUD, queries)
# No external API calls or UI code here

import os
from datetime import datetime, timezone
from supabase import create_client, Client

import config

# Initialize Supabase client
def get_client() -> Client:
    """Get Supabase client from environment/secrets."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


# --- Companies ---

def add_company(name: str, ticker: str = None, aliases: list = None) -> dict:
    """Add a company to the watchlist. Raises ValueError if ticker already exists."""
    client = get_client()

    # Check for duplicate ticker
    if ticker:
        existing = get_company_by_ticker(ticker)
        if existing:
            raise ValueError(f"Company with ticker '{ticker}' already exists")

    data = {
        "name": name,
        "ticker": ticker,
        "aliases": aliases or [name],
        "active": True,
    }
    result = client.table(config.TABLE_COMPANIES).insert(data).execute()
    return result.data[0] if result.data else None


def get_companies(active_only: bool = True) -> list:
    """Get all companies from watchlist."""
    client = get_client()
    query = client.table(config.TABLE_COMPANIES).select("*")
    if active_only:
        query = query.eq("active", True)
    result = query.execute()
    return result.data


def get_company_by_ticker(ticker: str) -> dict:
    """Get a company by ticker symbol."""
    client = get_client()
    result = client.table(config.TABLE_COMPANIES).select("*").eq("ticker", ticker).execute()
    return result.data[0] if result.data else None


# --- Articles ---

def add_article(company_id: str, title: str, url: str, source: str, published_at: datetime) -> dict:
    """Add an article. Returns None if URL already exists (dedup)."""
    client = get_client()
    data = {
        "company_id": company_id,
        "title": title,
        "url": url,
        "source": source,
        "published_at": published_at.isoformat() if published_at else None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = client.table(config.TABLE_ARTICLES).insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        # URL unique constraint violation = duplicate
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return None
        raise


def article_exists(url: str) -> bool:
    """Check if article URL already exists."""
    client = get_client()
    result = client.table(config.TABLE_ARTICLES).select("id").eq("url", url).execute()
    return len(result.data) > 0


def get_existing_urls(urls: list) -> set:
    """Batch check which URLs already exist. Returns set of existing URLs."""
    if not urls:
        return set()
    client = get_client()
    result = client.table(config.TABLE_ARTICLES).select("url").in_("url", urls).execute()
    return {row["url"] for row in result.data}


# --- Signals ---

def add_signal(article_id: str, company_id: str, summary: str, relevance_score: float, signal_type: str = None, sales_relevance: float = 0.5) -> dict:
    """Add a signal for an article."""
    client = get_client()
    data = {
        "article_id": article_id,
        "company_id": company_id,
        "summary": summary,
        "relevance_score": relevance_score,
        "signal_type": signal_type,
        "sales_relevance": sales_relevance,
    }
    result = client.table(config.TABLE_SIGNALS).insert(data).execute()
    return result.data[0] if result.data else None


def clear_signals_and_articles() -> dict:
    """Delete all signals and articles. Returns counts of deleted rows."""
    client = get_client()
    # Delete signals first (foreign key dependency)
    signals = client.table(config.TABLE_SIGNALS).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    articles = client.table(config.TABLE_ARTICLES).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    return {"signals": len(signals.data), "articles": len(articles.data)}


def get_signals(company_id: str = None, min_relevance: float = 0.5, signal_type: str = None, limit: int = 100) -> list:
    """Get signals with optional filters."""
    client = get_client()
    query = client.table(config.TABLE_SIGNALS).select(
        "*, articles(*), companies(*)"
    ).gte("relevance_score", min_relevance).order("created_at", desc=True).limit(limit)

    if company_id:
        query = query.eq("company_id", company_id)

    if signal_type:
        query = query.eq("signal_type", signal_type)

    result = query.execute()
    return result.data


def get_hot_signals(limit: int = 5) -> list:
    """Get top signals by sales_relevance."""
    client = get_client()
    result = client.table(config.TABLE_SIGNALS).select(
        "*, articles(*), companies(*)"
    ).gte("relevance_score", 0.5).order("sales_relevance", desc=True).limit(limit).execute()
    return result.data


def get_company_signal_summary() -> list:
    """Get signal counts by type for each company."""
    client = get_client()
    # Get all signals with company info
    result = client.table(config.TABLE_SIGNALS).select(
        "company_id, signal_type, companies(name)"
    ).gte("relevance_score", 0.5).execute()

    # Aggregate in Python (Supabase free tier doesn't support GROUP BY well)
    company_stats = {}
    for row in result.data:
        company_id = row["company_id"]
        company_name = row["companies"]["name"] if row.get("companies") else "Unknown"
        signal_type = row.get("signal_type", "general")

        if company_id not in company_stats:
            company_stats[company_id] = {"name": company_name, "total": 0, "by_type": {}}

        company_stats[company_id]["total"] += 1
        company_stats[company_id]["by_type"][signal_type] = company_stats[company_id]["by_type"].get(signal_type, 0) + 1

    return list(company_stats.values())
