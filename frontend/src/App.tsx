import { useState, useMemo } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { CompanyFinancials } from './types';
import { CompanyTable } from './components/CompanyTable';
import { Filters, type StockMovementFilter, type IRCycleFilter } from './components/Filters';
import { Sidebar } from './components/Sidebar';
import { OutreachSection } from './components/OutreachSection';
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

  // Fetch all initial data in a single request
  const {
    data: initData,
    isLoading: isLoadingInit,
  } = useQuery({
    queryKey: ['initData', timeWindow],
    queryFn: () => api.getInitData(timeWindow),
  });

  const companySummary = initData?.summary ?? [];
  const financialsData = initData?.financials ?? [];
  const hiddenData = initData?.outreach;

  // Convert financials array to lookup map
  const financialsMap = useMemo(() => {
    const map: Record<string, CompanyFinancials> = {};
    financialsData.forEach((f) => {
      map[f.company_id] = f;
    });
    return map;
  }, [financialsData]);

  // Extract contacted and snoozed company lists
  const contactedCompanies = hiddenData?.contacted || [];
  const snoozedCompanies = hiddenData?.snoozed || [];

  // Combined set of hidden company IDs for filtering the active table
  const hiddenCompanyIds = useMemo(
    () => new Set([
      ...contactedCompanies.map((c) => c.company_id),
      ...snoozedCompanies.map((c) => c.company_id),
    ]),
    [contactedCompanies, snoozedCompanies]
  );

  // Mutations
  const invalidateInitData = () => {
    queryClientInstance.invalidateQueries({ queryKey: ['initData'] });
  };

  const refetchInitData = () => {
    return queryClientInstance.refetchQueries({ queryKey: ['initData'] });
  };

  // Mutations
  const addCompanyMutation = useMutation({
    mutationFn: (data: { name: string; ticker?: string }) => api.addCompany(data),
    onSuccess: invalidateInitData,
  });

  const addOutreachMutation = useMutation({
    mutationFn: api.addOutreachAction,
    onSuccess: invalidateInitData,
  });

  const runPipelineMutation = useMutation({
    mutationFn: api.runPipeline,
    onSuccess: invalidateInitData,
  });

  const refreshFinancialsMutation = useMutation({
    mutationFn: api.refreshFinancials,
    onSuccess: async () => {
      await refetchInitData();
    },
  });

  const updateAllMutation = useMutation({
    mutationFn: api.updateAll,
    onSuccess: async () => {
      await refetchInitData();
    },
  });

  const deleteCompanyMutation = useMutation({
    mutationFn: api.deleteCompany,
    onSuccess: invalidateInitData,
  });

  const removeOutreachMutation = useMutation({
    mutationFn: ({ companyId, actionType }: { companyId: string; actionType: string }) =>
      api.deleteOutreachAction(companyId, actionType),
    onSuccess: invalidateInitData,
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

  const handleUndoContacted = (companyId: string) => {
    removeOutreachMutation.mutate({ companyId, actionType: 'contacted' });
  };

  const handleUndoSnoozed = (companyId: string) => {
    removeOutreachMutation.mutate({ companyId, actionType: 'snoozed' });
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
        isLoading={isLoadingInit}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 px-6 py-4">
          <h1 className="text-2xl font-bold text-white">Sales Intelligence Tracker</h1>
          <p className="text-sm text-blue-100 mt-1">
            Monitor IR pain points for outreach opportunities
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
        />

        {/* Main Content - Stacked Sections */}
        <main className="flex-1 p-6 overflow-auto">
          {isLoadingInit ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"></div>
                <p className="text-gray-500">Loading companies...</p>
              </div>
            </div>
          ) : (
            <>
              {/* Active Companies - Full Table */}
              <section className="bg-white rounded-lg border border-blue-100 shadow-sm mb-6">
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
                />
              </section>

              {/* Contacted Section - Collapsible */}
              <OutreachSection
                title="Contacted"
                items={contactedCompanies}
                onUndo={handleUndoContacted}
                colorScheme="green"
              />

              {/* Snoozed Section - Collapsible */}
              <OutreachSection
                title="Snoozed"
                items={snoozedCompanies}
                onUndo={handleUndoSnoozed}
                colorScheme="amber"
              />
            </>
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
