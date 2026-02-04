'use client';

import { useQuery } from '@tanstack/react-query';
import { jobsApi, companiesApi, Company } from '@/lib/api';
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
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const RISK_COLORS = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#22c55e',
};

const CATEGORY_COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#14b8a6'];

export default function RiskPage() {
  const { data: riskSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ['riskSummary'],
    queryFn: () => jobsApi.getRiskSummary(),
  });

  const { data: companiesData, isLoading: companiesLoading } = useQuery({
    queryKey: ['companies', 'all'],
    queryFn: () => companiesApi.list({ limit: 200 }),
  });

  const isLoading = summaryLoading || companiesLoading;

  // Prepare pie chart data
  const pieData = riskSummary
    ? [
        { name: 'High Risk', value: riskSummary.high_risk_count, color: RISK_COLORS.high },
        { name: 'Medium Risk', value: riskSummary.medium_risk_count, color: RISK_COLORS.medium },
        { name: 'Low Risk', value: riskSummary.low_risk_count, color: RISK_COLORS.low },
      ]
    : [];

  // Prepare bar chart data for risk by category
  const categoryData = riskSummary?.risk_by_category
    ? Object.entries(riskSummary.risk_by_category).map(([category, score], index) => ({
        category: category.charAt(0).toUpperCase() + category.slice(1),
        score: Number(score),
        fill: CATEGORY_COLORS[index % CATEGORY_COLORS.length],
      }))
    : [];

  // Get high risk companies
  const highRiskCompanies = companiesData?.companies
    .filter((c) => c.risk_scores && c.risk_scores.overall >= 7)
    .sort((a, b) => (b.risk_scores?.overall || 0) - (a.risk_scores?.overall || 0))
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Risk Overview</h2>
        <p className="text-muted-foreground">
          Aggregated risk analysis across all S&P 100 companies
        </p>
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Risk Distribution Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
            <CardDescription>Companies by risk level</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : pieData.every((d) => d.value === 0) ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No analyzed companies yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Risk by Category Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Average Risk by Category</CardTitle>
            <CardDescription>Mean scores across all companies</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : categoryData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No risk data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={categoryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 10]} />
                  <YAxis dataKey="category" type="category" width={100} />
                  <Tooltip />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-16" /> : riskSummary?.total_companies || 0}
            </div>
            <p className="text-sm text-muted-foreground">Total Companies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-16" /> : riskSummary?.analyzed_companies || 0}
            </div>
            <p className="text-sm text-muted-foreground">Analyzed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-500">
              {isLoading ? <Skeleton className="h-8 w-16" /> : riskSummary?.high_risk_count || 0}
            </div>
            <p className="text-sm text-muted-foreground">High Risk</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                riskSummary?.average_risk_score?.toFixed(1) || 'N/A'
              )}
            </div>
            <p className="text-sm text-muted-foreground">Avg Risk Score</p>
          </CardContent>
        </Card>
      </div>

      {/* High Risk Companies Table */}
      <Card>
        <CardHeader>
          <CardTitle>Highest Risk Companies</CardTitle>
          <CardDescription>Companies with overall risk score 7.0 or higher</CardDescription>
        </CardHeader>
        <CardContent>
          {companiesLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !highRiskCompanies?.length ? (
            <div className="text-center py-8 text-muted-foreground">
              No high-risk companies identified yet.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ticker</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Sector</TableHead>
                  <TableHead className="text-right">Overall Score</TableHead>
                  <TableHead className="text-right">Highest Category</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {highRiskCompanies.map((company) => {
                  const scores = company.risk_scores;
                  const categories = scores
                    ? [
                        { name: 'Operational', score: scores.operational },
                        { name: 'Financial', score: scores.financial },
                        { name: 'Regulatory', score: scores.regulatory },
                        { name: 'Strategic', score: scores.strategic },
                        { name: 'Reputational', score: scores.reputational },
                      ]
                    : [];
                  const highest = categories.sort((a, b) => b.score - a.score)[0];

                  return (
                    <TableRow key={company.id}>
                      <TableCell>
                        <Link
                          href={`/companies/${company.ticker}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {company.ticker}
                        </Link>
                      </TableCell>
                      <TableCell>{company.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{company.sector || 'N/A'}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="destructive">
                          {scores?.overall.toFixed(1)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {highest && (
                          <span className="text-sm text-muted-foreground">
                            {highest.name} ({highest.score.toFixed(1)})
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
