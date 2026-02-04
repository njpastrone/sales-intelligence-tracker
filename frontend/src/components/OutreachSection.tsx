import { useState } from 'react';
import type { OutreachCompanyDetail } from '../api/client';

interface OutreachSectionProps {
  title: string;
  items: OutreachCompanyDetail[];
  onUndo: (companyId: string) => void;
  colorScheme: 'green' | 'amber';
}

// Calculate relative time string
function getRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffDays === 0) {
    if (diffHours === 0) {
      return 'Just now';
    }
    return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
  }
  if (diffDays === 1) {
    return '1 day ago';
  }
  return `${diffDays} days ago`;
}

export function OutreachSection({
  title,
  items,
  onUndo,
  colorScheme,
}: OutreachSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (items.length === 0) {
    return null;
  }

  const colors = {
    green: {
      header: 'bg-green-50 border-green-200',
      headerText: 'text-green-800',
      headerHover: 'hover:bg-green-100',
      badge: 'bg-green-200 text-green-800',
      row: 'border-green-100',
      undoBtn: 'text-green-700 bg-green-100 hover:bg-green-200 border-green-300',
    },
    amber: {
      header: 'bg-amber-50 border-amber-200',
      headerText: 'text-amber-800',
      headerHover: 'hover:bg-amber-100',
      badge: 'bg-amber-200 text-amber-800',
      row: 'border-amber-100',
      undoBtn: 'text-amber-700 bg-amber-100 hover:bg-amber-200 border-amber-300',
    },
  };

  const c = colors[colorScheme];

  return (
    <div className={`rounded-lg border shadow-sm ${c.header} mb-4`}>
      {/* Collapsible Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between px-4 py-3 ${c.headerHover} transition-colors rounded-t-lg`}
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-4 h-4 ${c.headerText} transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className={`font-medium ${c.headerText}`}>{title}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${c.badge}`}>
            {items.length}
          </span>
        </div>
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="px-4 pb-3">
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.company_id}
                className={`flex items-center justify-between py-2 px-3 bg-white rounded border ${c.row}`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{item.name}</span>
                  {item.ticker && (
                    <span className="text-xs text-gray-500 bg-blue-50 px-1.5 py-0.5 rounded">
                      {item.ticker}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">
                    {getRelativeTime(item.created_at)}
                  </span>
                  <button
                    onClick={() => onUndo(item.company_id)}
                    className={`text-xs px-2 py-1 rounded cursor-pointer transition-colors border ${c.undoBtn}`}
                  >
                    Undo
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
