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


# --- Signals ---

def add_signal(article_id: str, company_id: str, summary: str, relevance_score: float, signal_type: str = None) -> dict:
    """Add a signal for an article."""
    client = get_client()
    data = {
        "article_id": article_id,
        "company_id": company_id,
        "summary": summary,
        "relevance_score": relevance_score,
        "signal_type": signal_type,
    }
    result = client.table(config.TABLE_SIGNALS).insert(data).execute()
    return result.data[0] if result.data else None


def get_signals(company_id: str = None, min_relevance: float = 0.5, limit: int = 100) -> list:
    """Get signals with optional filters."""
    client = get_client()
    query = client.table(config.TABLE_SIGNALS).select(
        "*, articles(*), companies(*)"
    ).gte("relevance_score", min_relevance).order("created_at", desc=True).limit(limit)

    if company_id:
        query = query.eq("company_id", company_id)

    result = query.execute()
    return result.data
