import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Filter, MoreVertical, Code, Download, Maximize2 } from "lucide-react";
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
} from "recharts";

interface MetricData {
  time: string;
  [key: string]: string | number;
}

// Color mapping for different models
const colors = {
  "openai-main/gpt-4o": "#3b82f6",
  "gw-test-anthropic/claude-3-7-sonnet-20250219": "#10b981",
  "openai-fake-provider/gpt-4": "#f59e0b",
  "internal-google/gemini-2-0-flash": "#ef4444",
  "openai-fake-provider/gpt-3-5": "#06b6d4",
  "openai-fake-provider/gpt-3-5-turbo": "#8b5cf6",
  "openai-fake-provider/o4-mini": "#84cc16",
  "openai-main/gpt-4o-2024-11-20": "#f97316",
  "openai-main/gpt-4o-mini": "#ec4899",
  "llm-gateway-test-openai/openai-0": "#6366f1",
  "openai-main/o4-mini": "#14b8a6",
};

const metricData: MetricData[] = [
  {
    time: "08:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 0,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
  {
    time: "09:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 50000,
    "openai-fake-provider/gpt-3-5": 10000,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
  {
    time: "10:00",
    "openai-main/gpt-4o": 1100000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 300000,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 10000,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
];

const outputData: MetricData[] = [
  {
    time: "08:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 0,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
  {
    time: "09:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 2000,
    "openai-fake-provider/gpt-3-5": 500,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
  {
    time: "10:00",
    "openai-main/gpt-4o": 9000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 1500,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 500,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
];

const costData: MetricData[] = [
  {
    time: "08:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 0,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
  {
    time: "09:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 0,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0,
  },
  {
    time: "10:00",
    "openai-main/gpt-4o": 0,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 0,
    "openai-fake-provider/gpt-4": 0,
    "internal-google/gemini-2-0-flash": 0,
    "openai-fake-provider/gpt-3-5": 0,
    "openai-fake-provider/gpt-3-5-turbo": 0,
    "openai-fake-provider/o4-mini": 0,
    "openai-main/gpt-4o-2024-11-20": 0,
    "openai-main/gpt-4o-mini": 0,
    "llm-gateway-test-openai/openai-0": 0,
    "openai-main/o4-mini": 0.13,
  },
];

const latencyData: MetricData[] = [
  {
    time: "08:00",
    "openai-main/gpt-4o": 5000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 3000,
    "openai-fake-provider/gpt-4": 2000,
    "internal-google/gemini-2-0-flash": 1500,
    "openai-fake-provider/gpt-3-5": 1000,
    "openai-fake-provider/gpt-3-5-turbo": 1200,
    "openai-fake-provider/o4-mini": 800,
    "openai-main/gpt-4o-2024-11-20": 4000,
    "openai-main/gpt-4o-mini": 2500,
    "llm-gateway-test-openai/openai-0": 1800,
    "openai-main/o4-mini": 2000,
  },
  {
    time: "09:00",
    "openai-main/gpt-4o": 8000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 5000,
    "openai-fake-provider/gpt-4": 3500,
    "internal-google/gemini-2-0-flash": 2500,
    "openai-fake-provider/gpt-3-5": 2000,
    "openai-fake-provider/gpt-3-5-turbo": 2200,
    "openai-fake-provider/o4-mini": 1500,
    "openai-main/gpt-4o-2024-11-20": 6000,
    "openai-main/gpt-4o-mini": 4000,
    "llm-gateway-test-openai/openai-0": 3000,
    "openai-main/o4-mini": 3500,
  },
  {
    time: "10:00",
    "openai-main/gpt-4o": 40000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 25000,
    "openai-fake-provider/gpt-4": 15000,
    "internal-google/gemini-2-0-flash": 12000,
    "openai-fake-provider/gpt-3-5": 8000,
    "openai-fake-provider/gpt-3-5-turbo": 10000,
    "openai-fake-provider/o4-mini": 6000,
    "openai-main/gpt-4o-2024-11-20": 35000,
    "openai-main/gpt-4o-mini": 20000,
    "llm-gateway-test-openai/openai-0": 15000,
    "openai-main/o4-mini": 18000,
  },
];

const timeToFirstTokenData: MetricData[] = [
  {
    time: "08:00",
    "openai-main/gpt-4o": 2000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 1500,
    "openai-fake-provider/gpt-4": 1000,
    "internal-google/gemini-2-0-flash": 800,
    "openai-fake-provider/gpt-3-5": 600,
    "openai-fake-provider/gpt-3-5-turbo": 700,
    "openai-fake-provider/o4-mini": 500,
    "openai-main/gpt-4o-2024-11-20": 2500,
    "openai-main/gpt-4o-mini": 1800,
    "llm-gateway-test-openai/openai-0": 1200,
    "openai-main/o4-mini": 1400,
  },
  {
    time: "09:00",
    "openai-main/gpt-4o": 3000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 2000,
    "openai-fake-provider/gpt-4": 1500,
    "internal-google/gemini-2-0-flash": 1200,
    "openai-fake-provider/gpt-3-5": 1000,
    "openai-fake-provider/gpt-3-5-turbo": 1100,
    "openai-fake-provider/o4-mini": 800,
    "openai-main/gpt-4o-2024-11-20": 4000,
    "openai-main/gpt-4o-mini": 2500,
    "llm-gateway-test-openai/openai-0": 1800,
    "openai-main/o4-mini": 2000,
  },
  {
    time: "10:00",
    "openai-main/gpt-4o": 11000,
    "gw-test-anthropic/claude-3-7-sonnet-20250219": 8000,
    "openai-fake-provider/gpt-4": 5000,
    "internal-google/gemini-2-0-flash": 4000,
    "openai-fake-provider/gpt-3-5": 3000,
    "openai-fake-provider/gpt-3-5-turbo": 3500,
    "openai-fake-provider/o4-mini": 2500,
    "openai-main/gpt-4o-2024-11-20": 9000,
    "openai-main/gpt-4o-mini": 6000,
    "llm-gateway-test-openai/openai-0": 4500,
    "openai-main/o4-mini": 5000,
  },
];

const interTokenLatencyData = [
  { time: "08:00", P99: 350, P90: 300, P50: 250 },
  { time: "09:00", P99: 380, P90: 320, P50: 270 },
  { time: "10:00", P99: 420, P90: 350, P50: 290 },
];

const requestsPerSecondData = [
  { time: "08:00", value: 10 },
  { time: "09:00", value: 11 },
  { time: "10:00", value: 12 },
];

// Helper function to sum all values across all models for a specific field
const sumFieldValues = (data: MetricData[], field: string): number => {
  return data.reduce((sum, item) => {
    return (
      sum +
      Object.entries(item).reduce((modelSum, [key, value]) => {
        return (
          modelSum + (key !== "time" && key !== field ? (value as number) : 0)
        );
      }, 0)
    );
  }, 0);
};

// Helper to format large numbers
const formatLargeNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(2)}M`;
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
};

// Helper to format currency
const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 5,
  }).format(amount);
};

// Helper to get data filtered by percentile
const filterDataByPercentile = (data: any[], percentile: number): any[] => {
  return data.map((item) => {
    const filteredItem = { ...item };
    Object.keys(filteredItem).forEach((key) => {
      if (key !== "time" && Array.isArray(filteredItem[key])) {
        // Sort the array and get the value at the requested percentile
        const sortedValues = [...filteredItem[key]].sort((a, b) => a - b);
        const index = Math.ceil((percentile / 100) * sortedValues.length) - 1;
        filteredItem[key] = sortedValues[Math.max(0, index)] || 0;
      }
    });
    return filteredItem;
  });
};

// Tab content components
interface ModelsTabProps {
  metricData: MetricData[];
  latencyData: MetricData[];
  selectedPercentile: number;
  setSelectedPercentile: (value: number) => void;
}

const ModelsTab = ({
  metricData,
  latencyData,
  selectedPercentile,
  setSelectedPercentile,
}: ModelsTabProps) => {
  // Helper function to safely sum numeric values from an object
  const sumNumericValues = (obj: Record<string, any>): number => {
    return Object.values(obj).reduce((sum: number, val) => {
      return typeof val === "number" ? sum + val : sum;
    }, 0);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Input Tokens
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatLargeNumber(
              metricData.reduce((sum, item) => sum + sumNumericValues(item), 0)
            )}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Output Tokens
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatLargeNumber(
              latencyData.reduce((sum, item) => sum + sumNumericValues(item), 0)
            )}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Count of Requests
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatLargeNumber(metricData.length * 3)}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Cost of Tokens
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(
              metricData.length * 0.05 + latencyData.length * 0.03
            )}
          </p>
        </div>
      </div>
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">Model Performance</h2>
        <p className="text-gray-600">
          Model-specific metrics and charts will be displayed here.
        </p>
      </div>
    </div>
  );
};

const UsersTab = () => (
  <div className="bg-white p-6 rounded-lg border border-gray-200">
    <h2 className="text-lg font-semibold mb-4">User Analytics</h2>
    <p className="text-gray-600">
      User-specific metrics and analytics will be displayed here.
    </p>
  </div>
);

const TeamsTab = () => (
  <div className="bg-white p-6 rounded-lg border border-gray-200">
    <h2 className="text-lg font-semibold mb-4">Team Performance</h2>
    <p className="text-gray-600">
      Team-based metrics and analytics will be displayed here.
    </p>
  </div>
);

const ConfigTab = () => (
  <div className="bg-white p-6 rounded-lg border border-gray-200">
    <h2 className="text-lg font-semibold mb-4">Monitor Configuration</h2>
    <p className="text-gray-600">
      Monitoring settings and configuration options will be displayed here.
    </p>
  </div>
);

const TABS = [
  { id: "models", name: "Models" },
  { id: "users", name: "Users" },
  { id: "teams", name: "Teams" },
  { id: "config", name: "Config" },
] as const;

export default function Monitor() {
  const navigate = useNavigate();
  const [selectedMetric, setSelectedMetric] = useState("latency");
  const [selectedProvider, setSelectedProvider] = useState("all");
  const [activeTab, setActiveTab] = useState<string>("models");
  const [selectedPercentile, setSelectedPercentile] = useState<number>(90);
  const [timeRange, setTimeRange] = useState("Last 3 hours");

  // Apply percentile filter to latency-related data
  const filteredLatencyData = filterDataByPercentile(
    latencyData,
    selectedPercentile
  );
  const filteredTimeToFirstTokenData = filterDataByPercentile(
    timeToFirstTokenData,
    selectedPercentile
  );
  const filteredInterTokenLatencyData = filterDataByPercentile(
    interTokenLatencyData,
    selectedPercentile
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <button
            type="button"
            className="text-gray-500 hover:text-gray-700"
            onClick={() => navigate(-1)}
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
              />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Monitor</h1>
        </div>

        <div className="flex items-center space-x-4">
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Filter className="w-4 h-4" />
            <span>Filter</span>
          </button>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option>Last 3 hours</option>
            <option>Last 24 hours</option>
            <option>Last 7 days</option>
          </select>
          <button className="text-gray-400 hover:text-gray-600">
            <MoreVertical className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Sample Data Banner */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-red-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-800">
              ▲ You are viewing Sample Data
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
              activeTab === tab.id
                ? "bg-white border-t border-l border-r border-gray-200 text-blue-600 border-b-2 border-b-blue-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === "models" && (
          <ModelsTab
            metricData={metricData}
            latencyData={latencyData}
            selectedPercentile={selectedPercentile}
            setSelectedPercentile={setSelectedPercentile}
          />
        )}
        {activeTab === "users" && <UsersTab />}
        {activeTab === "teams" && <TeamsTab />}
        {activeTab === "config" && <ConfigTab />}

        {!["models", "users", "teams", "config"].includes(activeTab) && (
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">Select a View</h2>
            <p className="text-gray-600">
              Please select a view from the tabs above to see the relevant
              metrics.
            </p>
          </div>
        )}
      </div>

      {/* Models Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Input Tokens
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatLargeNumber(sumFieldValues(metricData, "time"))}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Output Tokens
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatLargeNumber(sumFieldValues(outputData, "time"))}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Count of Requests
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatLargeNumber(metricData.length * 3)}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            Total Cost of Tokens
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(
              sumFieldValues(metricData, "time") * 0.00002 +
                sumFieldValues(outputData, "time") * 0.00003
            )}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="space-y-8">
        {/* Input Tokens Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Input Tokens (tokens)
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metricData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              {Object.keys(colors).map((key) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[key as keyof typeof colors]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Output Tokens Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Output Tokens (tokens)
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={outputData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              {Object.keys(colors).map((key) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[key as keyof typeof colors]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cost Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Cost of Inference ($)
            </h3>
            <div className="flex items-center space-x-2">
              <button className="text-gray-400 hover:text-gray-600">
                <Code className="w-4 h-4" />
              </button>
              <button className="text-gray-400 hover:text-gray-600">
                <Download className="w-4 h-4" />
              </button>
              <button className="text-gray-400 hover:text-gray-600">
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              {Object.keys(colors).map((key) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[key as keyof typeof colors]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Request Latency Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Request Latency (milliseconds)
            </h3>
            <div className="flex space-x-1">
              {["P99", "P90", "P50"].map((percentile) => {
                const percentileValue = parseInt(percentile.slice(1));
                return (
                  <button
                    key={percentile}
                    onClick={() => setSelectedPercentile(percentileValue)}
                    className={`px-3 py-1 text-sm rounded ${
                      selectedPercentile === percentileValue
                        ? "bg-blue-600 text-white"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`}
                  >
                    {percentile}
                  </button>
                );
              })}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={filteredLatencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              {Object.keys(colors).map((key) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[key as keyof typeof colors]}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Time to First Token Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Time to First Token (milliseconds)
            </h3>
            <div className="flex space-x-1">
              {["P99", "P90", "P50"].map((percentile) => {
                const percentileValue = parseInt(percentile.slice(1));
                return (
                  <button
                    key={percentile}
                    onClick={() => setSelectedPercentile(percentileValue)}
                    className={`px-3 py-1 text-sm rounded ${
                      selectedPercentile === percentileValue
                        ? "bg-blue-600 text-white"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`}
                  >
                    {percentile}
                  </button>
                );
              })}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={filteredTimeToFirstTokenData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              {Object.keys(colors).map((key) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[key as keyof typeof colors]}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Inter Token Latency Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Inter Token Latency (milliseconds)
            </h3>
            <div className="flex space-x-1">
              {["P99", "P90", "P50"].map((percentile) => {
                const percentileValue = percentile;
                return (
                  <button
                    key={percentile}
                    onClick={() =>
                      setSelectedPercentile(parseInt(percentile.slice(1)))
                    }
                    className={`px-3 py-1 text-sm rounded ${
                      selectedPercentile === parseInt(percentile.slice(1))
                        ? "bg-blue-600 text-white"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`}
                  >
                    {percentile}
                  </button>
                );
              })}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={interTokenLatencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey={
                  selectedPercentile === 99
                    ? "P99"
                    : selectedPercentile === 90
                    ? "P90"
                    : "P50"
                }
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Requests Per Second Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Requests Per Second (requests/second)
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={requestsPerSecondData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#10b981"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
