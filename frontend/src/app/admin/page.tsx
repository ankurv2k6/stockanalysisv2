'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, filingsApi, Job } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Download, Play, RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

function JobStatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return (
        <Badge className="bg-green-500">
          <CheckCircle className="h-3 w-3 mr-1" />
          Completed
        </Badge>
      );
    case 'running':
      return (
        <Badge className="bg-blue-500">
          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
          Running
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="destructive">
          <XCircle className="h-3 w-3 mr-1" />
          Failed
        </Badge>
      );
    case 'pending':
      return (
        <Badge variant="outline">
          <Clock className="h-3 w-3 mr-1" />
          Pending
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function ProgressBar({ completed, total }: { completed: number; total: number | null }) {
  if (!total) return <span className="text-muted-foreground">-</span>;
  const percentage = Math.round((completed / total) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-sm text-muted-foreground">
        {completed}/{total}
      </span>
    </div>
  );
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [activeJob, setActiveJob] = useState<number | null>(null);

  const { data: currentJob, isLoading: jobLoading } = useQuery({
    queryKey: ['jobStatus', activeJob],
    queryFn: () => jobsApi.getStatus(activeJob || undefined),
    refetchInterval: (query) => {
      const job = query.state.data;
      return job?.status === 'running' ? 2000 : false;
    },
  });

  const { data: jobHistory, isLoading: historyLoading } = useQuery({
    queryKey: ['jobHistory'],
    queryFn: () => jobsApi.getHistory(10),
  });

  const { data: pendingFilings } = useQuery({
    queryKey: ['pendingFilings'],
    queryFn: () => filingsApi.list({ status: 'pending', limit: 1 }),
  });

  const fetchMutation = useMutation({
    mutationFn: () => jobsApi.fetchAll(),
    onSuccess: (data) => {
      setActiveJob(data.job_id);
      queryClient.invalidateQueries({ queryKey: ['jobHistory'] });
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: () => jobsApi.analyzeAll(),
    onSuccess: (data) => {
      setActiveJob(data.job_id);
      queryClient.invalidateQueries({ queryKey: ['jobHistory'] });
    },
  });

  const isFetchRunning = currentJob?.job_type === 'fetch' && currentJob?.status === 'running';
  const isAnalyzeRunning = currentJob?.job_type === 'analyze' && currentJob?.status === 'running';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Admin</h2>
        <p className="text-muted-foreground">
          Manage data fetching and analysis jobs
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Fetch SEC Filings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Step 1: Fetch SEC Filings
            </CardTitle>
            <CardDescription>
              Downloads latest 10-K filings for all S&P 100 companies from SEC EDGAR.
              Rate limited to respect SEC guidelines.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isFetchRunning && currentJob && (
              <div className="p-3 bg-secondary/50 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Progress</span>
                  <JobStatusBadge status={currentJob.status} />
                </div>
                <ProgressBar
                  completed={currentJob.completed_items}
                  total={currentJob.total_items}
                />
              </div>
            )}
            <Button
              onClick={() => fetchMutation.mutate()}
              disabled={isFetchRunning || fetchMutation.isPending}
              className="w-full"
            >
              {fetchMutation.isPending || isFetchRunning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Fetch All Filings
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Run AI Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5" />
              Step 2: Run AI Analysis
            </CardTitle>
            <CardDescription>
              Analyzes fetched filings using Gemini 1.5 Flash.
              Generates summaries and risk assessments.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 bg-secondary/50 rounded-lg">
              <span className="text-sm">
                Pending filings: <span className="font-medium">{pendingFilings?.length || 0}</span>
              </span>
            </div>
            {isAnalyzeRunning && currentJob && (
              <div className="p-3 bg-secondary/50 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Progress</span>
                  <JobStatusBadge status={currentJob.status} />
                </div>
                <ProgressBar
                  completed={currentJob.completed_items}
                  total={currentJob.total_items}
                />
              </div>
            )}
            <Button
              onClick={() => analyzeMutation.mutate()}
              disabled={isAnalyzeRunning || analyzeMutation.isPending}
              className="w-full"
            >
              {analyzeMutation.isPending || isAnalyzeRunning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Analyze All Pending
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Job History */}
      <Card>
        <CardHeader>
          <CardTitle>Job History</CardTitle>
          <CardDescription>Recent background job executions</CardDescription>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !jobHistory?.length ? (
            <p className="text-muted-foreground text-sm text-center py-4">
              No jobs have been run yet.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Completed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobHistory.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell className="font-medium capitalize">
                      {job.job_type}
                    </TableCell>
                    <TableCell>
                      <JobStatusBadge status={job.status} />
                    </TableCell>
                    <TableCell>
                      <ProgressBar
                        completed={job.completed_items}
                        total={job.total_items}
                      />
                    </TableCell>
                    <TableCell>
                      {job.started_at
                        ? new Date(job.started_at).toLocaleString()
                        : '-'}
                    </TableCell>
                    <TableCell>
                      {job.completed_at
                        ? new Date(job.completed_at).toLocaleString()
                        : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {currentJob?.error_message && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Job Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{currentJob.error_message}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
