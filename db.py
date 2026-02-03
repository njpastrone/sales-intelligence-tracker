# db.py - Database operations (CRUD, queries)
# No external API calls or UI code here

import os
from datetime import datetime, timezone, timedelta
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


def delete_company(company_id: str) -> dict:
    """Delete a company and all related data (signals, articles, financials, outreach)."""
    client = get_client()

    # Delete related data first (foreign key constraints)
    client.table(config.TABLE_SIGNALS).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_ARTICLES).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_FINANCIALS).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_OUTREACH).delete().eq("company_id", company_id).execute()

    # Delete the company
    result = client.table(config.TABLE_COMPANIES).delete().eq("id", company_id).execute()
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

def add_signal(article_id: str, company_id: str, summary: str, relevance_score: float, signal_type: str = None, sales_relevance: float = 0.5, talking_point: str = None) -> dict:
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
    if talking_point:
        data["talking_point"] = talking_point
    result = client.table(config.TABLE_SIGNALS).insert(data).execute()
    return result.data[0] if result.data else None


def add_signals_batch(signals: list) -> list:
    """Add multiple signals in a single database call.

    Args:
        signals: List of dicts with keys: article_id, company_id, summary,
                 relevance_score, signal_type, sales_relevance, talking_point

    Returns:
        List of inserted signal records
    """
    if not signals:
        return []
    client = get_client()
    result = client.table(config.TABLE_SIGNALS).insert(signals).execute()
    return result.data


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


def get_company_pain_summary(days: int = 7) -> list:
    """Get company-level pain summary for outreach prioritization.

    Returns list of dicts with:
    - company_id, name, ticker
    - max_pain_score, max_pain_summary (highest pain signal)
    - signal_count
    - newest_signal_age_hours
    - signals (list of all signals)

    Sorted by max_pain_score descending.
    """
    client = get_client()

    # Calculate cutoff date
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get all signals within time window with company and article info
    result = client.table(config.TABLE_SIGNALS).select(
        "*, articles(*), companies(*)"
    ).gte("relevance_score", 0.5).gte("created_at", cutoff.isoformat()).execute()

    # Group by company in Python
    company_data = {}
    now = datetime.now(timezone.utc)

    for signal in result.data:
        company_id = signal["company_id"]
        company = signal.get("companies", {})

        if company_id not in company_data:
            company_data[company_id] = {
                "company_id": company_id,
                "name": company.get("name", "Unknown"),
                "ticker": company.get("ticker"),
                "max_pain_score": 0.0,
                "max_pain_summary": "",
                "signal_count": 0,
                "newest_signal_age_hours": float('inf'),
                "signals": [],
            }

        entry = company_data[company_id]
        pain_score = signal.get("sales_relevance", 0.5)

        # Update max pain
        if pain_score > entry["max_pain_score"]:
            entry["max_pain_score"] = pain_score
            entry["max_pain_summary"] = signal.get("summary", "")

        # Update signal count
        entry["signal_count"] += 1

        # Calculate signal age in hours
        created_at_str = signal.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                age_hours = (now - created_at).total_seconds() / 3600
                if age_hours < entry["newest_signal_age_hours"]:
                    entry["newest_signal_age_hours"] = age_hours
            except (ValueError, TypeError):
                pass

        # Add to signals list
        entry["signals"].append(signal)

    # Convert to list and sort by max_pain_score descending
    companies = list(company_data.values())
    companies.sort(key=lambda x: x["max_pain_score"], reverse=True)

    return companies


# --- Company Financials ---

def upsert_company_financials(company_id: str, data: dict) -> dict:
    """Insert or update financial data for a company."""
    client = get_client()
    record = {
        "company_id": company_id,
        "price_change_7d": data.get("price_change_7d"),
        "price_change_30d": data.get("price_change_30d"),
        "market_cap": data.get("market_cap"),
        "market_cap_tier": data.get("market_cap_tier"),
        "last_earnings": data.get("last_earnings"),
        "next_earnings": data.get("next_earnings"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = client.table(config.TABLE_FINANCIALS).upsert(record).execute()
    return result.data[0] if result.data else None


def get_company_financials(company_id: str = None) -> list:
    """Get financials for one or all companies."""
    client = get_client()
    query = client.table(config.TABLE_FINANCIALS).select("*")
    if company_id:
        query = query.eq("company_id", company_id)
    result = query.execute()
    return result.data


def get_financials_needing_refresh(hours: int = 24) -> list:
    """Get companies with tickers that have stale or missing financials."""
    client = get_client()

    # Get all companies with tickers
    companies = client.table(config.TABLE_COMPANIES).select("id, ticker").eq("active", True).execute()
    companies_with_tickers = [c for c in companies.data if c.get("ticker")]

    if not companies_with_tickers:
        return []

    # Get existing financials
    company_ids = [c["id"] for c in companies_with_tickers]
    financials = client.table(config.TABLE_FINANCIALS).select("company_id, updated_at").in_("company_id", company_ids).execute()

    # Build lookup of last update times
    fin_lookup = {f["company_id"]: f["updated_at"] for f in financials.data}

    # Find companies needing refresh
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    needs_refresh = []

    for company in companies_with_tickers:
        updated_at = fin_lookup.get(company["id"])
        if not updated_at:
            # No financials record yet
            needs_refresh.append(company)
        else:
            try:
                last_update = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if last_update < cutoff:
                    needs_refresh.append(company)
            except (ValueError, TypeError):
                needs_refresh.append(company)

    return needs_refresh


# --- Outreach Actions ---

def add_outreach_action(company_id: str, action_type: str, note: str = None) -> dict:
    """Log an outreach action for a company."""
    client = get_client()
    data = {
        "company_id": company_id,
        "action_type": action_type,
        "note": note,
    }
    result = client.table(config.TABLE_OUTREACH).insert(data).execute()
    return result.data[0] if result.data else None


def get_outreach_actions(company_id: str, limit: int = 10) -> list:
    """Get recent outreach actions for a company."""
    client = get_client()
    result = client.table(config.TABLE_OUTREACH).select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).limit(limit).execute()
    return result.data


def get_last_contact(company_id: str) -> dict:
    """Get most recent 'contacted' action for a company."""
    client = get_client()
    result = client.table(config.TABLE_OUTREACH).select("*").eq(
        "company_id", company_id
    ).eq("action_type", "contacted").order("created_at", desc=True).limit(1).execute()
    return result.data[0] if result.data else None


def get_companies_to_hide(contacted_days: int = 7, snoozed_days: int = 7) -> set:
    """Get company IDs that should be hidden (recently contacted or snoozed)."""
    client = get_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(contacted_days, snoozed_days))

    result = client.table(config.TABLE_OUTREACH).select(
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
