import React from 'react';
import { MetricsOverviewProps } from '../../types';
import { Card } from '../ui';

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ summary, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              </div>
              <div className="w-10 h-10 lg:w-12 lg:h-12 bg-gray-200 rounded-lg flex-shrink-0 ml-3"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // Handle case where summary is undefined
  if (!summary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <Card className="col-span-full p-6">
          <p className="text-gray-500 text-center">No data available</p>
        </Card>
      </div>
    );
  }

  const formatNumber = (num: number | undefined | null): string => {
    if (num == null) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatCurrency = (amount: number | undefined | null): string => {
    if (amount == null) return '$0.00';
    return `$${amount.toFixed(2)}`;
  };

  const formatPercentage = (rate: number | undefined | null): string => {
    if (rate == null) return '0.0%';
    return `${(rate * 100).toFixed(1)}%`;
  };

  const formatLatency = (ms: number | undefined | null): string => {
    if (ms == null) return '0ms';
    return `${ms.toFixed(0)}ms`;
  };

  const metrics = [
    {
      title: 'Total Requests',
      value: formatNumber(summary.total_requests),
      icon: '📊',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Total Cost',
      value: formatCurrency(summary.total_cost),
      icon: '💰',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Success Rate',
      value: formatPercentage(summary.success_rate),
      icon: '✅',
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      title: 'Avg Latency',
      value: formatLatency(summary.average_latency),
      icon: '⚡',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
      {metrics.map((metric, index) => (
        <Card key={index} className="hover:shadow-lg transition-shadow duration-200 p-6">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-600 mb-1 truncate">{metric.title}</p>
              <p className={`text-xl lg:text-2xl font-bold ${metric.color} truncate`}>{metric.value}</p>
            </div>
            <div className={`w-10 h-10 lg:w-12 lg:h-12 rounded-lg ${metric.bgColor} flex items-center justify-center text-lg lg:text-xl flex-shrink-0 ml-3`}>
              {metric.icon}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default MetricsOverview;
