const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Types
export interface Company {
  id: number;
  ticker: string;
  name: string;
  cik: string;
  sector: string | null;
  created_at: string;
  latest_filing_date: string | null;
  risk_scores: RiskScores | null;
}

export interface RiskScores {
  overall: number;
  operational: number;
  financial: number;
  regulatory: number;
  strategic: number;
  reputational: number;
}

export interface Filing {
  id: number;
  company_id: number;
  filing_type: string;
  filing_date: string;
  fiscal_year: number | null;
  accession_number: string;
  status: string;
  created_at: string;
}

export interface CompanyDetail extends Company {
  filings: Filing[];
  latest_analysis: Analysis | null;
}

export interface Analysis {
  id: number;
  filing_id: number;
  summary: string;
  risk_assessment: Record<string, RiskCategory> | null;
  created_at: string;
}

export interface RiskCategory {
  score: number;
  severity?: string;
  risks: string[];
}

export interface Job {
  id: number;
  job_type: string;
  status: string;
  total_items: number | null;
  completed_items: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface RiskSummary {
  total_companies: number;
  analyzed_companies: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  average_risk_score: number;
  risk_by_category: Record<string, number>;
}

export interface CompanyListResponse {
  companies: Company[];
  total: number;
}

// API Functions
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

// Companies API
export const companiesApi = {
  list: (params?: { skip?: number; limit?: number; sector?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.set('skip', String(params.skip));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.sector) searchParams.set('sector', params.sector);
    const query = searchParams.toString();
    return fetchApi<CompanyListResponse>(`/companies${query ? `?${query}` : ''}`);
  },

  get: (ticker: string) => fetchApi<CompanyDetail>(`/companies/${ticker}`),

  getSectors: () => fetchApi<{ sectors: string[] }>('/companies/sectors/list'),
};

// Filings API
export const filingsApi = {
  list: (params?: { skip?: number; limit?: number; status?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.set('skip', String(params.skip));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.status) searchParams.set('status', params.status);
    const query = searchParams.toString();
    return fetchApi<Filing[]>(`/filings${query ? `?${query}` : ''}`);
  },

  get: (id: number) => fetchApi<Filing>(`/filings/${id}`),

  getAnalysis: (id: number) => fetchApi<Analysis>(`/filings/${id}/analysis`),
};

// Jobs API
export const jobsApi = {
  fetchAll: () => fetchApi<{ job_id: number; status: string; message: string }>('/jobs/fetch-all', { method: 'POST' }),

  analyzeAll: () => fetchApi<{ job_id: number; status: string; message: string }>('/jobs/analyze-all', { method: 'POST' }),

  getStatus: (jobId?: number) => {
    const query = jobId ? `?job_id=${jobId}` : '';
    return fetchApi<Job | null>(`/jobs/status${query}`);
  },

  getHistory: (limit?: number) => {
    const query = limit ? `?limit=${limit}` : '';
    return fetchApi<Job[]>(`/jobs/history${query}`);
  },

  getRiskSummary: () => fetchApi<RiskSummary>('/jobs/risk-summary'),
};
