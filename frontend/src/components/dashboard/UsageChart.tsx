import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { UsageChartProps } from '../../types';
import { Card } from '../ui';

const UsageChart: React.FC<UsageChartProps> = ({ data, loading = false, timeRange }) => {
  if (loading) {
    return (
      <Card title="Usage Trends" className="mb-8">
        <div className="h-80 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Usage Trends" className="mb-8">
        <div className="h-80 flex items-center justify-center text-gray-500">
          No usage data available for the selected time period
        </div>
      </Card>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    if (timeRange.days <= 7) {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } else if (timeRange.days <= 30) {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    }
  };

  const formatTooltipValue = (value: number, name: string) => {
    if (name === 'cost') return [`$${value.toFixed(2)}`, 'Cost'];
    if (name === 'latency') return [`${value.toFixed(0)}ms`, 'Avg Latency'];
    if (name === 'requests') return [value.toLocaleString(), 'Requests'];
    if (name === 'tokens') return [value.toLocaleString(), 'Tokens'];
    if (name === 'errors') return [value.toLocaleString(), 'Errors'];
    return [value, name];
  };

  const chartData = data.map(item => ({
    ...item,
    date: formatDate(item.date),
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {/* Requests and Errors Chart */}
      <Card title="Request Volume & Errors">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
            />
            <YAxis 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
            />
            <Tooltip 
              formatter={formatTooltipValue}
              labelStyle={{ color: '#374151' }}
              contentStyle={{ 
                backgroundColor: '#F9FAFB', 
                border: '1px solid #E5E7EB',
                borderRadius: '6px'
              }}
            />
            <Legend />
            <Bar dataKey="requests" fill="#3B82F6" name="Requests" />
            <Bar dataKey="errors" fill="#EF4444" name="Errors" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Cost and Latency Chart */}
      <Card title="Cost & Performance">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
            />
            <YAxis 
              yAxisId="cost"
              fontSize={12}
              tick={{ fill: '#6B7280' }}
              orientation="left"
            />
            <YAxis 
              yAxisId="latency"
              fontSize={12}
              tick={{ fill: '#6B7280' }}
              orientation="right"
            />
            <Tooltip 
              formatter={formatTooltipValue}
              labelStyle={{ color: '#374151' }}
              contentStyle={{ 
                backgroundColor: '#F9FAFB', 
                border: '1px solid #E5E7EB',
                borderRadius: '6px'
              }}
            />
            <Legend />
            <Line 
              yAxisId="cost"
              type="monotone" 
              dataKey="cost" 
              stroke="#10B981" 
              strokeWidth={2}
              name="Cost"
              dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
            />
            <Line 
              yAxisId="latency"
              type="monotone" 
              dataKey="latency" 
              stroke="#F59E0B" 
              strokeWidth={2}
              name="Latency"
              dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
};

export default UsageChart;
