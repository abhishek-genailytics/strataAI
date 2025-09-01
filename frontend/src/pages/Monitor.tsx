import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Filter,
  MoreVertical,
  Code,
  Download,
  Maximize2,
  AlertTriangle,
  TrendingUp,
  Clock,
  DollarSign,
  Activity,
  RotateCcw,
} from "lucide-react";
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
  Area,
  AreaChart,
} from "recharts";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

// Sample data with more realistic values
const metricData = [
  {
    time: "08:00",
    "gpt-4o": 0,
    "claude-3-sonnet": 0,
    "gpt-4": 0,
    "gemini-2": 0,
    "gpt-3.5": 0,
  },
  {
    time: "08:30",
    "gpt-4o": 150000,
    "claude-3-sonnet": 80000,
    "gpt-4": 45000,
    "gemini-2": 120000,
    "gpt-3.5": 200000,
  },
  {
    time: "09:00",
    "gpt-4o": 320000,
    "claude-3-sonnet": 180000,
    "gpt-4": 90000,
    "gemini-2": 250000,
    "gpt-3.5": 450000,
  },
  {
    time: "09:30",
    "gpt-4o": 780000,
    "claude-3-sonnet": 420000,
    "gpt-4": 180000,
    "gemini-2": 580000,
    "gpt-3.5": 890000,
  },
  {
    time: "10:00",
    "gpt-4o": 1200000,
    "claude-3-sonnet": 650000,
    "gpt-4": 280000,
    "gemini-2": 850000,
    "gpt-3.5": 1100000,
  },
];

const outputData = [
  {
    time: "08:00",
    "gpt-4o": 0,
    "claude-3-sonnet": 0,
    "gpt-4": 0,
    "gemini-2": 0,
    "gpt-3.5": 0,
  },
  {
    time: "08:30",
    "gpt-4o": 2500,
    "claude-3-sonnet": 1800,
    "gpt-4": 1200,
    "gemini-2": 2000,
    "gpt-3.5": 3200,
  },
  {
    time: "09:00",
    "gpt-4o": 5800,
    "claude-3-sonnet": 4200,
    "gpt-4": 2800,
    "gemini-2": 4800,
    "gpt-3.5": 7200,
  },
  {
    time: "09:30",
    "gpt-4o": 8900,
    "claude-3-sonnet": 6500,
    "gpt-4": 4200,
    "gemini-2": 7200,
    "gpt-3.5": 10500,
  },
  {
    time: "10:00",
    "gpt-4o": 12139,
    "claude-3-sonnet": 8500,
    "gpt-4": 5800,
    "gemini-2": 9200,
    "gpt-3.5": 13800,
  },
];

const latencyData = [
  { time: "08:00", P99: 1200, P90: 850, P50: 420 },
  { time: "08:30", P99: 1850, P90: 1200, P50: 680 },
  { time: "09:00", P99: 3200, P90: 2100, P50: 980 },
  { time: "09:30", P99: 4800, P90: 3200, P50: 1450 },
  { time: "10:00", P99: 6500, P90: 4200, P50: 1980 },
];

const requestsData = [
  { time: "08:00", value: 8 },
  { time: "08:30", value: 9 },
  { time: "09:00", value: 11 },
  { time: "09:30", value: 12 },
  { time: "10:00", value: 14 },
];

const modelColors = {
  "gpt-4o": "#3b82f6",
  "claude-3-sonnet": "#10b981",
  "gpt-4": "#f59e0b",
  "gemini-2": "#ef4444",
  "gpt-3.5": "#8b5cf6",
  P99: "#dc2626",
  P90: "#ea580c",
  P50: "#65a30d",
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(amount);
};

export default function Monitor() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("models");
  const [selectedPercentile, setSelectedPercentile] = useState("P99");
  const [timeRange, setTimeRange] = useState("Last 3 hours");
  const [showFilter, setShowFilter] = useState(false);

  const tabs = [
    { id: "models", name: "Models", icon: Activity },
    { id: "users", name: "Users", icon: Activity },
    { id: "teams", name: "Teams", icon: Activity },
    { id: "config", name: "Config", icon: Activity },
  ];

  const metricCards = [
    {
      title: "Total Input Tokens",
      value: "1.26",
      unit: "Million",
      icon: TrendingUp,
      color: "blue",
      change: "+12.5%",
    },
    {
      title: "Total Output Tokens",
      value: "12,139",
      unit: "",
      icon: Activity,
      color: "green",
      change: "+8.2%",
    },
    {
      title: "Total Count of Requests",
      value: "0.11",
      unit: "Million",
      icon: Clock,
      color: "purple",
      change: "+15.7%",
    },
    {
      title: "Total Cost of Tokens",
      value: "0.128",
      unit: "USD",
      icon: DollarSign,
      color: "orange",
      change: "+5.4%",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="p-6 lg:p-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(-1)}
              className="text-slate-500 hover:text-slate-700 transition-colors"
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
            <h1 className="text-2xl font-bold text-slate-900">Monitor</h1>
          </div>

          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilter(!showFilter)}
              className="border-slate-300 text-slate-700 hover:border-slate-400 bg-white/60"
            >
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </Button>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white/60 text-sm"
            >
              <option>Last 3 hours</option>
              <option>Last 24 hours</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
            </select>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-slate-600"
            >
              <MoreVertical className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Sample Data Warning */}
        <div className="mb-6">
          <Card className="bg-gradient-to-r from-red-50 to-orange-50 border-red-200 border">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-red-800">
                    ▲ You are viewing Sample Data
                  </p>
                  <button className="text-red-500 hover:text-red-700">
                    <span className="sr-only">Dismiss</span>✕
                  </button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 border-b border-slate-200 mb-8 bg-white/60 p-1 rounded-xl">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-6 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                activeTab === tab.id
                  ? "bg-white text-blue-600 shadow-md border border-blue-200"
                  : "text-slate-600 hover:text-slate-900 hover:bg-white/40"
              }`}
            >
              <tab.icon className="w-4 h-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </div>

        {/* Metrics Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {metricCards.map((metric, index) => (
            <Card
              key={index}
              className="bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-shadow duration-300"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-600 mb-1">
                    {metric.title}
                  </p>
                  <div className="flex items-baseline space-x-1">
                    <p className="text-2xl font-bold text-slate-900">
                      {metric.value}
                    </p>
                    {metric.unit && (
                      <span className="text-sm text-slate-500 font-medium">
                        {metric.unit}
                      </span>
                    )}
                  </div>
                  <div
                    className={`text-xs font-medium mt-1 ${
                      metric.change.startsWith("+")
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {metric.change} from last period
                  </div>
                </div>
                <div className={`p-3 rounded-xl bg-${metric.color}-50`}>
                  <metric.icon className={`w-6 h-6 text-${metric.color}-600`} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          {/* Request Latency Chart */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-900">
                Request Latency
                <span className="text-sm font-normal text-slate-500 ml-2">
                  (milliseconds)
                </span>
              </h3>
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  {["P99", "P90", "P50"].map((percentile) => (
                    <button
                      key={percentile}
                      onClick={() => setSelectedPercentile(percentile)}
                      className={`px-3 py-1 text-sm rounded-lg transition-all duration-200 ${
                        selectedPercentile === percentile
                          ? "bg-blue-600 text-white shadow-md"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      {percentile}
                    </button>
                  ))}
                </div>
                <div className="flex items-center space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <Code className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={latencyData}>
                <defs>
                  <linearGradient
                    id="latencyGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  tickLine={{ stroke: "#cbd5e1" }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  tickLine={{ stroke: "#cbd5e1" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey={selectedPercentile}
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#latencyGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          {/* Time to First Token */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-900">
                Time to First Token
                <span className="text-sm font-normal text-slate-500 ml-2">
                  (milliseconds)
                </span>
              </h3>
              <div className="flex space-x-1">
                {["P99", "P90", "P50"].map((percentile) => (
                  <button
                    key={percentile}
                    onClick={() => setSelectedPercentile(percentile)}
                    className={`px-3 py-1 text-sm rounded-lg transition-all duration-200 ${
                      selectedPercentile === percentile
                        ? "bg-purple-600 text-white shadow-md"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    }`}
                  >
                    {percentile}
                  </button>
                ))}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: "#64748b" }}
                />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey={selectedPercentile}
                  stroke="#8b5cf6"
                  strokeWidth={3}
                  dot={{ fill: "#8b5cf6", strokeWidth: 2, r: 5 }}
                  activeDot={{ r: 7, stroke: "#8b5cf6", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Input Tokens Chart */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg xl:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-900">
                Input Tokens
                <span className="text-sm font-normal text-slate-500 ml-2">
                  (tokens)
                </span>
              </h3>
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-slate-400 hover:text-slate-600"
                >
                  <Code className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-slate-400 hover:text-slate-600"
                >
                  <Download className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-slate-400 hover:text-slate-600"
                >
                  <Maximize2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={metricData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  tickLine={{ stroke: "#cbd5e1" }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  tickFormatter={formatNumber}
                  tickLine={{ stroke: "#cbd5e1" }}
                />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    formatNumber(value),
                    name,
                  ]}
                  labelStyle={{ color: "#334155", fontWeight: 500 }}
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Legend wrapperStyle={{ paddingTop: "20px" }} />
                {Object.entries(modelColors)
                  .slice(0, 5)
                  .map(([model, color]) => (
                    <Bar
                      key={model}
                      dataKey={model}
                      fill={color}
                      name={model}
                      radius={[2, 2, 0, 0]}
                    />
                  ))}
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Output Tokens Chart */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg xl:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-900">
                Output Tokens
                <span className="text-sm font-normal text-slate-500 ml-2">
                  (tokens)
                </span>
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={outputData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  tickLine={{ stroke: "#cbd5e1" }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  tickFormatter={formatNumber}
                  tickLine={{ stroke: "#cbd5e1" }}
                />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    formatNumber(value),
                    name,
                  ]}
                  labelStyle={{ color: "#334155", fontWeight: 500 }}
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Legend />
                {Object.entries(modelColors)
                  .slice(0, 5)
                  .map(([model, color]) => (
                    <Bar
                      key={model}
                      dataKey={model}
                      fill={color}
                      name={model}
                      radius={[2, 2, 0, 0]}
                    />
                  ))}
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Requests Per Second */}
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-900">
                Requests Per Second
                <span className="text-sm font-normal text-slate-500 ml-2">
                  (requests/second)
                </span>
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={requestsData}>
                <defs>
                  <linearGradient
                    id="requestsGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: "#64748b" }}
                />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  strokeWidth={3}
                  fill="url(#requestsGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Model Performance Summary */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-900">
              Model Performance Summary
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-slate-500">
                Last updated: 2 minutes ago
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="text-blue-600 hover:text-blue-800"
              >
                <RotateCcw className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {[
              {
                name: "gpt-4o",
                requests: "45.2K",
                latency: "1.2s",
                cost: "$2.85",
                status: "healthy",
              },
              {
                name: "claude-3-sonnet",
                requests: "32.1K",
                latency: "0.9s",
                cost: "$1.95",
                status: "healthy",
              },
              {
                name: "gpt-4",
                requests: "18.5K",
                latency: "1.8s",
                cost: "$4.20",
                status: "warning",
              },
              {
                name: "gemini-2",
                requests: "28.7K",
                latency: "1.1s",
                cost: "$1.65",
                status: "healthy",
              },
              {
                name: "gpt-3.5",
                requests: "67.3K",
                latency: "0.6s",
                cost: "$0.85",
                status: "healthy",
              },
            ].map((model) => (
              <div
                key={model.name}
                className="p-4 border border-slate-200 rounded-xl hover:border-slate-300 transition-colors bg-white/60"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-slate-900 text-sm">
                    {model.name}
                  </span>
                  <div
                    className={`w-2 h-2 rounded-full ${
                      model.status === "healthy"
                        ? "bg-green-500"
                        : "bg-yellow-500"
                    }`}
                  ></div>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Requests:</span>
                    <span className="font-medium text-slate-900">
                      {model.requests}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Latency:</span>
                    <span className="font-medium text-slate-900">
                      {model.latency}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Cost:</span>
                    <span className="font-medium text-slate-900">
                      {model.cost}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
