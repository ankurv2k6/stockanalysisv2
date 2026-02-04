'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import Link from 'next/link';
import { ArrowLeft, ExternalLink } from 'lucide-react';

const RISK_CATEGORIES = [
  { key: 'operational', label: 'Operational' },
  { key: 'financial', label: 'Financial' },
  { key: 'regulatory', label: 'Regulatory' },
  { key: 'strategic', label: 'Strategic' },
  { key: 'reputational', label: 'Reputational' },
];

function RiskBar({ score, label }: { score: number; label: string }) {
  const percentage = (score / 10) * 100;
  const getColor = () => {
    if (score >= 7) return 'bg-red-500';
    if (score >= 4) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium">{score.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor()} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'completed':
      return <Badge className="bg-green-500">Analyzed</Badge>;
    case 'processing':
      return <Badge className="bg-blue-500">Processing</Badge>;
    case 'pending':
      return <Badge variant="outline">Pending</Badge>;
    case 'error':
      return <Badge variant="destructive">Error</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

export default function CompanyDetailPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const { data: company, isLoading, error } = useQuery({
    queryKey: ['company', ticker],
    queryFn: () => companiesApi.get(ticker),
    enabled: !!ticker,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="space-y-4">
        <Link href="/companies" className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to Companies
        </Link>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              Company not found or an error occurred.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const overallRisk = company.risk_scores?.overall;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link href="/companies" className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Back to Companies
      </Link>

      {/* Company Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold">{company.ticker}</h2>
            {overallRisk && (
              <Badge
                className={
                  overallRisk >= 7
                    ? 'bg-red-500'
                    : overallRisk >= 4
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }
              >
                Risk: {overallRisk.toFixed(1)}
              </Badge>
            )}
          </div>
          <p className="text-xl text-muted-foreground">{company.name}</p>
        </div>
        <div className="text-right text-sm text-muted-foreground">
          <p>Sector: <span className="font-medium">{company.sector || 'N/A'}</span></p>
          <p>CIK: {company.cik}</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Executive Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Executive Summary</CardTitle>
            <CardDescription>AI-generated analysis from latest 10-K</CardDescription>
          </CardHeader>
          <CardContent>
            {company.latest_analysis?.summary ? (
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {company.latest_analysis.summary}
              </p>
            ) : (
              <p className="text-muted-foreground text-sm">
                No analysis available yet. Run analysis from the Admin page.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Risk Assessment */}
        <Card>
          <CardHeader>
            <CardTitle>Risk Assessment</CardTitle>
            <CardDescription>Scores by category (1-10)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {company.risk_scores ? (
              <>
                {RISK_CATEGORIES.map(({ key, label }) => (
                  <RiskBar
                    key={key}
                    label={label}
                    score={company.risk_scores?.[key as keyof typeof company.risk_scores] || 0}
                  />
                ))}
                <div className="pt-4 border-t">
                  <div className="flex justify-between font-medium">
                    <span>Overall Risk Score</span>
                    <span
                      className={
                        overallRisk && overallRisk >= 7
                          ? 'text-red-500'
                          : overallRisk && overallRisk >= 4
                          ? 'text-yellow-500'
                          : 'text-green-500'
                      }
                    >
                      {overallRisk?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground text-sm">
                No risk assessment available yet.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Key Risks */}
      {company.latest_analysis?.risk_assessment && (
        <Card>
          <CardHeader>
            <CardTitle>Key Risks by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {RISK_CATEGORIES.map(({ key, label }) => {
                const categoryData = company.latest_analysis?.risk_assessment?.[key];
                if (!categoryData?.risks?.length) return null;
                return (
                  <div key={key} className="space-y-2">
                    <h4 className="font-medium">{label}</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {categoryData.risks.slice(0, 3).map((risk: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-primary">•</span>
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filing History */}
      <Card>
        <CardHeader>
          <CardTitle>Filing History</CardTitle>
          <CardDescription>SEC 10-K filings</CardDescription>
        </CardHeader>
        <CardContent>
          {company.filings.length === 0 ? (
            <p className="text-muted-foreground text-sm">No filings found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Filing Date</TableHead>
                  <TableHead>Fiscal Year</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Accession #</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {company.filings.map((filing) => (
                  <TableRow key={filing.id}>
                    <TableCell className="font-medium">{filing.filing_type}</TableCell>
                    <TableCell>
                      {new Date(filing.filing_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{filing.fiscal_year || 'N/A'}</TableCell>
                    <TableCell>{getStatusBadge(filing.status)}</TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {filing.accession_number}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
