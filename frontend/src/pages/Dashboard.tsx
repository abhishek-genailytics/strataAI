import React from 'react';
import { Card } from '../components/ui/Card';

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome to your StrataAI dashboard
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <Card title="API Usage">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">0</div>
            <div className="text-sm text-gray-500">Requests today</div>
          </div>
        </Card>

        <Card title="Total Cost">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">$0.00</div>
            <div className="text-sm text-gray-500">This month</div>
          </div>
        </Card>

        <Card title="Active Keys">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">0</div>
            <div className="text-sm text-gray-500">API keys configured</div>
          </div>
        </Card>
      </div>

      <Card title="Recent Activity">
        <div className="text-center py-8">
          <p className="text-gray-500">No recent activity</p>
        </div>
      </Card>
    </div>
  );
};
