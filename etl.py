# etl.py - Data pipeline: fetch, classify, transform
# Uses db module for storage, no raw SQL or UI code here

import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import httpx
import anthropic
import yfinance as yf

import config


def fetch_news_rss(company_name: str, ticker: str = None) -> list:
    """Fetch news articles from Google News RSS for a company.

    Returns list of dicts with: title, url, source, published_at
    """
    # Build search query - use ticker if available for better precision
    if ticker:
        query = f'"{company_name}" OR "{ticker}"'
    else:
        query = f'"{company_name}"'

    url = config.GOOGLE_NEWS_RSS_URL.format(query=quote_plus(query))

    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    articles = []
    root = ET.fromstring(response.content)

    for item in root.findall(".//item"):
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        source = item.find("source").text if item.find("source") is not None else ""
        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""

        # Parse date (format: "Mon, 01 Jan 2024 12:00:00 GMT")
        published_at = None
        if pub_date:
            try:
                published_at = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                pass

        articles.append({
            "title": title,
            "url": link,
            "source": source,
            "published_at": published_at,
        })

    return articles[:config.MAX_ARTICLES_PER_COMPANY]


def title_mentions_company(title: str, company_name: str, ticker: str = None) -> bool:
    """Quick check if title mentions the company - skip obvious irrelevant articles."""
    title_lower = title.lower()
    # Check company name (first word at minimum, e.g., "Apple" from "Apple Inc")
    name_parts = company_name.lower().split()
    if name_parts[0] in title_lower:
        return True
    # Check ticker
    if ticker and ticker.upper() in title.upper():
        return True
    return False


def generate_talking_point(signal_type: str, summary: str, company_name: str) -> str:
    """Generate a personalized talking point for outreach using Claude Haiku.

    Args:
        signal_type: Type of pain signal (e.g., 'analyst_negative')
        summary: Summary of the signal
        company_name: Name of the company

    Returns:
        A 1-2 sentence outreach opener string
    """
    client = anthropic.Anthropic()

    prompt = config.TALKING_POINTS_PROMPT.format(
        company_name=company_name,
        signal_type=signal_type,
        summary=summary,
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=150,  # Short response expected
        temperature=config.CLAUDE_TEMPERATURE,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()


def classify_article(title: str, source: str, company_name: str) -> dict:
    """Use Claude Haiku to classify an article and generate summary.

    Returns dict with: summary, relevance_score, signal_type, sales_relevance (ir_pain_score)
    """
    client = anthropic.Anthropic()

    prompt = config.SIGNAL_CLASSIFICATION_PROMPT.format(
        company_name=company_name,
        title=title,
        source=source,
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.CLAUDE_MAX_TOKENS,
        temperature=config.CLAUDE_TEMPERATURE,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    # Parse JSON from response
    result = None
    try:
        # First try: parse the whole response as JSON
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Second try: strip markdown code blocks and parse
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            # Remove ```json and ``` markers
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: extract values manually
            result = {
                "summary": response_text[:200],
                "relevance_score": 0.5,
                "signal_type": "neutral",
                "ir_pain_score": 0.5,
            }

    # Validate signal_type is a known type
    signal_type = result.get("signal_type", "neutral")
    if signal_type not in config.SIGNAL_TYPES:
        signal_type = "neutral"

    # Use ir_pain_score for sales_relevance column (no schema change needed)
    ir_pain_score = result.get("ir_pain_score", result.get("sales_relevance", 0.5))

    return {
        "summary": result.get("summary", ""),
        "relevance_score": float(result.get("relevance_score", 0.5)),
        "signal_type": signal_type,
        "sales_relevance": float(ir_pain_score),
    }


def process_company(company: dict) -> dict:
    """Fetch and classify news for a single company.

    Args:
        company: dict with id, name, ticker, aliases

    Returns:
        dict with: articles_fetched, articles_new, signals_created
    """
    import db  # Import here to avoid circular dependency

    stats = {"articles_fetched": 0, "articles_new": 0, "signals_created": 0}

    # Fetch news
    articles = fetch_news_rss(company["name"], company.get("ticker"))
    stats["articles_fetched"] = len(articles)

    # Batch check which URLs already exist (single DB call)
    all_urls = [a["url"] for a in articles]
    existing_urls = db.get_existing_urls(all_urls)

    for article in articles:
        # Skip if already processed
        if article["url"] in existing_urls:
            continue

        # Skip if title doesn't mention the company (avoid irrelevant articles)
        if not title_mentions_company(article["title"], company["name"], company.get("ticker")):
            continue

        # Add article to database
        db_article = db.add_article(
            company_id=company["id"],
            title=article["title"],
            url=article["url"],
            source=article["source"],
            published_at=article["published_at"],
        )

        if not db_article:
            continue

        stats["articles_new"] += 1

        # Classify with Claude
        try:
            classification = classify_article(
                title=article["title"],
                source=article["source"],
                company_name=company["name"],
            )

            # Generate talking point for high-pain signals
            talking_point = None
            if classification["sales_relevance"] >= config.TALKING_POINTS_MIN_PAIN:
                try:
                    talking_point = generate_talking_point(
                        signal_type=classification["signal_type"],
                        summary=classification["summary"],
                        company_name=company["name"],
                    )
                except Exception:
                    # Continue without talking point if generation fails
                    pass

            # Save signal
            db.add_signal(
                article_id=db_article["id"],
                company_id=company["id"],
                summary=classification["summary"],
                relevance_score=classification["relevance_score"],
                signal_type=classification["signal_type"],
                sales_relevance=classification["sales_relevance"],
                talking_point=talking_point,
            )
            stats["signals_created"] += 1
        except Exception:
            # Skip this article if classification fails, continue with others
            continue

    return stats


def run_pipeline() -> dict:
    """Run full ETL pipeline for all active companies.

    Returns:
        dict with total stats
    """
    import db  # Import here to avoid circular dependency

    companies = db.get_companies(active_only=True)

    totals = {"companies": len(companies), "articles_fetched": 0, "articles_new": 0, "signals_created": 0}

    for company in companies:
        stats = process_company(company)
        totals["articles_fetched"] += stats["articles_fetched"]
        totals["articles_new"] += stats["articles_new"]
        totals["signals_created"] += stats["signals_created"]

    return totals


def get_market_cap_tier(market_cap: int) -> str:
    """Determine market cap tier based on value."""
    if market_cap is None:
        return "unknown"
    if market_cap < config.MARKET_CAP_TIERS["small"]:
        return "small"
    elif market_cap < config.MARKET_CAP_TIERS["mid"]:
        return "mid"
    else:
        return "large"


def fetch_company_financials(ticker: str) -> dict:
    """Fetch financial data from yfinance.

    Returns dict with:
    - price_change_7d, price_change_30d (percentage as decimal, e.g., 0.05 = 5%)
    - market_cap (integer)
    - market_cap_tier ('small', 'mid', 'large', 'unknown')
    - last_earnings, next_earnings (ISO date string or None)
    """
    result = {
        "price_change_7d": None,
        "price_change_30d": None,
        "market_cap": None,
        "market_cap_tier": "unknown",
        "last_earnings": None,
        "next_earnings": None,
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Market cap
        market_cap = info.get("marketCap")
        if market_cap:
            result["market_cap"] = int(market_cap)
            result["market_cap_tier"] = get_market_cap_tier(market_cap)

        # Price changes - calculate from history
        try:
            hist = stock.history(period="1mo")
            if len(hist) >= 2:
                current_price = hist["Close"].iloc[-1]

                # 7-day change
                if len(hist) >= 5:  # ~5 trading days in a week
                    price_7d_ago = hist["Close"].iloc[-5]
                    result["price_change_7d"] = (current_price - price_7d_ago) / price_7d_ago

                # 30-day change (full history)
                price_30d_ago = hist["Close"].iloc[0]
                result["price_change_30d"] = (current_price - price_30d_ago) / price_30d_ago
        except Exception:
            pass

        # Earnings dates
        try:
            calendar = stock.calendar
            # calendar can be a DataFrame or dict depending on yfinance version
            if calendar is not None:
                if hasattr(calendar, "get"):
                    # Dict format (newer yfinance)
                    earnings_date = calendar.get("Earnings Date")
                    if earnings_date:
                        if isinstance(earnings_date, list) and len(earnings_date) > 0:
                            result["next_earnings"] = earnings_date[0].strftime("%Y-%m-%d")
                elif hasattr(calendar, "empty") and not calendar.empty:
                    # DataFrame format (older yfinance)
                    if "Earnings Date" in calendar.columns:
                        dates = calendar["Earnings Date"].dropna()
                        if len(dates) > 0:
                            result["next_earnings"] = dates.iloc[0].strftime("%Y-%m-%d")
        except Exception:
            pass

        # Try to get last earnings from earnings history
        try:
            earnings_hist = stock.earnings_dates
            if earnings_hist is not None and len(earnings_hist) > 0:
                past_dates = earnings_hist[earnings_hist.index <= datetime.now()]
                if len(past_dates) > 0:
                    result["last_earnings"] = past_dates.index[0].strftime("%Y-%m-%d")
        except Exception:
            pass

    except Exception:
        # Return defaults if ticker not found or API fails
        pass

    return result


def refresh_financials() -> dict:
    """Refresh financial data for companies with stale or missing data.

    Returns:
        dict with stats: companies_refreshed, companies_failed
    """
    import db  # Import here to avoid circular dependency

    stats = {"companies_refreshed": 0, "companies_failed": 0}

    # Get companies needing refresh
    companies = db.get_financials_needing_refresh(hours=config.FINANCIALS_REFRESH_HOURS)

    for company in companies:
        ticker = company.get("ticker")
        if not ticker:
            continue

        try:
            financials = fetch_company_financials(ticker)
            db.upsert_company_financials(company["id"], financials)
            stats["companies_refreshed"] += 1
        except Exception:
            stats["companies_failed"] += 1

    return stats
