import type { SignalType } from '../types';
import { SIGNAL_LABELS } from '../types';

export type StockMovementFilter = 'all' | 'positive' | 'negative';

interface FiltersProps {
  timeWindow: number;
  onTimeWindowChange: (days: number) => void;
  signalTypeFilter: string | null;
  onSignalTypeChange: (type: string | null) => void;
  stockMovementFilter: StockMovementFilter;
  onStockMovementChange: (filter: StockMovementFilter) => void;
  showHidden: boolean;
  onShowHiddenChange: (show: boolean) => void;
}

const TIME_WINDOW_OPTIONS = [7, 14, 30];

const SIGNAL_TYPES: SignalType[] = [
  'activist_risk',
  'analyst_negative',
  'earnings_miss',
  'leadership_change',
  'governance_issue',
  'esg_negative',
  'stock_pressure',
  'capital_stress',
  'peer_pressure',
];

export function Filters({
  timeWindow,
  onTimeWindowChange,
  signalTypeFilter,
  onSignalTypeChange,
  stockMovementFilter,
  onStockMovementChange,
  showHidden,
  onShowHiddenChange,
}: FiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-white border-b border-blue-100">
      {/* Time Window - clarified label */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Signals from:</label>
        <select
          value={timeWindow}
          onChange={(e) => onTimeWindowChange(Number(e.target.value))}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {TIME_WINDOW_OPTIONS.map((days) => (
            <option key={days} value={days}>
              Last {days} days
            </option>
          ))}
        </select>
      </div>

      {/* Signal Type Filter - renamed to IR Pain Point */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">IR Pain Point:</label>
        <select
          value={signalTypeFilter || ''}
          onChange={(e) => onSignalTypeChange(e.target.value || null)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All types</option>
          {SIGNAL_TYPES.map((type) => (
            <option key={type} value={type}>
              {SIGNAL_LABELS[type]}
            </option>
          ))}
        </select>
      </div>

      {/* Stock Movement Filter - new */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Stock (7D):</label>
        <select
          value={stockMovementFilter}
          onChange={(e) => onStockMovementChange(e.target.value as StockMovementFilter)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All</option>
          <option value="negative">Negative movers</option>
          <option value="positive">Positive movers</option>
        </select>
      </div>

      {/* Show Hidden Toggle - clarified label */}
      <div className="flex items-center gap-2 ml-auto">
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={showHidden}
            onChange={(e) => onShowHiddenChange(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          Include hidden
        </label>
      </div>
    </div>
  );
}
