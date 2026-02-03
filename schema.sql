-- Sales Intelligence Tracker - Database Schema
-- Run this in Supabase SQL Editor to create the tables

-- Companies watchlist
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    ticker TEXT UNIQUE,
    aliases TEXT[] DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on ticker for lookups (UNIQUE already creates an index, but explicit for clarity)
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);

-- Articles fetched from news sources
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for deduplication lookups
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_company ON articles(company_id);

-- Signals (AI-classified articles)
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    summary TEXT,
    signal_type TEXT DEFAULT 'general',
    relevance_score REAL DEFAULT 0.5,
    sales_relevance REAL DEFAULT 0.5,  -- IR pain score (0-1)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for filtering
CREATE INDEX IF NOT EXISTS idx_signals_company ON signals(company_id);
CREATE INDEX IF NOT EXISTS idx_signals_relevance ON signals(relevance_score);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);

-- Add talking_point column for AI-generated outreach openers
ALTER TABLE signals ADD COLUMN IF NOT EXISTS talking_point TEXT;

-- Company financials (stock data from yfinance)
CREATE TABLE IF NOT EXISTS company_financials (
    company_id UUID PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
    price_change_7d REAL,
    price_change_30d REAL,
    market_cap BIGINT,
    market_cap_tier TEXT,  -- 'small', 'mid', 'large'
    last_earnings DATE,
    next_earnings DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Outreach actions (track contacted, snoozed, notes)
CREATE TABLE IF NOT EXISTS outreach_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,  -- 'contacted', 'snoozed', 'note'
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_company ON outreach_actions(company_id);
CREATE INDEX IF NOT EXISTS idx_outreach_type ON outreach_actions(action_type);
