// TypeScript interfaces for the Sales Intelligence Tracker

export interface Profile {
  id: string;
  name: string;
  created_at: string;
}

export interface Company {
  id: string;
  name: string;
  ticker: string | null;
  aliases: string[];
  active: boolean;
  created_at: string;
}

export interface Article {
  id: string;
  company_id: string;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  fetched_at: string;
}

export interface Signal {
  id: string;
  article_id: string;
  company_id: string;
  summary: string;
  signal_type: SignalType;
  relevance_score: number;
  sales_relevance: number;
  talking_point: string | null;
  created_at: string;
  articles?: Article;
  companies?: Company;
}

export interface CompanyFinancials {
  company_id: string;
  price_change_7d: number | null;
  price_change_30d: number | null;
  market_cap: number | null;
  market_cap_tier: MarketCapTier | null;
  last_earnings: string | null;
  next_earnings: string | null;
  updated_at: string;
}

export interface OutreachAction {
  id: string;
  company_id: string;
  action_type: OutreachActionType;
  note: string | null;
  created_at: string;
}

// Company pain summary (from GET /api/companies/summary)
export interface CompanyPainSummary {
  company_id: string;
  name: string;
  ticker: string | null;
  max_pain_score: number;
  max_pain_summary: string;
  signal_count: number;
  newest_signal_age_hours: number;
  signals: Signal[];
}

// Signal types matching config.py
export type SignalType =
  | 'activist_risk'
  | 'analyst_negative'
  | 'earnings_miss'
  | 'leadership_change'
  | 'governance_issue'
  | 'esg_negative'
  | 'stock_pressure'
  | 'capital_stress'
  | 'peer_pressure'
  | 'neutral';

export type MarketCapTier = 'small' | 'mid' | 'large' | 'unknown';

export type OutreachActionType = 'contacted' | 'snoozed' | 'note';

export type UrgencyLevel = 'hot' | 'warm' | 'cold';

// Signal type display info
export const SIGNAL_ICONS: Record<SignalType, string> = {
  activist_risk: '🦈',
  analyst_negative: '📉',
  earnings_miss: '❌',
  leadership_change: '🔄',
  governance_issue: '⚔️',
  esg_negative: '🌍',
  stock_pressure: '📊',
  capital_stress: '💸',
  peer_pressure: '🏃',
  neutral: '📰',
};

export const SIGNAL_LABELS: Record<SignalType, string> = {
  activist_risk: 'Activist Risk',
  analyst_negative: 'Analyst Negative',
  earnings_miss: 'Earnings Miss',
  leadership_change: 'Leadership Change',
  governance_issue: 'Governance Issue',
  esg_negative: 'ESG Negative',
  stock_pressure: 'Stock Pressure',
  capital_stress: 'Capital Stress',
  peer_pressure: 'Peer Pressure',
  neutral: 'Neutral',
};

// Urgency display info
export const URGENCY_CONFIG: Record<
  UrgencyLevel,
  { icon: string; label: string; color: string; bgColor: string }
> = {
  hot: { icon: '🔥', label: 'Call today', color: '#dc3545', bgColor: '#fee2e2' },
  warm: { icon: '🟡', label: 'Call this week', color: '#fd7e14', bgColor: '#fef3c7' },
  cold: { icon: '⚪', label: 'Monitor', color: '#6c757d', bgColor: '#f3f4f6' },
};

// Urgency thresholds
export const URGENCY_THRESHOLDS = {
  hot: { min_pain: 0.7, max_hours: 48 },
  warm: { min_pain: 0.5, max_hours: 168 }, // 7 days
};

// Helper to calculate urgency level
export function getUrgencyLevel(painScore: number, signalAgeHours: number): UrgencyLevel {
  if (painScore >= URGENCY_THRESHOLDS.hot.min_pain && signalAgeHours <= URGENCY_THRESHOLDS.hot.max_hours) {
    return 'hot';
  }
  if (painScore >= URGENCY_THRESHOLDS.warm.min_pain && signalAgeHours <= URGENCY_THRESHOLDS.warm.max_hours) {
    return 'warm';
  }
  return 'cold';
}

// Pipeline stats response
export interface PipelineStats {
  companies: number;
  articles_fetched: number;
  articles_new: number;
  signals_created: number;
}

export interface FinancialsRefreshStats {
  companies_refreshed: number;
  companies_failed: number;
}
