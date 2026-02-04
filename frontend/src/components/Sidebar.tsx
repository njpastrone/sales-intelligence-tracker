import { useState } from 'react';
import type { PipelineStats, FinancialsRefreshStats } from '../types';

interface SidebarProps {
  onAddCompany: (name: string, ticker: string) => Promise<void>;
  onRunPipeline: () => Promise<PipelineStats>;
  onRefreshFinancials: () => Promise<FinancialsRefreshStats>;
  onUpdateAll: () => Promise<{ pipeline: PipelineStats; financials: FinancialsRefreshStats }>;
  totalCompanies: number;
  totalSignals: number;
  isLoading: boolean;
}

export function Sidebar({
  onAddCompany,
  onRunPipeline,
  onRefreshFinancials,
  onUpdateAll,
  totalCompanies,
  totalSignals,
  isLoading,
}: SidebarProps) {
  const [companyName, setCompanyName] = useState('');
  const [ticker, setTicker] = useState('');
  const [isAddingCompany, setIsAddingCompany] = useState(false);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const [isRefreshingFinancials, setIsRefreshingFinancials] = useState(false);
  const [isUpdatingAll, setIsUpdatingAll] = useState(false);
  const [companyMessage, setCompanyMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [pipelineMessage, setPipelineMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleAddCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim() || !ticker.trim()) return;

    setIsAddingCompany(true);
    setCompanyMessage(null);

    try {
      await onAddCompany(companyName.trim(), ticker.trim());
      setCompanyName('');
      setTicker('');
      setCompanyMessage({ type: 'success', text: 'Company added. Click "Update Everything" to fetch pain points and financial data.' });
    } catch (error) {
      setCompanyMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to add company',
      });
    } finally {
      setIsAddingCompany(false);
    }
  };

  const handleRunPipeline = async () => {
    setIsPipelineRunning(true);
    setPipelineMessage(null);

    try {
      const stats = await onRunPipeline();
      setPipelineMessage({
        type: 'success',
        text: `Complete: ${stats.signals_created} new pain points from ${stats.articles_new} articles`,
      });
    } catch (error) {
      setPipelineMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Pipeline failed',
      });
    } finally {
      setIsPipelineRunning(false);
    }
  };

  const handleRefreshFinancials = async () => {
    setIsRefreshingFinancials(true);
    setPipelineMessage(null);

    try {
      const stats = await onRefreshFinancials();
      setPipelineMessage({
        type: 'success',
        text: `Refreshed ${stats.companies_refreshed} companies`,
      });
    } catch (error) {
      setPipelineMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Refresh failed',
      });
    } finally {
      setIsRefreshingFinancials(false);
    }
  };

  const handleUpdateAll = async () => {
    setIsUpdatingAll(true);
    setPipelineMessage(null);
    setCompanyMessage(null);

    try {
      const result = await onUpdateAll();
      setPipelineMessage({
        type: 'success',
        text: `Updated: ${result.pipeline.signals_created} pain points, ${result.financials.companies_refreshed} financials`,
      });
    } catch (error) {
      setPipelineMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Update failed',
      });
    } finally {
      setIsUpdatingAll(false);
    }
  };

  const isAnyOperationRunning = isPipelineRunning || isRefreshingFinancials || isUpdatingAll;

  return (
    <div className="w-80 bg-blue-50 border-r border-blue-100 p-4 flex flex-col gap-4">
      {/* Stats */}
      <div className="bg-white rounded-lg p-4 border border-blue-100 shadow-sm">
        <h3 className="font-semibold text-blue-900 mb-3">Dashboard</h3>
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">{totalCompanies}</div>
            <div className="text-xs text-gray-500">Companies</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-800">{totalSignals}</div>
            <div className="text-xs text-gray-500">Pain Points</div>
          </div>
        </div>
      </div>

      {/* Add Company Form */}
      <div className="bg-white rounded-lg p-4 border border-blue-100 shadow-sm">
        <h3 className="font-semibold text-blue-900 mb-3">Add Company</h3>
        <form onSubmit={handleAddCompany} className="space-y-3">
          <div>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Company name"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Ticker symbol"
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
        {/* Company Message */}
        {companyMessage && (
          <div
            className={`mt-3 p-2 rounded-md text-xs ${
              companyMessage.type === 'success'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            {companyMessage.text}
            <button
              onClick={() => setCompanyMessage(null)}
              className="float-right text-current opacity-60 hover:opacity-100 ml-2"
            >
              x
            </button>
          </div>
        )}
      </div>

      {/* Pipeline Actions */}
      <div className="bg-white rounded-lg p-4 border border-blue-100 shadow-sm">
        <h3 className="font-semibold text-blue-900 mb-3">Data Pipeline</h3>
        <div className="space-y-2">
          <button
            onClick={handleUpdateAll}
            disabled={isAnyOperationRunning || isLoading}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isUpdatingAll ? 'Updating...' : 'Update Everything'}
          </button>
          <div className="border-t border-gray-100 pt-2 mt-2">
            <p className="text-xs text-gray-400 mb-2">Or run individually:</p>
            <div className="space-y-2">
              <button
                onClick={handleRunPipeline}
                disabled={isAnyOperationRunning || isLoading}
                className="w-full px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isPipelineRunning ? 'Running...' : 'Pipeline Only'}
              </button>
              <button
                onClick={handleRefreshFinancials}
                disabled={isAnyOperationRunning || isLoading}
                className="w-full px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isRefreshingFinancials ? 'Refreshing...' : 'Financials Only'}
              </button>
            </div>
          </div>
        </div>
        {/* Pipeline Message */}
        {pipelineMessage && (
          <div
            className={`mt-3 p-2 rounded-md text-xs ${
              pipelineMessage.type === 'success'
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            {pipelineMessage.text}
            <button
              onClick={() => setPipelineMessage(null)}
              className="float-right text-current opacity-60 hover:opacity-100 ml-2"
            >
              x
            </button>
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="mt-auto text-xs text-gray-500">
        <p className="mb-1">
          <strong>Update Everything:</strong> Fetches news, pain points & financials
        </p>
        <p className="mb-1">
          <strong>Pipeline:</strong> Fetches news & classifies pain points
        </p>
        <p>
          <strong>Financials:</strong> Updates stock prices & earnings
        </p>
      </div>
    </div>
  );
}
