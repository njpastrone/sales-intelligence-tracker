# db.py - Database operations (CRUD, queries)
# No external API calls or UI code here

import os
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client

import config

# Initialize Supabase client (singleton)
_client: Client = None

def get_client() -> Client:
    """Get cached Supabase client from environment/secrets."""
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(url, key)
    return _client


# --- Profiles ---

def create_profile(name: str) -> dict:
    """Create a new profile. Raises ValueError on duplicate name."""
    client = get_client()
    try:
        result = client.table(config.TABLE_PROFILES).insert({"name": name}).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise ValueError(f"Profile '{name}' already exists")
        raise


def get_profiles() -> list:
    """Get all profiles, ordered by name."""
    client = get_client()
    result = client.table(config.TABLE_PROFILES).select("*").order("name").execute()
    return result.data


def delete_profile(profile_id: str) -> dict:
    """Delete a profile. CASCADE removes junction links + profile-scoped outreach."""
    client = get_client()
    result = client.table(config.TABLE_PROFILES).delete().eq("id", profile_id).execute()
    return result.data[0] if result.data else None


# --- Profile-Company Junction ---

def link_company_to_profile(profile_id: str, company_id: str) -> dict:
    """Link a company to a profile. Ignores duplicates."""
    client = get_client()
    try:
        result = client.table(config.TABLE_PROFILE_COMPANIES).insert({
            "profile_id": profile_id,
            "company_id": company_id,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return None
        raise


def unlink_company_from_profile(profile_id: str, company_id: str) -> bool:
    """Remove a company from a profile. Returns True if removed."""
    client = get_client()
    result = client.table(config.TABLE_PROFILE_COMPANIES).delete().eq(
        "profile_id", profile_id
    ).eq("company_id", company_id).execute()
    return len(result.data) > 0


def get_profile_company_ids(profile_id: str) -> list:
    """Get list of company_id strings for a profile."""
    client = get_client()
    result = client.table(config.TABLE_PROFILE_COMPANIES).select(
        "company_id"
    ).eq("profile_id", profile_id).execute()
    return [row["company_id"] for row in result.data]


def is_company_orphaned(company_id: str) -> bool:
    """Check if a company has no profile links remaining."""
    client = get_client()
    result = client.table(config.TABLE_PROFILE_COMPANIES).select(
        "profile_id"
    ).eq("company_id", company_id).limit(1).execute()
    return len(result.data) == 0


# --- Companies ---

def add_company(name: str, ticker: str = None, aliases: list = None, profile_id: str = None) -> dict:
    """Add a company to the watchlist. If ticker exists and profile_id given, reuse existing company."""
    client = get_client()

    # Check for existing ticker
    if ticker:
        existing = get_company_by_ticker(ticker)
        if existing:
            if profile_id:
                # Reuse existing company — just create junction link
                link_company_to_profile(profile_id, existing["id"])
                return existing
            else:
                raise ValueError(f"Company with ticker '{ticker}' already exists")

    data = {
        "name": name,
        "ticker": ticker,
        "aliases": aliases or [name],
        "active": True,
    }
    result = client.table(config.TABLE_COMPANIES).insert(data).execute()
    company = result.data[0] if result.data else None

    if company and profile_id:
        link_company_to_profile(profile_id, company["id"])

    return company


def get_companies(active_only: bool = True, profile_id: str = None) -> list:
    """Get companies from watchlist, optionally filtered to a profile's territory."""
    client = get_client()

    if profile_id:
        company_ids = get_profile_company_ids(profile_id)
        if not company_ids:
            return []
        query = client.table(config.TABLE_COMPANIES).select("*").in_("id", company_ids)
        if active_only:
            query = query.eq("active", True)
        result = query.execute()
        return result.data

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


def delete_company(company_id: str, profile_id: str = None) -> dict:
    """Delete a company. If profile_id, unlink from profile and only delete if orphaned."""
    client = get_client()

    if profile_id:
        # Unlink from this profile
        unlink_company_from_profile(profile_id, company_id)
        # Delete profile-scoped outreach for this company
        client.table(config.TABLE_OUTREACH).delete().eq(
            "company_id", company_id
        ).eq("profile_id", profile_id).execute()
        # Only delete the company record if no other profiles reference it
        if not is_company_orphaned(company_id):
            return {"id": company_id}
        # Fall through to full delete if orphaned

    # Full delete: remove related data then company
    client.table(config.TABLE_SIGNALS).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_ARTICLES).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_FINANCIALS).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_OUTREACH).delete().eq("company_id", company_id).execute()
    client.table(config.TABLE_PROFILE_COMPANIES).delete().eq("company_id", company_id).execute()

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


def get_company_pain_summary(days: int = 7, profile_id: str = None) -> list:
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

    # If profile_id, get the profile's company IDs for filtering
    profile_company_ids = None
    if profile_id:
        profile_company_ids = set(get_profile_company_ids(profile_id))
        if not profile_company_ids:
            return []

    # Calculate cutoff date
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get signals within time window with only the fields the UI needs
    result = client.table(config.TABLE_SIGNALS).select(
        "id, company_id, summary, signal_type, relevance_score, sales_relevance, created_at, talking_point, articles(url, source), companies(name, ticker)"
    ).gte("relevance_score", 0.5).gte("created_at", cutoff.isoformat()).execute()

    # Group by company in Python
    company_data = {}
    now = datetime.now(timezone.utc)

    for signal in result.data:
        company_id = signal["company_id"]

        # Filter to profile's companies
        if profile_company_ids is not None and company_id not in profile_company_ids:
            continue

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


def get_company_financials(company_id: str = None, profile_id: str = None) -> list:
    """Get financials for one or all companies, optionally filtered by profile."""
    client = get_client()
    query = client.table(config.TABLE_FINANCIALS).select("*")
    if company_id:
        query = query.eq("company_id", company_id)
    elif profile_id:
        company_ids = get_profile_company_ids(profile_id)
        if not company_ids:
            return []
        query = query.in_("company_id", company_ids)
    result = query.execute()
    return result.data


def get_financials_needing_refresh(hours: int = 24, profile_id: str = None) -> list:
    """Get companies with tickers that have stale or missing financials."""
    client = get_client()

    # Get all companies with tickers (scoped to profile if given)
    if profile_id:
        company_ids = get_profile_company_ids(profile_id)
        if not company_ids:
            return []
        companies = client.table(config.TABLE_COMPANIES).select(
            "id, ticker"
        ).eq("active", True).in_("id", company_ids).execute()
    else:
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

def add_outreach_action(company_id: str, action_type: str, note: str = None, profile_id: str = None) -> dict:
    """Log an outreach action for a company, optionally scoped to a profile."""
    client = get_client()
    data = {
        "company_id": company_id,
        "action_type": action_type,
        "note": note,
    }
    if profile_id:
        data["profile_id"] = profile_id
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


def get_companies_to_hide(contacted_days: int = 7, snoozed_days: int = 7, profile_id: str = None) -> dict:
    """Get company IDs that should be hidden (recently contacted or snoozed).

    Returns:
        dict with 'contacted' and 'snoozed' sets of company IDs
    """
    client = get_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(contacted_days, snoozed_days))

    query = client.table(config.TABLE_OUTREACH).select(
        "company_id, action_type, created_at"
    ).in_("action_type", ["contacted", "snoozed"]).gte(
        "created_at", cutoff.isoformat()
    )
    if profile_id:
        query = query.eq("profile_id", profile_id)
    result = query.execute()

    contacted_ids = set()
    snoozed_ids = set()
    now = datetime.now(timezone.utc)

    for action in result.data:
        created = datetime.fromisoformat(action["created_at"].replace("Z", "+00:00"))
        age_days = (now - created).days

        if action["action_type"] == "contacted" and age_days < contacted_days:
            contacted_ids.add(action["company_id"])
        elif action["action_type"] == "snoozed" and age_days < snoozed_days:
            snoozed_ids.add(action["company_id"])

    return {"contacted": contacted_ids, "snoozed": snoozed_ids}


def delete_outreach_action(company_id: str, action_type: str, profile_id: str = None) -> bool:
    """Delete all outreach actions of given type for a company.

    Returns:
        True if any actions were deleted, False otherwise
    """
    client = get_client()

    query = client.table(config.TABLE_OUTREACH).delete().eq(
        "company_id", company_id
    ).eq("action_type", action_type)
    if profile_id:
        query = query.eq("profile_id", profile_id)
    result = query.execute()

    return len(result.data) > 0


def get_outreach_details(contacted_days: int = 7, snoozed_days: int = 7, profile_id: str = None) -> dict:
    """Get detailed outreach info for contacted/snoozed companies.

    Returns:
        dict with 'contacted' and 'snoozed' lists of dicts containing:
        - company_id, name, ticker, created_at (outreach timestamp)
    """
    client = get_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(contacted_days, snoozed_days))

    # Get outreach actions with company info
    query = client.table(config.TABLE_OUTREACH).select(
        "company_id, action_type, created_at, companies(name, ticker)"
    ).in_("action_type", ["contacted", "snoozed"]).gte(
        "created_at", cutoff.isoformat()
    ).order("created_at", desc=True)
    if profile_id:
        query = query.eq("profile_id", profile_id)
    result = query.execute()

    contacted = []
    snoozed = []
    now = datetime.now(timezone.utc)

    # Track seen company IDs to avoid duplicates (keep most recent)
    contacted_seen = set()
    snoozed_seen = set()

    for action in result.data:
        created = datetime.fromisoformat(action["created_at"].replace("Z", "+00:00"))
        age_days = (now - created).days
        company_id = action["company_id"]
        company = action.get("companies", {}) or {}

        detail = {
            "company_id": company_id,
            "name": company.get("name", "Unknown"),
            "ticker": company.get("ticker"),
            "created_at": action["created_at"],
        }

        if action["action_type"] == "contacted" and age_days < contacted_days:
            if company_id not in contacted_seen:
                contacted.append(detail)
                contacted_seen.add(company_id)
        elif action["action_type"] == "snoozed" and age_days < snoozed_days:
            if company_id not in snoozed_seen:
                snoozed.append(detail)
                snoozed_seen.add(company_id)

    return {"contacted": contacted, "snoozed": snoozed}
