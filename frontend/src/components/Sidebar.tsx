import { useState } from 'react';
import type { PipelineStats, FinancialsRefreshStats } from '../types';

interface SidebarProps {
  onAddCompany: (name: string, ticker: string) => Promise<void>;
  onRunPipeline: () => Promise<PipelineStats>;
  onRefreshFinancials: () => Promise<FinancialsRefreshStats>;
  totalCompanies: number;
  totalSignals: number;
  isLoading: boolean;
}

export function Sidebar({
  onAddCompany,
  onRunPipeline,
  onRefreshFinancials,
  totalCompanies,
  totalSignals,
  isLoading,
}: SidebarProps) {
  const [companyName, setCompanyName] = useState('');
  const [ticker, setTicker] = useState('');
  const [isAddingCompany, setIsAddingCompany] = useState(false);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const [isRefreshingFinancials, setIsRefreshingFinancials] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  const handleAddCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim() || !ticker.trim()) return;

    setIsAddingCompany(true);
    setMessage(null);

    try {
      await onAddCompany(companyName.trim(), ticker.trim());
      setCompanyName('');
      setTicker('');
      setMessage({ type: 'success', text: 'Company added successfully!' });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to add company',
      });
    } finally {
      setIsAddingCompany(false);
    }
  };

  const handleRunPipeline = async () => {
    setIsPipelineRunning(true);
    setMessage(null);

    try {
      const stats = await onRunPipeline();
      setMessage({
        type: 'success',
        text: `Pipeline complete: ${stats.signals_created} new signals from ${stats.articles_new} articles`,
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Pipeline failed',
      });
    } finally {
      setIsPipelineRunning(false);
    }
  };

  const handleRefreshFinancials = async () => {
    setIsRefreshingFinancials(true);
    setMessage(null);

    try {
      const stats = await onRefreshFinancials();
      setMessage({
        type: 'success',
        text: `Refreshed ${stats.companies_refreshed} companies`,
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Refresh failed',
      });
    } finally {
      setIsRefreshingFinancials(false);
    }
  };

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 p-4 flex flex-col gap-6">
      {/* Stats */}
      <div className="bg-white rounded-lg p-4 border border-gray-200">
        <h3 className="font-semibold text-gray-800 mb-3">Dashboard</h3>
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">{totalCompanies}</div>
            <div className="text-xs text-gray-500">Companies</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-orange-600">{totalSignals}</div>
            <div className="text-xs text-gray-500">Signals</div>
          </div>
        </div>
      </div>

      {/* Add Company Form */}
      <div className="bg-white rounded-lg p-4 border border-gray-200">
        <h3 className="font-semibold text-gray-800 mb-3">Add Company</h3>
        <form onSubmit={handleAddCompany} className="space-y-3">
          <div>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Company name *"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Ticker *"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <p className="text-xs text-gray-400 mt-1">Required for stock data</p>
          </div>
          <button
            type="submit"
            disabled={isAddingCompany || !companyName.trim() || !ticker.trim()}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isAddingCompany ? 'Adding...' : 'Add Company'}
          </button>
        </form>
      </div>

      {/* Pipeline Actions */}
      <div className="bg-white rounded-lg p-4 border border-gray-200">
        <h3 className="font-semibold text-gray-800 mb-3">Data Pipeline</h3>
        <div className="space-y-2">
          <button
            onClick={handleRunPipeline}
            disabled={isPipelineRunning || isLoading}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isPipelineRunning ? (
              <>
                <span className="animate-spin">⟳</span> Running...
              </>
            ) : (
              <>🔄 Run Pipeline</>
            )}
          </button>
          <button
            onClick={handleRefreshFinancials}
            disabled={isRefreshingFinancials || isLoading}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isRefreshingFinancials ? (
              <>
                <span className="animate-spin">⟳</span> Refreshing...
              </>
            ) : (
              <>📊 Refresh Financials</>
            )}
          </button>
        </div>
      </div>

      {/* Message Toast */}
      {message && (
        <div
          className={`p-3 rounded-md text-sm ${
            message.type === 'success'
              ? 'bg-green-100 text-green-800 border border-green-200'
              : 'bg-red-100 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
          <button
            onClick={() => setMessage(null)}
            className="float-right text-current opacity-60 hover:opacity-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-auto text-xs text-gray-500">
        <p className="mb-1">
          <strong>Pipeline:</strong> Fetches news & classifies signals
        </p>
        <p>
          <strong>Financials:</strong> Updates stock prices & earnings
        </p>
      </div>
    </div>
  );
}
