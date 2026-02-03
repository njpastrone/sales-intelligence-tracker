import type { SignalType, UrgencyLevel } from '../types';
import { SIGNAL_LABELS, SIGNAL_ICONS, URGENCY_CONFIG } from '../types';

interface FiltersProps {
  timeWindow: number;
  onTimeWindowChange: (days: number) => void;
  signalTypeFilter: string | null;
  onSignalTypeChange: (type: string | null) => void;
  urgencyFilter: UrgencyLevel | null;
  onUrgencyChange: (urgency: UrgencyLevel | null) => void;
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

const URGENCY_LEVELS: UrgencyLevel[] = ['hot', 'warm', 'cold'];

export function Filters({
  timeWindow,
  onTimeWindowChange,
  signalTypeFilter,
  onSignalTypeChange,
  urgencyFilter,
  onUrgencyChange,
  showHidden,
  onShowHiddenChange,
}: FiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-white border-b border-gray-200">
      {/* Time Window */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Time:</label>
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

      {/* Signal Type Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Signal:</label>
        <select
          value={signalTypeFilter || ''}
          onChange={(e) => onSignalTypeChange(e.target.value || null)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All signals</option>
          {SIGNAL_TYPES.map((type) => (
            <option key={type} value={type}>
              {SIGNAL_ICONS[type]} {SIGNAL_LABELS[type]}
            </option>
          ))}
        </select>
      </div>

      {/* Urgency Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Urgency:</label>
        <div className="flex gap-1">
          <button
            onClick={() => onUrgencyChange(null)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              urgencyFilter === null
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          {URGENCY_LEVELS.map((level) => {
            const config = URGENCY_CONFIG[level];
            const isActive = urgencyFilter === level;
            return (
              <button
                key={level}
                onClick={() => onUrgencyChange(isActive ? null : level)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  isActive
                    ? 'text-white'
                    : 'hover:opacity-80'
                }`}
                style={{
                  backgroundColor: isActive ? config.color : config.bgColor,
                  color: isActive ? 'white' : config.color,
                }}
              >
                {config.icon} {level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Show Hidden Toggle */}
      <div className="flex items-center gap-2 ml-auto">
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={showHidden}
            onChange={(e) => onShowHiddenChange(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          Show contacted/snoozed
        </label>
      </div>
    </div>
  );
}
