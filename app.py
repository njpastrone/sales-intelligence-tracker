# app.py - Streamlit UI only
# No business logic or API calls here

import os
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

# Main area - IR Teams in Pain
try:
    hot_signals = db.get_hot_signals(limit=5)
except Exception:
    hot_signals = []

st.header("🎯 IR Teams in Pain")
st.caption("Top outreach opportunities ranked by IR pain score")

if hot_signals:
    for s in hot_signals:
        signal_type = s.get("signal_type", "neutral")
        icon = config.SIGNAL_ICONS.get(signal_type, "📰")
        company_name = s["companies"]["name"] if s.get("companies") else "Unknown"
        pain_score = s.get("sales_relevance", 0.5)

        # Color based on pain score - red for high pain
        if pain_score >= 0.7:
            border_color = "#dc3545"  # Red - high pain
        elif pain_score >= 0.5:
            border_color = "#fd7e14"  # Orange - moderate pain
        else:
            border_color = "#6c757d"  # Gray - low pain

        st.markdown(
            f"""<div style="padding: 10px; margin: 5px 0; border-left: 4px solid {border_color}; background: #f8f9fa; border-radius: 4px;">
            <strong>{icon} {company_name}</strong>: {s['summary']}
            <span style="color: #666; font-size: 0.9em;">— {signal_type} ({pain_score:.0%} pain)</span>
            </div>""",
            unsafe_allow_html=True
        )
else:
    st.info("No pain signals yet. Add companies and run the pipeline.")

# Company Overview section
st.header("📋 Company Overview")

try:
    company_summaries = db.get_company_signal_summary()
except Exception:
    company_summaries = []

if company_summaries:
    # Create columns for company cards (max 4 per row)
    cols_per_row = 4
    for i in range(0, len(company_summaries), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, summary in enumerate(company_summaries[i:i+cols_per_row]):
            with cols[j]:
                st.markdown(f"**{summary['name']}**")
                st.caption(f"{summary['total']} signals")

                # Show signal type breakdown with icons
                type_icons = []
                for signal_type, count in summary["by_type"].items():
                    icon = config.SIGNAL_ICONS.get(signal_type, "📰")
                    type_icons.append(f"{icon}{count}")

                if type_icons:
                    st.write(" ".join(type_icons))
else:
    st.info("No company data yet.")

# Main area - All Signals
st.header("📰 All Signals")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    company_options = ["All"] + [c["name"] for c in companies]
    selected_company = st.selectbox("Filter by Company", company_options)

with col2:
    signal_type_options = ["All"] + list(config.SIGNAL_TYPES.keys())
    selected_signal_type = st.selectbox("Filter by Signal Type", signal_type_options)

with col3:
    min_relevance = st.slider("Minimum Relevance", 0.0, 1.0, config.DEFAULT_RELEVANCE_THRESHOLD)

# Load signals
try:
    company_id = None
    if selected_company != "All":
        for c in companies:
            if c["name"] == selected_company:
                company_id = c["id"]
                break

    signal_type_filter = None if selected_signal_type == "All" else selected_signal_type

    signals = db.get_signals(
        company_id=company_id,
        min_relevance=min_relevance,
        signal_type=signal_type_filter
    )

    if signals:
        # Display as table
        rows = []
        for s in signals:
            signal_type = s.get("signal_type", "neutral")
            icon = config.SIGNAL_ICONS.get(signal_type, "📰")
            pain_score = s.get("sales_relevance", 0.5)

            rows.append({
                "Type": f"{icon} {signal_type}",
                "Company": s["companies"]["name"] if s.get("companies") else "",
                "Date": s["articles"]["published_at"][:10] if s.get("articles", {}).get("published_at") else "",
                "Summary": s["summary"],
                "Relevance": f"{s['relevance_score']:.0%}",
                "Pain": f"{pain_score:.0%}",
                "Source": s["articles"]["source"] if s.get("articles") else "",
                "URL": s["articles"]["url"] if s.get("articles") else "",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name="signals_export.csv",
            mime="text/csv",
        )
    else:
        st.info("No signals found. Add companies and run the pipeline.")

except Exception as e:
    st.warning(f"Could not load signals: {e}")
    st.info("Make sure database is configured and tables exist.")
