# backend/main.py - FastAPI routes wrapping existing db.py and etl.py
# This provides REST API endpoints for the React frontend

import sys
import os

# Add parent directory to path to import existing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Load secrets from .streamlit/secrets.toml for local development
# (In production, use environment variables directly)
def load_streamlit_secrets():
    secrets_path = os.path.join(parent_dir, ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        for key, value in secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)

load_streamlit_secrets()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import db
import etl
import config

app = FastAPI(title="Sales Intelligence Tracker API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---

class CompanyCreate(BaseModel):
    name: str
    ticker: Optional[str] = None
    aliases: Optional[list[str]] = None


class OutreachCreate(BaseModel):
    company_id: str
    action_type: str
    note: Optional[str] = None


# --- Company Endpoints ---

@app.get("/api/companies")
def get_companies(active_only: bool = True):
    """Get all companies from watchlist."""
    return db.get_companies(active_only=active_only)


@app.post("/api/companies")
def add_company(company: CompanyCreate):
    """Add a company to the watchlist."""
    try:
        result = db.add_company(
            name=company.name,
            ticker=company.ticker,
            aliases=company.aliases,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/companies/summary")
def get_company_summary(days: int = 7):
    """Get company pain summary for outreach prioritization."""
    return db.get_company_pain_summary(days=days)


@app.delete("/api/companies/{company_id}")
def delete_company(company_id: str):
    """Delete a company and all related data."""
    result = db.delete_company(company_id)
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"deleted": True, "company_id": company_id}


# --- Financials Endpoints ---

@app.get("/api/financials")
def get_financials(company_id: Optional[str] = None):
    """Get financial data for companies."""
    return db.get_company_financials(company_id=company_id)


# --- Signals Endpoints ---

@app.get("/api/signals")
def get_signals(
    company_id: Optional[str] = None,
    min_relevance: float = 0.5,
    signal_type: Optional[str] = None,
    limit: int = 100,
):
    """Get signals with optional filters."""
    return db.get_signals(
        company_id=company_id,
        min_relevance=min_relevance,
        signal_type=signal_type,
        limit=limit,
    )


@app.get("/api/signals/hot")
def get_hot_signals(limit: int = 5):
    """Get top signals by sales relevance."""
    return db.get_hot_signals(limit=limit)


# --- Outreach Endpoints ---

@app.post("/api/outreach")
def add_outreach(outreach: OutreachCreate):
    """Log an outreach action for a company."""
    if outreach.action_type not in config.OUTREACH_ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_type. Must be one of: {list(config.OUTREACH_ACTION_TYPES.keys())}",
        )
    return db.add_outreach_action(
        company_id=outreach.company_id,
        action_type=outreach.action_type,
        note=outreach.note,
    )


# NOTE: /hidden must come BEFORE /{company_id} to avoid route conflict
@app.get("/api/outreach/hidden")
def get_hidden_companies(contacted_days: int = 7, snoozed_days: int = 7):
    """Get company IDs that should be hidden (recently contacted or snoozed)."""
    hidden = db.get_companies_to_hide(
        contacted_days=contacted_days,
        snoozed_days=snoozed_days,
    )
    return {"hidden_company_ids": list(hidden)}


@app.get("/api/outreach/{company_id}")
def get_outreach_actions(company_id: str, limit: int = 10):
    """Get recent outreach actions for a company."""
    return db.get_outreach_actions(company_id=company_id, limit=limit)


# --- Pipeline Endpoints ---

@app.post("/api/pipeline/run")
def run_pipeline():
    """Run the full ETL pipeline for all active companies."""
    result = etl.run_pipeline()
    return result


@app.post("/api/pipeline/financials")
def refresh_financials():
    """Refresh financial data for companies with stale data."""
    result = etl.refresh_financials()
    return result


@app.delete("/api/pipeline/clear")
def clear_data():
    """Clear all signals and articles (use with caution)."""
    result = db.clear_signals_and_articles()
    return result


# --- Config Endpoints ---

@app.get("/api/config/signal-types")
def get_signal_types():
    """Get available signal types with descriptions."""
    return config.SIGNAL_TYPES


@app.get("/api/config/urgency")
def get_urgency_config():
    """Get urgency thresholds and display settings."""
    return {
        "thresholds": config.URGENCY_THRESHOLDS,
        "display": config.URGENCY_DISPLAY,
    }


# --- Health Check ---

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
