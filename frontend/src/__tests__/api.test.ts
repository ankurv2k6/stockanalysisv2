/**
 * Tests for API client utilities
 */

import { companiesApi, filingsApi, jobsApi } from '@/lib/api';

// Mock fetch globally
global.fetch = jest.fn();

const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('companiesApi', () => {
    it('should fetch companies list', async () => {
      const mockResponse = {
        companies: [
          { id: 1, ticker: 'AAPL', name: 'Apple Inc.' },
        ],
        total: 1,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await companiesApi.list();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/companies'),
        expect.any(Object)
      );
      expect(result.companies).toHaveLength(1);
      expect(result.companies[0].ticker).toBe('AAPL');
    });

    it('should fetch company by ticker', async () => {
      const mockCompany = {
        id: 1,
        ticker: 'AAPL',
        name: 'Apple Inc.',
        filings: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCompany,
      } as Response);

      const result = await companiesApi.get('AAPL');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/companies/AAPL'),
        expect.any(Object)
      );
      expect(result.ticker).toBe('AAPL');
    });

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Company not found' }),
      } as Response);

      await expect(companiesApi.get('INVALID')).rejects.toThrow('Company not found');
    });

    it('should fetch sectors list', async () => {
      const mockSectors = { sectors: ['Technology', 'Finance'] };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSectors,
      } as Response);

      const result = await companiesApi.getSectors();

      expect(result.sectors).toContain('Technology');
    });

    it('should apply pagination parameters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ companies: [], total: 0 }),
      } as Response);

      await companiesApi.list({ skip: 10, limit: 20 });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('skip=10'),
        expect.any(Object)
      );
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=20'),
        expect.any(Object)
      );
    });
  });

  describe('filingsApi', () => {
    it('should fetch filings list', async () => {
      const mockFilings = [
        { id: 1, filing_type: '10-K', status: 'completed' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFilings,
      } as Response);

      const result = await filingsApi.list();

      expect(result).toHaveLength(1);
      expect(result[0].filing_type).toBe('10-K');
    });

    it('should fetch filing analysis', async () => {
      const mockAnalysis = {
        id: 1,
        filing_id: 1,
        summary: 'Test summary',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnalysis,
      } as Response);

      const result = await filingsApi.getAnalysis(1);

      expect(result.summary).toBe('Test summary');
    });
  });

  describe('jobsApi', () => {
    it('should start fetch job', async () => {
      const mockResponse = {
        job_id: 1,
        status: 'started',
        message: 'Job started',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await jobsApi.fetchAll();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/jobs/fetch-all'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.job_id).toBe(1);
    });

    it('should start analyze job', async () => {
      const mockResponse = {
        job_id: 2,
        status: 'started',
        message: 'Job started',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await jobsApi.analyzeAll();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/jobs/analyze-all'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.job_id).toBe(2);
    });

    it('should get job status', async () => {
      const mockJob = {
        id: 1,
        job_type: 'fetch',
        status: 'running',
        total_items: 100,
        completed_items: 50,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockJob,
      } as Response);

      const result = await jobsApi.getStatus(1);

      expect(result?.status).toBe('running');
      expect(result?.completed_items).toBe(50);
    });

    it('should get risk summary', async () => {
      const mockSummary = {
        total_companies: 100,
        analyzed_companies: 85,
        high_risk_count: 10,
        average_risk_score: 5.2,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummary,
      } as Response);

      const result = await jobsApi.getRiskSummary();

      expect(result.total_companies).toBe(100);
      expect(result.high_risk_count).toBe(10);
    });
  });
});
