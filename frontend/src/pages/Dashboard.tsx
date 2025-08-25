import React, { useState, useEffect, useCallback } from 'react';
import { 
  UsageSummary, 
  UsageTrend, 
  CostAnalysis as CostAnalysisType, 
  TimeRange, 
  DashboardFilters 
} from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import MetricsOverview from '../components/dashboard/MetricsOverview';
import UsageChart from '../components/dashboard/UsageChart';
import CostAnalysis from '../components/dashboard/CostAnalysis';
import TimeRangeSelector from '../components/dashboard/TimeRangeSelector';
import ProviderFilter from '../components/dashboard/ProviderFilter';

const TIME_RANGE_OPTIONS: TimeRange[] = [
  { label: 'Last 24 Hours', value: '24h', days: 1 },
  { label: 'Last 7 Days', value: '7d', days: 7 },
  { label: 'Last 30 Days', value: '30d', days: 30 },
  { label: 'Last 90 Days', value: '90d', days: 90 },
];

export const Dashboard: React.FC = () => {
  const { currentOrganization } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilters>({
    timeRange: TIME_RANGE_OPTIONS[1], // Default to 7 days
  });

  // Data state
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [trends, setTrends] = useState<UsageTrend[]>([]);
  const [costAnalysis, setCostAnalysis] = useState<CostAnalysisType | null>(null);
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);

  const getDateRange = (timeRange: TimeRange) => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - timeRange.days);
    
    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
    };
  };

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const dateRange = getDateRange(filters.timeRange);
      const params = {
        ...dateRange,
        provider: filters.provider,
      };

      // Fetch all dashboard data in parallel
      const [
        summaryResponse,
        trendsResponse,
        costResponse,
      ] = await Promise.all([
        apiService.getUsageSummary(params),
        apiService.getUsageTrends({ ...params, group_by: 'day' }),
        apiService.getCostAnalysis({ ...params, group_by: 'provider' }),
      ]);

      if (summaryResponse.error) {
        throw new Error(summaryResponse.error);
      }
      if (trendsResponse.error) {
        throw new Error(trendsResponse.error);
      }
      if (costResponse.error) {
        throw new Error(costResponse.error);
      }

      setSummary(summaryResponse.data);
      setTrends(trendsResponse.data || []);
      setCostAnalysis(costResponse.data);

      // Extract available providers from summary data
      if (summaryResponse.data?.providers) {
        setAvailableProviders(Object.keys(summaryResponse.data.providers));
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]); // Refetch when organization changes

  const handleTimeRangeChange = (timeRange: TimeRange) => {
    setFilters(prev => ({ ...prev, timeRange }));
  };

  const handleProviderChange = (provider?: string) => {
    setFilters(prev => ({ ...prev, provider }));
  };

  const handleRefresh = () => {
    fetchDashboardData();
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Observability Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor your API usage, costs, and performance metrics
          </p>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={handleRefresh}
                  className="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-semibold text-gray-900">Observability Dashboard</h1>
          <div className="mt-2 space-y-1">
            <p className="text-sm text-gray-500">
              Monitor your API usage, costs, and performance metrics
            </p>
            {currentOrganization ? (
              <div className="flex items-center text-sm text-blue-600">
                <svg className="w-4 h-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <span className="truncate">Organization: {currentOrganization.display_name || currentOrganization.name}</span>
              </div>
            ) : (
              <div className="flex items-center text-sm text-gray-500">
                <svg className="w-4 h-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Personal Workspace
              </div>
            )}
          </div>
        </div>
        <div className="flex-shrink-0">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors duration-150"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                Loading...
              </>
            ) : (
              <>
                <span className="mr-2">🔄</span>
                Refresh
              </>
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <TimeRangeSelector
            value={filters.timeRange}
            onChange={handleTimeRangeChange}
            options={TIME_RANGE_OPTIONS}
          />
          <ProviderFilter
            value={filters.provider}
            onChange={handleProviderChange}
            providers={availableProviders}
          />
        </div>
      </div>

      {/* Metrics Overview */}
      <MetricsOverview summary={summary || undefined} loading={loading} />

      {/* Usage Charts */}
      <UsageChart 
        data={trends} 
        loading={loading} 
        timeRange={filters.timeRange} 
      />

      {/* Cost Analysis */}
      {costAnalysis && (
        <CostAnalysis data={costAnalysis} loading={loading} />
      )}

      {/* Empty State */}
      {!loading && (!summary || summary.total_requests === 0) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
          <div className="text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No data available</h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Start making API requests to see your usage analytics and cost breakdown.
            </p>
            <a
              href="/playground"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-150"
            >
              Try the Playground
            </a>
          </div>
        </div>
      )}
    </>
  );
};

export default Dashboard;
