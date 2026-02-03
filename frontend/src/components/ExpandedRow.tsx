import type { CompanyPainSummary, CompanyFinancials } from '../types';
import { SIGNAL_LABELS } from '../types';

interface ExpandedRowProps {
  company: CompanyPainSummary;
  financials?: CompanyFinancials;
}

export function ExpandedRow({ company, financials }: ExpandedRowProps) {
  // Sort signals by sales_relevance (pain score) descending
  const sortedSignals = [...company.signals].sort(
    (a, b) => b.sales_relevance - a.sales_relevance
  );

  // Calculate last signal age display
  const getLastSignalDisplay = (hours: number): string => {
    if (hours === Infinity) return '—';
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${Math.round(hours)}h ago`;
    const days = Math.round(hours / 24);
    return `${days}d ago`;
  };

  return (
    <div className="bg-gray-50 border-l-4 border-blue-500 p-4">
      {/* Summary Stats Section - moved from main table */}
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Pain Score:</span>
          <span
            className={`px-2 py-0.5 rounded font-medium ${
              company.max_pain_score >= 0.7
                ? 'bg-red-100 text-red-800'
                : company.max_pain_score >= 0.5
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-gray-100 text-gray-600'
            }`}
          >
            {Math.round(company.max_pain_score * 100)}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Pain Points:</span>
          <span className="font-medium">{company.signal_count}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Last Signal:</span>
          <span className="font-medium">{getLastSignalDisplay(company.newest_signal_age_hours)}</span>
        </div>
      </div>

      {/* Financials Section */}
      {financials && (
        <div className="mb-4 p-3 bg-white rounded-lg border border-gray-200">
          <h4 className="font-medium text-gray-700 mb-2">Financial Overview</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Market Cap:</span>
              <span className="ml-2 font-medium">
                {financials.market_cap
                  ? formatMarketCap(financials.market_cap)
                  : '—'}
              </span>
              {financials.market_cap_tier && (
                <span className="ml-1 text-xs text-gray-400">
                  ({financials.market_cap_tier})
                </span>
              )}
            </div>
            <div>
              <span className="text-gray-500">7D Change:</span>
              <span
                className={`ml-2 font-medium ${
                  financials.price_change_7d && financials.price_change_7d >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {financials.price_change_7d
                  ? `${financials.price_change_7d >= 0 ? '+' : ''}${(financials.price_change_7d * 100).toFixed(1)}%`
                  : '—'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">30D Change:</span>
              <span
                className={`ml-2 font-medium ${
                  financials.price_change_30d && financials.price_change_30d >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {financials.price_change_30d
                  ? `${financials.price_change_30d >= 0 ? '+' : ''}${(financials.price_change_30d * 100).toFixed(1)}%`
                  : '—'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Last Earnings:</span>
              <span className="ml-2 font-medium">
                {financials.last_earnings ? formatEarningsDate(financials.last_earnings) : '—'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Next Earnings:</span>
              <span className="ml-2 font-medium">
                {financials.next_earnings ? formatEarningsDate(financials.next_earnings) : '—'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Signals Section */}
      <div>
        <h4 className="font-medium text-gray-700 mb-3">
          Pain Points ({company.signal_count})
        </h4>
        <div className="space-y-3">
          {sortedSignals.map((signal) => (
            <div
              key={signal.id}
              className="p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      {SIGNAL_LABELS[signal.signal_type]}
                    </span>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        signal.sales_relevance >= 0.7
                          ? 'bg-red-100 text-red-700'
                          : signal.sales_relevance >= 0.5
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      Pain: {Math.round(signal.sales_relevance * 100)}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{signal.summary}</p>
                  {signal.talking_point && (
                    <div className="mt-2 p-2 bg-blue-50 rounded text-sm text-blue-800 border-l-2 border-blue-400">
                      <strong>Talking Point:</strong> {signal.talking_point}
                    </div>
                  )}
                </div>
                <div className="text-right text-xs text-gray-400 whitespace-nowrap">
                  {signal.articles && (
                    <a
                      href={signal.articles.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline block mb-1"
                    >
                      {signal.articles.source || 'View Source'}
                    </a>
                  )}
                  {formatDate(signal.created_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function formatMarketCap(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  return `$${value.toLocaleString()}`;
}

function formatEarningsDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}
