'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { companiesApi, Company } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import Link from 'next/link';
import { Search, ArrowUpDown } from 'lucide-react';

type SortField = 'ticker' | 'name' | 'sector' | 'risk';
type SortDirection = 'asc' | 'desc';

function getRiskBadge(score: number | undefined) {
  if (!score) return <Badge variant="outline">N/A</Badge>;
  if (score >= 7) return <Badge variant="destructive">{score.toFixed(1)}</Badge>;
  if (score >= 4) return <Badge className="bg-yellow-500">{score.toFixed(1)}</Badge>;
  return <Badge className="bg-green-500">{score.toFixed(1)}</Badge>;
}

export default function CompaniesPage() {
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('ticker');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const { data, isLoading } = useQuery({
    queryKey: ['companies', 'all'],
    queryFn: () => companiesApi.list({ limit: 200 }),
  });

  const { data: sectorsData } = useQuery({
    queryKey: ['sectors'],
    queryFn: () => companiesApi.getSectors(),
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredAndSortedCompanies = data?.companies
    .filter((company) => {
      const matchesSearch =
        search === '' ||
        company.ticker.toLowerCase().includes(search.toLowerCase()) ||
        company.name.toLowerCase().includes(search.toLowerCase());
      const matchesSector = sectorFilter === 'all' || company.sector === sectorFilter;
      return matchesSearch && matchesSector;
    })
    .sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'ticker':
          comparison = a.ticker.localeCompare(b.ticker);
          break;
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'sector':
          comparison = (a.sector || '').localeCompare(b.sector || '');
          break;
        case 'risk':
          comparison = (a.risk_scores?.overall || 0) - (b.risk_scores?.overall || 0);
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Companies</h2>
        <p className="text-muted-foreground">
          S&P 100 companies with risk analysis
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <CardTitle>Company List</CardTitle>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search companies..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8 w-[200px]"
                />
              </div>
              <Select value={sectorFilter} onValueChange={setSectorFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by sector" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sectors</SelectItem>
                  {sectorsData?.sectors.map((sector) => (
                    <SelectItem key={sector} value={sector}>
                      {sector}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(10)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : filteredAndSortedCompanies?.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No companies found matching your criteria.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer"
                    onClick={() => handleSort('ticker')}
                  >
                    <div className="flex items-center gap-1">
                      Ticker
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer"
                    onClick={() => handleSort('name')}
                  >
                    <div className="flex items-center gap-1">
                      Company Name
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer"
                    onClick={() => handleSort('sector')}
                  >
                    <div className="flex items-center gap-1">
                      Sector
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </TableHead>
                  <TableHead>Filing Date</TableHead>
                  <TableHead
                    className="cursor-pointer text-right"
                    onClick={() => handleSort('risk')}
                  >
                    <div className="flex items-center gap-1 justify-end">
                      Risk Score
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedCompanies?.map((company) => (
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
                    <TableCell>
                      {company.latest_filing_date
                        ? new Date(company.latest_filing_date).toLocaleDateString()
                        : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      {getRiskBadge(company.risk_scores?.overall)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {filteredAndSortedCompanies && (
            <div className="mt-4 text-sm text-muted-foreground">
              Showing {filteredAndSortedCompanies.length} of {data?.total || 0} companies
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
