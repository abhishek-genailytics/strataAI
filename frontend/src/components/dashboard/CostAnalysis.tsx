import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { CostAnalysisProps } from '../../types';
import { Card } from '../ui';

const CostAnalysis: React.FC<CostAnalysisProps> = ({ data, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </Card>
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <Card title="Cost Analysis" className="mb-8">
        <div className="h-64 flex items-center justify-center text-gray-500">
          No cost data available
        </div>
      </Card>
    );
  }

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  const formatCurrency = (value: number) => `$${value.toFixed(2)}`;
  
  const formatTooltipValue = (value: number, name: string) => {
    if (name === 'cost' || name === 'Cost') return [formatCurrency(value), 'Cost'];
    if (name === 'percentage') return [`${value.toFixed(1)}%`, 'Percentage'];
    return [value, name];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const costTrendsData = (data.daily_costs || data.cost_trends || []).map(item => ({
    ...item,
    date: formatDate(item.date),
  }));

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // Don't show labels for slices < 5%
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="space-y-6 mb-8">
      {/* Cost Overview */}
      <Card title={`Total Cost: ${formatCurrency(data.total_cost)}`}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost by Provider Pie Chart */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Cost by Provider</h4>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={data.cost_by_provider}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="cost"
                >
                  {data.cost_by_provider.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={formatTooltipValue} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Provider Cost Breakdown */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Provider Breakdown</h4>
            <div className="space-y-3">
              {data.cost_by_provider.map((provider, index) => (
                <div key={provider.provider} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full" 
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <span className="font-medium text-gray-700 capitalize">{provider.provider}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-gray-900">{formatCurrency(provider.cost)}</div>
                    <div className="text-sm text-gray-500">{provider.percentage.toFixed(1)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Cost by Model */}
      <Card title="Cost by Model">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.cost_by_model} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="model" 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
              tickFormatter={formatCurrency}
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
            <Bar dataKey="cost" fill="#3B82F6" name="Cost" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Cost Trends */}
      <Card title="Cost Trends Over Time">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={costTrendsData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
            />
            <YAxis 
              fontSize={12}
              tick={{ fill: '#6B7280' }}
              tickFormatter={formatCurrency}
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
            <Line 
              type="monotone" 
              dataKey="cost" 
              stroke="#10B981" 
              strokeWidth={3}
              name="Daily Cost"
              dot={{ fill: '#10B981', strokeWidth: 2, r: 5 }}
              activeDot={{ r: 7, stroke: '#10B981', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
};

export default CostAnalysis;
