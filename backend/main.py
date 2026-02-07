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
    profile_id: Optional[str] = None


class OutreachCreate(BaseModel):
    company_id: str
    action_type: str
    note: Optional[str] = None
    profile_id: Optional[str] = None


class ProfileCreate(BaseModel):
    name: str


# --- Profile Endpoints ---

@app.get("/api/profiles")
def get_profiles():
    """Get all profiles."""
    return db.get_profiles()


@app.post("/api/profiles")
def create_profile(profile: ProfileCreate):
    """Create a new profile."""
    try:
        return db.create_profile(name=profile.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: str):
    """Delete a profile and its junction links."""
    result = db.delete_profile(profile_id)
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"deleted": True, "profile_id": profile_id}


# --- Company Endpoints ---

@app.get("/api/companies")
def get_companies(active_only: bool = True, profile_id: Optional[str] = None):
    """Get all companies from watchlist."""
    return db.get_companies(active_only=active_only, profile_id=profile_id)


@app.post("/api/companies")
def add_company(company: CompanyCreate):
    """Add a company to the watchlist and fetch initial financials."""
    try:
        result = db.add_company(
            name=company.name,
            ticker=company.ticker,
            aliases=company.aliases,
            profile_id=company.profile_id,
        )

        # Automatically fetch financials if ticker is provided
        if company.ticker:
            try:
                financials = etl.fetch_company_financials(company.ticker)
                db.upsert_company_financials(result["id"], financials)
            except Exception:
                # Don't fail the company add if financials fetch fails
                pass

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/companies/summary")
def get_company_summary(days: int = 7, profile_id: Optional[str] = None):
    """Get company pain summary for outreach prioritization."""
    return db.get_company_pain_summary(days=days, profile_id=profile_id)


@app.get("/api/init")
def get_init_data(days: int = 7, contacted_days: int = 7, snoozed_days: int = 7, profile_id: Optional[str] = None):
    """Combined initial load endpoint - returns all data needed for first render."""
    summary = db.get_company_pain_summary(days=days, profile_id=profile_id)
    financials = db.get_company_financials(profile_id=profile_id)
    outreach = db.get_outreach_details(
        contacted_days=contacted_days,
        snoozed_days=snoozed_days,
        profile_id=profile_id,
    )
    return {
        "summary": summary,
        "financials": financials,
        "outreach": {
            "contacted": outreach["contacted"],
            "snoozed": outreach["snoozed"],
        },
    }


@app.delete("/api/companies/{company_id}")
def delete_company(company_id: str, profile_id: Optional[str] = None):
    """Delete a company and all related data."""
    result = db.delete_company(company_id, profile_id=profile_id)
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"deleted": True, "company_id": company_id}


# --- Financials Endpoints ---

@app.get("/api/financials")
def get_financials(company_id: Optional[str] = None, profile_id: Optional[str] = None):
    """Get financial data for companies."""
    return db.get_company_financials(company_id=company_id, profile_id=profile_id)


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
        profile_id=outreach.profile_id,
    )


# NOTE: /hidden must come BEFORE /{company_id} to avoid route conflict
@app.get("/api/outreach/hidden")
def get_hidden_companies(contacted_days: int = 7, snoozed_days: int = 7, profile_id: Optional[str] = None):
    """Get detailed info for hidden companies (recently contacted or snoozed)."""
    result = db.get_outreach_details(
        contacted_days=contacted_days,
        snoozed_days=snoozed_days,
        profile_id=profile_id,
    )
    return {
        "contacted": result["contacted"],
        "snoozed": result["snoozed"],
    }


@app.delete("/api/outreach/{company_id}/{action_type}")
def delete_outreach_action(company_id: str, action_type: str, profile_id: Optional[str] = None):
    """Delete the most recent outreach action of given type for a company."""
    if action_type not in config.OUTREACH_ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_type. Must be one of: {list(config.OUTREACH_ACTION_TYPES.keys())}",
        )
    deleted = db.delete_outreach_action(company_id, action_type, profile_id=profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No action found to delete")
    return {"deleted": True, "company_id": company_id, "action_type": action_type}


@app.get("/api/outreach/{company_id}")
def get_outreach_actions(company_id: str, limit: int = 10):
    """Get recent outreach actions for a company."""
    return db.get_outreach_actions(company_id=company_id, limit=limit)


# --- Pipeline Endpoints ---

@app.post("/api/pipeline/run")
def run_pipeline(profile_id: Optional[str] = None):
    """Run the full ETL pipeline for active companies."""
    result = etl.run_pipeline(profile_id=profile_id)
    return result


@app.post("/api/pipeline/financials")
def refresh_financials(profile_id: Optional[str] = None):
    """Refresh financial data for companies with stale data."""
    result = etl.refresh_financials(profile_id=profile_id)
    return result


@app.post("/api/pipeline/update-all")
def update_all(profile_id: Optional[str] = None):
    """Run full pipeline and refresh financials in one call."""
    pipeline_result = etl.run_pipeline(profile_id=profile_id)
    financials_result = etl.refresh_financials(force=True, profile_id=profile_id)
    return {
        "pipeline": pipeline_result,
        "financials": financials_result,
    }


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
