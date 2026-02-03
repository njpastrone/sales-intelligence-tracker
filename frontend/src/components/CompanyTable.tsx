import { useState, useMemo, Fragment } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getExpandedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ExpandedState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import type { CompanyPainSummary, CompanyFinancials } from '../types';
import { SIGNAL_LABELS } from '../types';
import { ExpandedRow } from './ExpandedRow';
import { ActionButtons } from './ActionButtons';
import type { StockMovementFilter, IRCycleFilter } from './Filters';

interface CompanyTableProps {
  data: CompanyPainSummary[];
  financials: Record<string, CompanyFinancials>;
  hiddenCompanyIds: Set<string>;
  onMarkContacted: (companyId: string) => void;
  onSnooze: (companyId: string) => void;
  onAddNote: (companyId: string, note: string) => void;
  onDelete: (companyId: string) => void;
  signalTypeFilter: string | null;
  stockMovementFilter: StockMovementFilter;
  irCycleFilter: IRCycleFilter;
  showHidden: boolean;
}

// Format earnings date as "Feb 5" or "Apr 29"
// Use UTC methods to avoid timezone shift (API returns date-only strings like "2026-04-30")
function formatEarningsDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

// IR Cycle stages based on earnings dates
type IRCycleStage = 'quiet_period' | 'earnings_week' | 'open_window' | 'mid_quarter' | 'unknown';

interface IRCycleInfo {
  stage: IRCycleStage;
  label: string;
  opportunity: 'high' | 'medium' | 'low';
  color: string;
  tooltip: string;
}

function calculateIRCycle(lastEarnings: string | null, nextEarnings: string | null): IRCycleInfo {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // Parse dates in UTC to avoid timezone issues
  const lastDate = lastEarnings ? new Date(lastEarnings + 'T00:00:00Z') : null;
  const nextDate = nextEarnings ? new Date(nextEarnings + 'T00:00:00Z') : null;

  // Calculate days since last earnings
  const daysSinceLast = lastDate
    ? Math.floor((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
    : null;

  // Calculate days until next earnings
  const daysUntilNext = nextDate
    ? Math.floor((nextDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
    : null;

  // Quiet Period: ≤14 days until next earnings
  if (daysUntilNext !== null && daysUntilNext <= 14) {
    return {
      stage: 'quiet_period',
      label: 'Quiet Period',
      opportunity: 'low',
      color: 'bg-gray-100 text-gray-600',
      tooltip: 'Limited external comms before earnings. Low outreach opportunity.',
    };
  }

  // Earnings Week: ≤7 days since last earnings
  if (daysSinceLast !== null && daysSinceLast >= 0 && daysSinceLast <= 7) {
    return {
      stage: 'earnings_week',
      label: 'Earnings Week',
      opportunity: 'low',
      color: 'bg-gray-100 text-gray-600',
      tooltip: 'IR team focused on earnings calls and follow-up. Low outreach opportunity.',
    };
  }

  // Open Window: 8-45 days since last earnings
  if (daysSinceLast !== null && daysSinceLast >= 8 && daysSinceLast <= 45) {
    return {
      stage: 'open_window',
      label: 'Open Window',
      opportunity: 'high',
      color: 'bg-green-100 text-green-800',
      tooltip: 'Active investor outreach period. High outreach opportunity.',
    };
  }

  // Mid-Quarter: >45 days since last earnings
  if (daysSinceLast !== null && daysSinceLast > 45) {
    return {
      stage: 'mid_quarter',
      label: 'Mid-Quarter',
      opportunity: 'medium',
      color: 'bg-amber-100 text-amber-800',
      tooltip: 'Between earnings cycles, strategic planning. Medium outreach opportunity.',
    };
  }

  // Unknown: no earnings data
  return {
    stage: 'unknown',
    label: '—',
    opportunity: 'medium',
    color: 'text-gray-400',
    tooltip: 'No earnings data available.',
  };
}

const columnHelper = createColumnHelper<CompanyPainSummary>();

export function CompanyTable({
  data,
  financials,
  hiddenCompanyIds,
  onMarkContacted,
  onSnooze,
  onAddNote,
  onDelete,
  signalTypeFilter,
  stockMovementFilter,
  irCycleFilter,
  showHidden,
}: CompanyTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'max_pain_score', desc: true },
  ]);
  const [expanded, setExpanded] = useState<ExpandedState>({});
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  // Filter data based on hidden companies and filters
  const filteredData = useMemo(() => {
    let result = data;

    // Filter out hidden companies unless showHidden is true
    if (!showHidden) {
      result = result.filter((company) => !hiddenCompanyIds.has(company.company_id));
    }

    // Filter by signal type
    if (signalTypeFilter) {
      result = result.filter((company) =>
        company.signals.some((signal) => signal.signal_type === signalTypeFilter)
      );
    }

    // Filter by stock movement
    if (stockMovementFilter !== 'all') {
      result = result.filter((company) => {
        const fin = financials[company.company_id];
        if (!fin?.price_change_7d) return false;
        if (stockMovementFilter === 'positive') return fin.price_change_7d >= 0;
        if (stockMovementFilter === 'negative') return fin.price_change_7d < 0;
        return true;
      });
    }

    // Filter by IR cycle
    if (irCycleFilter !== 'all') {
      result = result.filter((company) => {
        const fin = financials[company.company_id];
        const cycle = calculateIRCycle(fin?.last_earnings ?? null, fin?.next_earnings ?? null);
        return cycle.stage === irCycleFilter;
      });
    }

    return result;
  }, [data, financials, hiddenCompanyIds, signalTypeFilter, stockMovementFilter, irCycleFilter, showHidden]);

  const columns = useMemo(
    () => [
      // Company column
      columnHelper.accessor('name', {
        header: 'Company',
        cell: ({ row, getValue }) => {
          const isHidden = hiddenCompanyIds.has(row.original.company_id);
          return (
            <div className="flex items-center gap-2">
              <span className={isHidden ? 'text-gray-400' : 'font-medium'}>
                {getValue()}
              </span>
              {row.original.ticker && (
                <span className="text-xs text-gray-500 bg-blue-50 px-1.5 py-0.5 rounded">
                  {row.original.ticker}
                </span>
              )}
              {isHidden && (
                <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                  hidden
                </span>
              )}
            </div>
          );
        },
      }),
      // What's Happening - AI summary
      columnHelper.accessor('max_pain_summary', {
        header: "What's Happening",
        cell: ({ getValue }) => {
          const summary = getValue();
          if (!summary) return <span className="text-gray-400 text-sm">No recent signals</span>;
          return (
            <p className="text-sm text-gray-700">{summary}</p>
          );
        },
        size: 350,
      }),
      // Signal Type with severity indicator
      columnHelper.accessor(
        (row) => row.signals[0]?.signal_type || 'neutral',
        {
          id: 'top_signal_type',
          header: 'IR Pain Point',
          cell: ({ getValue, row }) => {
            const type = getValue();
            const pain = row.original.max_pain_score;
            const label = SIGNAL_LABELS[type];
            const severityColor =
              pain >= 0.7
                ? 'bg-red-100 text-red-800'
                : pain >= 0.5
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-gray-100 text-gray-600';
            return (
              <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${severityColor}`}>
                {label}
              </span>
            );
          },
        }
      ),
      // Stock - 7D price change
      columnHelper.accessor(
        (row) => {
          const fin = financials[row.company_id];
          return fin?.price_change_7d ?? null;
        },
        {
          id: 'price_change',
          header: 'Stock (7D)',
          cell: ({ getValue }) => {
            const change = getValue();
            if (change === null) return <span className="text-gray-400">—</span>;
            const percentage = (change * 100).toFixed(1);
            const isPositive = change >= 0;
            return (
              <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}
                {percentage}%
              </span>
            );
          },
        }
      ),
      // Last Earnings date
      columnHelper.accessor(
        (row) => financials[row.company_id]?.last_earnings ?? null,
        {
          id: 'last_earnings',
          header: 'Last Earnings',
          cell: ({ getValue }) => {
            const date = getValue();
            if (!date) return <span className="text-gray-400">—</span>;
            return (
              <span className="text-sm text-gray-700">
                {formatEarningsDate(date)}
              </span>
            );
          },
        }
      ),
      // Next Earnings date
      columnHelper.accessor(
        (row) => financials[row.company_id]?.next_earnings ?? null,
        {
          id: 'next_earnings',
          header: 'Next Earnings',
          cell: ({ getValue }) => {
            const date = getValue();
            if (!date) return <span className="text-gray-400">—</span>;
            return (
              <span className="text-sm text-gray-700">
                {formatEarningsDate(date)}
              </span>
            );
          },
        }
      ),
      // IR Cycle stage
      columnHelper.accessor(
        (row) => {
          const fin = financials[row.company_id];
          return calculateIRCycle(fin?.last_earnings ?? null, fin?.next_earnings ?? null);
        },
        {
          id: 'ir_cycle',
          header: 'IR Cycle',
          cell: ({ getValue }) => {
            const cycle = getValue();
            return (
              <span className="relative group inline-flex items-center gap-1">
                <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${cycle.color}`}>
                  {cycle.label}
                </span>
                {cycle.stage !== 'unknown' && (
                  <>
                    <svg
                      className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-600 cursor-help"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <circle cx="12" cy="12" r="10" strokeWidth={2} />
                      <path strokeLinecap="round" strokeWidth={2} d="M12 16v-4m0-4h.01" />
                    </svg>
                    <span className="absolute bottom-full left-0 mb-2 px-3 py-2 text-xs text-white bg-gray-800 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none w-48">
                      {cycle.tooltip}
                    </span>
                  </>
                )}
              </span>
            );
          },
          sortingFn: (rowA, rowB) => {
            const order: Record<IRCycleStage, number> = {
              open_window: 0,
              mid_quarter: 1,
              earnings_week: 2,
              quiet_period: 3,
              unknown: 4,
            };
            const a = rowA.getValue<IRCycleInfo>('ir_cycle').stage;
            const b = rowB.getValue<IRCycleInfo>('ir_cycle').stage;
            return order[a] - order[b];
          },
        }
      ),
      // Actions column
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <ActionButtons
            companyId={row.original.company_id}
            companyName={row.original.name}
            onMarkContacted={onMarkContacted}
            onSnooze={onSnooze}
            onAddNote={onAddNote}
            onDelete={onDelete}
          />
        ),
        size: 220,
      }),
      // Expand toggle column (on the right)
      columnHelper.display({
        id: 'expand',
        header: '',
        cell: ({ row }) =>
          row.getCanExpand() ? (
            <button
              onClick={row.getToggleExpandedHandler()}
              className="p-1.5 hover:bg-blue-100 rounded transition-colors text-blue-600"
              title={row.getIsExpanded() ? 'Collapse details' : 'Expand details'}
            >
              {row.getIsExpanded() ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </button>
          ) : null,
        size: 50,
      }),
      // Hidden column for sorting by pain score
      columnHelper.accessor('max_pain_score', {
        header: () => null,
        cell: () => null,
        sortingFn: 'basic',
        enableHiding: true,
      }),
    ],
    [financials, hiddenCompanyIds, onMarkContacted, onSnooze, onAddNote, onDelete]
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
      expanded,
      columnFilters,
    },
    onSortingChange: setSorting,
    onExpandedChange: setExpanded,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowCanExpand: (row) => row.original.signals.length > 0,
    getRowId: (row) => row.company_id,
  });

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-blue-100">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="text-left py-3 px-4 font-medium text-blue-900 bg-blue-50"
                  style={{ width: header.getSize() !== 150 ? header.getSize() : undefined }}
                >
                  {header.isPlaceholder ? null : (
                    <div
                      className={
                        header.column.getCanSort()
                          ? 'cursor-pointer select-none flex items-center gap-1 hover:text-gray-900'
                          : ''
                      }
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {{
                        asc: ' ↑',
                        desc: ' ↓',
                      }[header.column.getIsSorted() as string] ?? null}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <Fragment key={row.id}>
              <tr
                className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  row.getIsExpanded() ? 'bg-blue-50' : ''
                }`}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="py-3 px-4">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
              {row.getIsExpanded() && (
                <tr>
                  <td colSpan={columns.length} className="p-0">
                    <ExpandedRow
                      company={row.original}
                      financials={financials[row.original.company_id]}
                    />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
      {filteredData.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No companies match the current filters.
        </div>
      )}
    </div>
  );
}
