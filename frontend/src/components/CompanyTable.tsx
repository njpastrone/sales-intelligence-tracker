import { useState, useMemo } from 'react';
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
import type { CompanyPainSummary, CompanyFinancials, UrgencyLevel } from '../types';
import { getUrgencyLevel, URGENCY_CONFIG, SIGNAL_ICONS } from '../types';
import { ExpandedRow } from './ExpandedRow';
import { ActionButtons } from './ActionButtons';

interface CompanyTableProps {
  data: CompanyPainSummary[];
  financials: Record<string, CompanyFinancials>;
  hiddenCompanyIds: Set<string>;
  onMarkContacted: (companyId: string) => void;
  onSnooze: (companyId: string) => void;
  onAddNote: (companyId: string, note: string) => void;
  signalTypeFilter: string | null;
  urgencyFilter: UrgencyLevel | null;
  showHidden: boolean;
}

const columnHelper = createColumnHelper<CompanyPainSummary>();

export function CompanyTable({
  data,
  financials,
  hiddenCompanyIds,
  onMarkContacted,
  onSnooze,
  onAddNote,
  signalTypeFilter,
  urgencyFilter,
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

    // Filter by urgency level
    if (urgencyFilter) {
      result = result.filter((company) => {
        const urgency = getUrgencyLevel(
          company.max_pain_score,
          company.newest_signal_age_hours
        );
        return urgency === urgencyFilter;
      });
    }

    return result;
  }, [data, hiddenCompanyIds, signalTypeFilter, urgencyFilter, showHidden]);

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: 'expander',
        header: () => null,
        cell: ({ row }) =>
          row.getCanExpand() ? (
            <button
              onClick={row.getToggleExpandedHandler()}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
            >
              {row.getIsExpanded() ? '▼' : '▶'}
            </button>
          ) : null,
        size: 40,
      }),
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
                <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
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
      columnHelper.accessor('max_pain_score', {
        header: 'Pain Score',
        cell: ({ getValue }) => {
          const score = getValue();
          const percentage = Math.round(score * 100);
          const bgColor =
            score >= 0.7
              ? 'bg-red-100 text-red-800'
              : score >= 0.5
                ? 'bg-orange-100 text-orange-800'
                : 'bg-gray-100 text-gray-600';
          return (
            <span className={`px-2 py-1 rounded text-sm font-medium ${bgColor}`}>
              {percentage}%
            </span>
          );
        },
        sortingFn: 'basic',
      }),
      columnHelper.accessor(
        (row) => getUrgencyLevel(row.max_pain_score, row.newest_signal_age_hours),
        {
          id: 'urgency',
          header: 'Urgency',
          cell: ({ getValue }) => {
            const urgency = getValue();
            const config = URGENCY_CONFIG[urgency];
            return (
              <span
                className="px-2 py-1 rounded text-sm font-medium"
                style={{ backgroundColor: config.bgColor, color: config.color }}
              >
                {config.icon} {config.label}
              </span>
            );
          },
        }
      ),
      columnHelper.accessor('signal_count', {
        header: 'Signals',
        cell: ({ getValue, row }) => {
          // Get unique signal types for icons
          const signalTypes = [
            ...new Set(row.original.signals.map((s) => s.signal_type)),
          ];
          return (
            <div className="flex items-center gap-1">
              <span className="font-medium">{getValue()}</span>
              <span className="text-sm">
                {signalTypes.slice(0, 3).map((type) => SIGNAL_ICONS[type]).join(' ')}
              </span>
            </div>
          );
        },
      }),
      columnHelper.accessor(
        (row) => {
          const fin = financials[row.company_id];
          return fin?.price_change_7d ?? null;
        },
        {
          id: 'price_change',
          header: '7D Price',
          cell: ({ getValue }) => {
            const change = getValue();
            if (change === null) return <span className="text-gray-400">—</span>;
            const percentage = (change * 100).toFixed(1);
            const isPositive = change >= 0;
            return (
              <span className={isPositive ? 'text-green-600' : 'text-red-600'}>
                {isPositive ? '+' : ''}
                {percentage}%
              </span>
            );
          },
        }
      ),
      columnHelper.accessor('newest_signal_age_hours', {
        header: 'Last Signal',
        cell: ({ getValue }) => {
          const hours = getValue();
          if (hours === Infinity) return <span className="text-gray-400">—</span>;
          if (hours < 1) return 'Just now';
          if (hours < 24) return `${Math.round(hours)}h ago`;
          const days = Math.round(hours / 24);
          return `${days}d ago`;
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <ActionButtons
            companyId={row.original.company_id}
            onMarkContacted={onMarkContacted}
            onSnooze={onSnooze}
            onAddNote={onAddNote}
          />
        ),
        size: 180,
      }),
    ],
    [financials, hiddenCompanyIds, onMarkContacted, onSnooze, onAddNote]
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
            <tr key={headerGroup.id} className="border-b border-gray-200">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="text-left py-3 px-4 font-medium text-gray-700 bg-gray-50"
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
            <>
              <tr
                key={row.id}
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
                <tr key={`${row.id}-expanded`}>
                  <td colSpan={columns.length} className="p-0">
                    <ExpandedRow
                      company={row.original}
                      financials={financials[row.original.company_id]}
                    />
                  </td>
                </tr>
              )}
            </>
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
