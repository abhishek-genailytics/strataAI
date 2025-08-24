import React from 'react';
import { MetricsOverviewProps } from '../../types';
import { Card } from '../ui';

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ summary, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </Card>
        ))}
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  const formatPercentage = (rate: number): string => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  const formatLatency = (ms: number): string => {
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {metrics.map((metric, index) => (
        <Card key={index} className="hover:shadow-lg transition-shadow duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">{metric.title}</p>
              <p className={`text-2xl font-bold ${metric.color}`}>{metric.value}</p>
            </div>
            <div className={`w-12 h-12 rounded-lg ${metric.bgColor} flex items-center justify-center text-xl`}>
              {metric.icon}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default MetricsOverview;
