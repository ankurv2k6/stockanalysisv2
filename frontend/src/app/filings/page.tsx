'use client';

import { useQuery } from '@tanstack/react-query';
import { filingsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

export default function FilingsPage() {
  const { data: filings, isLoading } = useQuery({
    queryKey: ['filings'],
    queryFn: () => filingsApi.list({ limit: 100 }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Filings</h2>
        <p className="text-muted-foreground">
          All SEC 10-K filings in the system
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filing List</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(10)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !filings?.length ? (
            <div className="text-center py-8 text-muted-foreground">
              No filings found. Go to Admin to fetch filings.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Filing Date</TableHead>
                  <TableHead>Fiscal Year</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Accession Number</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filings.map((filing) => (
                  <TableRow key={filing.id}>
                    <TableCell className="font-medium">{filing.id}</TableCell>
                    <TableCell>{filing.filing_type}</TableCell>
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
