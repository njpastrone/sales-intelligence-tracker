// API client for the Sales Intelligence Tracker backend

import axios from 'axios';
import type {
  Company,
  CompanyPainSummary,
  CompanyFinancials,
  Signal,
  OutreachAction,
  OutreachActionType,
  PipelineStats,
  FinancialsRefreshStats,
  SignalType,
} from '../types';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Companies ---

export async function getCompanies(activeOnly = true): Promise<Company[]> {
  const response = await api.get('/api/companies', {
    params: { active_only: activeOnly },
  });
  return response.data;
}

export async function addCompany(data: {
  name: string;
  ticker?: string;
  aliases?: string[];
}): Promise<Company> {
  const response = await api.post('/api/companies', data);
  return response.data;
}

export async function getCompanySummary(days = 7): Promise<CompanyPainSummary[]> {
  const response = await api.get('/api/companies/summary', {
    params: { days },
  });
  return response.data;
}

export async function deleteCompany(companyId: string): Promise<{ deleted: boolean; company_id: string }> {
  const response = await api.delete(`/api/companies/${companyId}`);
  return response.data;
}

// --- Financials ---

export async function getFinancials(companyId?: string): Promise<CompanyFinancials[]> {
  const response = await api.get('/api/financials', {
    params: companyId ? { company_id: companyId } : {},
  });
  return response.data;
}

// --- Signals ---

export async function getSignals(params?: {
  company_id?: string;
  min_relevance?: number;
  signal_type?: SignalType;
  limit?: number;
}): Promise<Signal[]> {
  const response = await api.get('/api/signals', { params });
  return response.data;
}

export async function getHotSignals(limit = 5): Promise<Signal[]> {
  const response = await api.get('/api/signals/hot', {
    params: { limit },
  });
  return response.data;
}

// --- Outreach ---

export async function addOutreachAction(data: {
  company_id: string;
  action_type: OutreachActionType;
  note?: string;
}): Promise<OutreachAction> {
  const response = await api.post('/api/outreach', data);
  return response.data;
}

export async function getOutreachActions(
  companyId: string,
  limit = 10
): Promise<OutreachAction[]> {
  const response = await api.get(`/api/outreach/${companyId}`, {
    params: { limit },
  });
  return response.data;
}

export interface OutreachCompanyDetail {
  company_id: string;
  name: string;
  ticker: string | null;
  created_at: string;
}

export interface HiddenCompaniesResponse {
  contacted: OutreachCompanyDetail[];
  snoozed: OutreachCompanyDetail[];
}

export async function getHiddenCompanies(
  contactedDays = 7,
  snoozedDays = 7
): Promise<HiddenCompaniesResponse> {
  const response = await api.get('/api/outreach/hidden', {
    params: { contacted_days: contactedDays, snoozed_days: snoozedDays },
  });
  return response.data;
}

export async function deleteOutreachAction(
  companyId: string,
  actionType: string
): Promise<{ deleted: boolean; company_id: string; action_type: string }> {
  const response = await api.delete(`/api/outreach/${companyId}/${actionType}`);
  return response.data;
}

// --- Pipeline ---

export async function runPipeline(): Promise<PipelineStats> {
  const response = await api.post('/api/pipeline/run');
  return response.data;
}

export async function refreshFinancials(): Promise<FinancialsRefreshStats> {
  const response = await api.post('/api/pipeline/financials');
  return response.data;
}

export async function updateAll(): Promise<{
  pipeline: PipelineStats;
  financials: FinancialsRefreshStats;
}> {
  const response = await api.post('/api/pipeline/update-all');
  return response.data;
}

export async function clearData(): Promise<{ signals: number; articles: number }> {
  const response = await api.delete('/api/pipeline/clear');
  return response.data;
}

// --- Config ---

export async function getSignalTypes(): Promise<Record<SignalType, string>> {
  const response = await api.get('/api/config/signal-types');
  return response.data;
}

// --- Init (combined initial load) ---

export interface InitData {
  summary: CompanyPainSummary[];
  financials: CompanyFinancials[];
  outreach: HiddenCompaniesResponse;
}

export async function getInitData(days = 7): Promise<InitData> {
  const response = await api.get('/api/init', {
    params: { days },
  });
  return response.data;
}

// --- Health ---

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await api.get('/api/health');
  return response.data;
}
