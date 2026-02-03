# app.py - Streamlit UI only
# No business logic or API calls here

import os
from datetime import datetime, date

import streamlit as st
import pandas as pd

import db
import config

# Page config
st.set_page_config(
    page_title="Sales Intelligence Tracker",
    page_icon="📊",
    layout="wide",
)

# Load secrets into environment
try:
    for key in ["SUPABASE_URL", "SUPABASE_KEY", "ANTHROPIC_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except FileNotFoundError:
    pass  # No secrets file yet

st.title("📊 Sales Intelligence Tracker")

# Load companies once for reuse
try:
    companies = db.get_companies()
except Exception:
    companies = []

# Sidebar - Company management
with st.sidebar:
    st.header("Companies")

    # Add company form
    with st.form("add_company"):
        new_name = st.text_input("Company Name")
        new_ticker = st.text_input("Ticker (optional)")
        submitted = st.form_submit_button("Add Company")

        if submitted and new_name:
            try:
                db.add_company(new_name, new_ticker or None)
                st.success(f"Added {new_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # Company list
    st.subheader("Watchlist")
    if companies:
        for c in companies:
            ticker_str = f" ({c['ticker']})" if c.get('ticker') else ""
            st.write(f"• {c['name']}{ticker_str}")
    else:
        st.info("No companies yet. Add one above.")

    # ETL trigger
    st.divider()
    st.subheader("Fetch News")
    if st.button("🔄 Run Pipeline", disabled=len(companies) == 0):
        with st.spinner("Fetching news and classifying..."):
            try:
                import etl
                stats = etl.run_pipeline()
                st.success(
                    f"Done! Fetched {stats['articles_fetched']} articles, "
                    f"{stats['articles_new']} new, "
                    f"{stats['signals_created']} signals created."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline error: {e}")

    # Refresh financials
    st.divider()
    st.subheader("Financial Data")
    if st.button("📈 Refresh Financials", disabled=len(companies) == 0):
        with st.spinner("Fetching stock data..."):
            try:
                import etl
                stats = etl.refresh_financials()
                st.success(
                    f"Done! Refreshed {stats['companies_refreshed']} companies"
                    + (f", {stats['companies_failed']} failed" if stats['companies_failed'] > 0 else "")
                )
                st.rerun()
            except Exception as e:
                st.error(f"Refresh error: {e}")

    # Clear data
    st.divider()
    st.subheader("Data Management")
    if st.button("🗑️ Clear All Signals", type="secondary"):
        try:
            stats = db.clear_signals_and_articles()
            st.success(f"Cleared {stats['signals']} signals and {stats['articles']} articles.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


def compute_urgency(pain_score: float, age_hours: float) -> str:
    """Determine urgency level based on pain score and signal age."""
    hot = config.URGENCY_THRESHOLDS["hot"]
    warm = config.URGENCY_THRESHOLDS["warm"]

    if pain_score >= hot["min_pain"] and age_hours <= hot["max_hours"]:
        return "hot"
    elif pain_score >= warm["min_pain"] or age_hours <= warm["max_hours"]:
        return "warm"
    return "cold"


def compute_enhanced_urgency(pain_score: float, age_hours: float, next_earnings: str) -> str:
    """Determine urgency level with earnings proximity boost.

    If next_earnings is within EARNINGS_URGENCY_DAYS and base urgency is 'warm',
    boost to 'hot'.
    """
    base_urgency = compute_urgency(pain_score, age_hours)

    # Check earnings proximity for urgency boost
    if next_earnings:
        try:
            earnings_date = datetime.strptime(next_earnings, "%Y-%m-%d").date()
            days_to_earnings = (earnings_date - date.today()).days
            if 0 <= days_to_earnings <= config.EARNINGS_URGENCY_DAYS:
                if base_urgency == "warm":
                    return "hot"  # Boost warm to hot when earnings are imminent
        except (ValueError, TypeError):
            pass

    return base_urgency


def format_price_change(change: float) -> str:
    """Format price change with icon and color."""
    if change is None:
        return "N/A"
    if change > 0.001:
        icon = config.PRICE_CHANGE_ICONS["up"]
        return f"{icon} +{change:.1%}"
    elif change < -0.001:
        icon = config.PRICE_CHANGE_ICONS["down"]
        return f"{icon} {change:.1%}"
    else:
        icon = config.PRICE_CHANGE_ICONS["flat"]
        return f"{icon} {change:.1%}"


def format_market_cap_tier(tier: str) -> str:
    """Format market cap tier for display."""
    if tier == "large":
        return "Large Cap"
    elif tier == "mid":
        return "Mid Cap"
    elif tier == "small":
        return "Small Cap"
    return "N/A"


# Main area - Company Pain Dashboard
st.header("🎯 Outreach Priorities")

# Filters row
col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
with col1:
    time_window = st.selectbox(
        "Time Window",
        options=config.TIME_WINDOW_OPTIONS,
        index=config.TIME_WINDOW_OPTIONS.index(config.DEFAULT_TIME_WINDOW),
        format_func=lambda x: f"Last {x} days"
    )
with col2:
    hide_contacted = st.checkbox("Hide contacted", value=False)
with col3:
    hide_snoozed = st.checkbox("Hide snoozed", value=False)

# Load company pain summary
try:
    company_summaries = db.get_company_pain_summary(days=time_window)
except Exception as e:
    company_summaries = []
    st.warning(f"Could not load data: {e}")

# Get companies to hide based on filter settings
companies_to_hide = set()
if hide_contacted or hide_snoozed:
    companies_to_hide = db.get_companies_to_hide(
        contacted_days=config.CONTACTED_HIDE_DAYS if hide_contacted else 0,
        snoozed_days=config.SNOOZE_DURATION_DAYS if hide_snoozed else 0,
    )

# Filter out hidden companies
if companies_to_hide:
    company_summaries = [c for c in company_summaries if c["company_id"] not in companies_to_hide]

# Load financials for all companies
try:
    financials_list = db.get_company_financials()
    financials_lookup = {f["company_id"]: f for f in financials_list}
except Exception:
    financials_lookup = {}

if company_summaries:
    # Prepare data for CSV export
    export_rows = []

    for company in company_summaries:
        name = company["name"]
        ticker = company.get("ticker")
        company_id = company["company_id"]
        display_name = f"{name} ({ticker})" if ticker else name
        pain_score = company["max_pain_score"]
        pain_summary = company["max_pain_summary"]
        signal_count = company["signal_count"]
        age_hours = company["newest_signal_age_hours"]
        signals = company["signals"]

        # Get financials for this company
        fin = financials_lookup.get(company_id, {})
        price_change_7d = fin.get("price_change_7d")
        market_cap_tier = fin.get("market_cap_tier", "unknown")
        next_earnings = fin.get("next_earnings")

        # Format financial data
        stock_str = format_price_change(price_change_7d)
        cap_str = format_market_cap_tier(market_cap_tier)
        earnings_str = next_earnings if next_earnings else "-"

        # Compute enhanced urgency (considers earnings proximity)
        urgency = compute_enhanced_urgency(pain_score, age_hours, next_earnings)
        urgency_display = config.URGENCY_DISPLAY[urgency]

        # Find top talking point from highest pain signal
        top_talking_point = None
        for sig in sorted(signals, key=lambda s: s.get("sales_relevance", 0), reverse=True):
            if sig.get("talking_point"):
                top_talking_point = sig["talking_point"]
                break

        # Add to export
        export_rows.append({
            "Company": name,
            "Ticker": ticker or "",
            "Stock 7d": f"{price_change_7d:.1%}" if price_change_7d is not None else "N/A",
            "Market Cap": cap_str,
            "Next Earnings": earnings_str,
            "Pain Score": f"{pain_score:.0%}",
            "Top Signal": pain_summary,
            "Suggested Opener": top_talking_point or "",
            "Signal Count": signal_count,
            "Urgency": urgency_display["label"],
        })

        # Create expander for each company
        urgency_icon = urgency_display["icon"]

        # Build expander header with financial info
        header_parts = [
            f"{urgency_icon} **{display_name}**",
            f"{stock_str}" if ticker else "",
            f"{cap_str}" if market_cap_tier != "unknown" else "",
            f"Earnings: {earnings_str}" if next_earnings else "",
            f"{pain_score:.0%} pain",
            f"{signal_count} signals",
            urgency_display['label'],
        ]
        header = " | ".join(p for p in header_parts if p)

        with st.expander(header):
            # Financial summary row
            if ticker and fin:
                fin_col1, fin_col2, fin_col3 = st.columns(3)
                with fin_col1:
                    st.metric("Stock (7d)", stock_str)
                with fin_col2:
                    st.metric("Market Cap", cap_str)
                with fin_col3:
                    st.metric("Next Earnings", earnings_str)
                st.divider()

            # Show suggested opener if available
            if top_talking_point:
                st.markdown(f"💬 **Suggested opener:** *{top_talking_point}*")
                st.divider()

            # Show pain summary at top
            st.markdown(f"**Top pain signal:** {pain_summary}")
            st.divider()

            # Show all signals
            for signal in signals:
                signal_type = signal.get("signal_type", "neutral")
                icon = config.SIGNAL_ICONS.get(signal_type, "📰")
                signal_pain = signal.get("sales_relevance", 0.5)
                summary = signal.get("summary", "")
                article = signal.get("articles", {})
                source = article.get("source", "Unknown")
                url = article.get("url", "")
                published = article.get("published_at", "")[:10] if article.get("published_at") else ""

                # Signal row
                st.markdown(
                    f"{icon} **{signal_type}** ({signal_pain:.0%}) — {summary}"
                )
                if url:
                    st.caption(f"[{source}]({url}) • {published}")
                else:
                    st.caption(f"{source} • {published}")

            # Outreach actions section
            st.divider()
            btn_col1, btn_col2, btn_col3 = st.columns(3)

            with btn_col1:
                if st.button("✅ Contacted", key=f"contact_{company_id}"):
                    db.add_outreach_action(company_id, "contacted")
                    st.rerun()

            with btn_col2:
                if st.button("😴 Snooze", key=f"snooze_{company_id}"):
                    db.add_outreach_action(company_id, "snoozed")
                    st.rerun()

            with btn_col3:
                note_input = st.text_input(
                    "Note",
                    key=f"note_input_{company_id}",
                    label_visibility="collapsed",
                    placeholder="Add note..."
                )
                if st.button("📝 Add", key=f"note_{company_id}") and note_input:
                    db.add_outreach_action(company_id, "note", note_input)
                    st.rerun()

            # Show outreach history
            last_contact = db.get_last_contact(company_id)
            if last_contact:
                st.caption(f"✅ Last contacted: {last_contact['created_at'][:10]}")

            actions = db.get_outreach_actions(company_id)
            notes = [a for a in actions if a["action_type"] == "note" and a.get("note")]
            if notes:
                for n in notes[:3]:
                    st.caption(f"📝 {n['note']} ({n['created_at'][:10]})")

    # Export button
    st.divider()
    df = pd.DataFrame(export_rows)
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Export Company Summary to CSV",
        data=csv,
        file_name="company_outreach_priorities.csv",
        mime="text/csv",
    )
else:
    st.info("No signals found. Add companies and run the pipeline.")
