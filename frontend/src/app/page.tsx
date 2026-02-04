'use client';

import { useQuery } from '@tanstack/react-query';
import { jobsApi, companiesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Building2, FileCheck, AlertTriangle, TrendingUp } from 'lucide-react';
import Link from 'next/link';

function StatsCard({
  title,
  value,
  icon: Icon,
  description,
  loading,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description?: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-20" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: riskSummary, isLoading: riskLoading } = useQuery({
    queryKey: ['riskSummary'],
    queryFn: () => jobsApi.getRiskSummary(),
  });

  const { data: companiesData, isLoading: companiesLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesApi.list({ limit: 10 }),
  });

  const isLoading = riskLoading || companiesLoading;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of S&P 100 company risk analysis
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Companies"
          value={riskSummary?.total_companies ?? 0}
          icon={Building2}
          description="S&P 100 companies tracked"
          loading={isLoading}
        />
        <StatsCard
          title="Analyzed"
          value={riskSummary?.analyzed_companies ?? 0}
          icon={FileCheck}
          description="Companies with analysis"
          loading={isLoading}
        />
        <StatsCard
          title="High Risk"
          value={riskSummary?.high_risk_count ?? 0}
          icon={AlertTriangle}
          description="Companies flagged"
          loading={isLoading}
        />
        <StatsCard
          title="Avg Risk Score"
          value={riskSummary?.average_risk_score?.toFixed(1) ?? 'N/A'}
          icon={TrendingUp}
          description="Out of 10"
          loading={isLoading}
        />
      </div>

      {/* Recent Companies */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Companies</CardTitle>
        </CardHeader>
        <CardContent>
          {companiesLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : companiesData?.companies.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No companies found.</p>
              <p className="text-sm mt-2">
                Go to <Link href="/admin" className="text-primary underline">Admin</Link> to fetch company data.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {companiesData?.companies.slice(0, 5).map((company) => (
                <Link
                  key={company.id}
                  href={`/companies/${company.ticker}`}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div>
                    <span className="font-medium">{company.ticker}</span>
                    <span className="text-muted-foreground ml-2">{company.name}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">{company.sector}</span>
                    {company.risk_scores && (
                      <span className={`font-medium ${
                        company.risk_scores.overall >= 7 ? 'text-red-500' :
                        company.risk_scores.overall >= 4 ? 'text-yellow-500' :
                        'text-green-500'
                      }`}>
                        {company.risk_scores.overall.toFixed(1)}
                      </span>
                    )}
                  </div>
                </Link>
              ))}
              {companiesData && companiesData.companies.length > 5 && (
                <Link
                  href="/companies"
                  className="block text-center text-sm text-primary hover:underline pt-2"
                >
                  View all {companiesData.total} companies
                </Link>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
