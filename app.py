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

# Main area - Signals
st.header("Recent Signals")

# Filters
col1, col2 = st.columns(2)
with col1:
    company_options = ["All"] + [c["name"] for c in companies]
    selected_company = st.selectbox("Filter by Company", company_options)

with col2:
    min_relevance = st.slider("Minimum Relevance", 0.0, 1.0, config.DEFAULT_RELEVANCE_THRESHOLD)

# Load signals
try:
    company_id = None
    if selected_company != "All":
        for c in companies:
            if c["name"] == selected_company:
                company_id = c["id"]
                break

    signals = db.get_signals(company_id=company_id, min_relevance=min_relevance)

    if signals:
        # Display as table
        rows = []
        for s in signals:
            rows.append({
                "Company": s["companies"]["name"] if s.get("companies") else "",
                "Date": s["articles"]["published_at"][:10] if s.get("articles", {}).get("published_at") else "",
                "Headline": s["articles"]["title"] if s.get("articles") else "",
                "Summary": s["summary"],
                "Score": f"{s['relevance_score']:.2f}",
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
