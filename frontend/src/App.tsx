import { useState, useMemo } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { CompanyFinancials } from './types';
import { CompanyTable } from './components/CompanyTable';
import { Filters, type StockMovementFilter, type IRCycleFilter } from './components/Filters';
import { Sidebar } from './components/Sidebar';
import * as api from './api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function Dashboard() {
  const queryClientInstance = useQueryClient();

  // Filter state
  const [timeWindow, setTimeWindow] = useState(7);
  const [signalTypeFilter, setSignalTypeFilter] = useState<string | null>(null);
  const [stockMovementFilter, setStockMovementFilter] = useState<StockMovementFilter>('all');
  const [irCycleFilter, setIRCycleFilter] = useState<IRCycleFilter>('all');
  const [showHidden, setShowHidden] = useState(false);

  // Fetch company pain summary
  const {
    data: companySummary = [],
    isLoading: isLoadingSummary,
  } = useQuery({
    queryKey: ['companySummary', timeWindow],
    queryFn: () => api.getCompanySummary(timeWindow),
  });

  // Fetch financials
  const { data: financialsData = [] } = useQuery({
    queryKey: ['financials'],
    queryFn: () => api.getFinancials(),
  });

  // Fetch hidden company IDs
  const { data: hiddenData } = useQuery({
    queryKey: ['hiddenCompanies'],
    queryFn: () => api.getHiddenCompanies(),
  });

  // Convert financials array to lookup map
  const financialsMap = useMemo(() => {
    const map: Record<string, CompanyFinancials> = {};
    financialsData.forEach((f) => {
      map[f.company_id] = f;
    });
    return map;
  }, [financialsData]);

  // Convert hidden IDs to Set
  const hiddenCompanyIds = useMemo(
    () => new Set(hiddenData?.hidden_company_ids || []),
    [hiddenData]
  );

  // Mutations
  const addCompanyMutation = useMutation({
    mutationFn: (data: { name: string; ticker?: string }) => api.addCompany(data),
    onSuccess: () => {
      queryClientInstance.invalidateQueries({ queryKey: ['companySummary'] });
      queryClientInstance.invalidateQueries({ queryKey: ['financials'] });
    },
  });

  const addOutreachMutation = useMutation({
    mutationFn: api.addOutreachAction,
    onSuccess: () => {
      queryClientInstance.invalidateQueries({ queryKey: ['hiddenCompanies'] });
    },
  });

  const runPipelineMutation = useMutation({
    mutationFn: api.runPipeline,
    onSuccess: () => {
      queryClientInstance.invalidateQueries({ queryKey: ['companySummary'] });
      queryClientInstance.invalidateQueries({ queryKey: ['financials'] });
    },
  });

  const refreshFinancialsMutation = useMutation({
    mutationFn: api.refreshFinancials,
    onSuccess: async () => {
      // Use refetchQueries to ensure data is updated before showing success
      await queryClientInstance.refetchQueries({ queryKey: ['financials'] });
    },
  });

  const updateAllMutation = useMutation({
    mutationFn: api.updateAll,
    onSuccess: async () => {
      // Refetch all data to ensure UI is in sync
      await Promise.all([
        queryClientInstance.refetchQueries({ queryKey: ['companySummary'] }),
        queryClientInstance.refetchQueries({ queryKey: ['financials'] }),
      ]);
    },
  });

  const deleteCompanyMutation = useMutation({
    mutationFn: api.deleteCompany,
    onSuccess: () => {
      queryClientInstance.invalidateQueries({ queryKey: ['companySummary'] });
      queryClientInstance.invalidateQueries({ queryKey: ['financials'] });
    },
  });

  // Handlers
  const handleAddCompany = async (name: string, ticker: string) => {
    await addCompanyMutation.mutateAsync({ name, ticker });
  };

  const handleMarkContacted = (companyId: string) => {
    addOutreachMutation.mutate({
      company_id: companyId,
      action_type: 'contacted',
    });
  };

  const handleSnooze = (companyId: string) => {
    addOutreachMutation.mutate({
      company_id: companyId,
      action_type: 'snoozed',
    });
  };

  const handleAddNote = (companyId: string, note: string) => {
    addOutreachMutation.mutate({
      company_id: companyId,
      action_type: 'note',
      note,
    });
  };

  const handleRunPipeline = async () => {
    return await runPipelineMutation.mutateAsync();
  };

  const handleRefreshFinancials = async () => {
    return await refreshFinancialsMutation.mutateAsync();
  };

  const handleUpdateAll = async () => {
    return await updateAllMutation.mutateAsync();
  };

  const handleDeleteCompany = (companyId: string) => {
    deleteCompanyMutation.mutate(companyId);
  };

  // Calculate totals
  const totalCompanies = companySummary.length;
  const totalSignals = companySummary.reduce((sum, c) => sum + c.signal_count, 0);

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <Sidebar
        onAddCompany={handleAddCompany}
        onRunPipeline={handleRunPipeline}
        onRefreshFinancials={handleRefreshFinancials}
        onUpdateAll={handleUpdateAll}
        totalCompanies={totalCompanies}
        totalSignals={totalSignals}
        isLoading={isLoadingSummary}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 px-6 py-4">
          <h1 className="text-2xl font-bold text-white">Sales Intelligence Tracker</h1>
          <p className="text-sm text-blue-100 mt-1">
            Monitor IR pain signals for outreach opportunities
          </p>
        </header>

        {/* Filters */}
        <Filters
          timeWindow={timeWindow}
          onTimeWindowChange={setTimeWindow}
          signalTypeFilter={signalTypeFilter}
          onSignalTypeChange={setSignalTypeFilter}
          stockMovementFilter={stockMovementFilter}
          onStockMovementChange={setStockMovementFilter}
          irCycleFilter={irCycleFilter}
          onIRCycleChange={setIRCycleFilter}
          showHidden={showHidden}
          onShowHiddenChange={setShowHidden}
        />

        {/* Table */}
        <main className="flex-1 p-6 overflow-auto">
          {isLoadingSummary ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"></div>
                <p className="text-gray-500">Loading companies...</p>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-blue-100 shadow-sm">
              <CompanyTable
                data={companySummary}
                financials={financialsMap}
                hiddenCompanyIds={hiddenCompanyIds}
                onMarkContacted={handleMarkContacted}
                onSnooze={handleSnooze}
                onAddNote={handleAddNote}
                onDelete={handleDeleteCompany}
                signalTypeFilter={signalTypeFilter}
                stockMovementFilter={stockMovementFilter}
                irCycleFilter={irCycleFilter}
                showHidden={showHidden}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}

export default App;
