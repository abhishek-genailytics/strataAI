// Common types used throughout the application

export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
  user_metadata?: {
    display_name?: string;
    full_name?: string;
    [key: string]: any;
  };
}

export interface Organization {
  id: string;
  name: string;
  display_name?: string;
  domain?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserOrganization {
  id: string;
  user_id: string;
  organization_id: string;
  role: "admin" | "member";
  is_active: boolean;
  created_at: string;
  updated_at: string;
  organization: Organization;
}

export interface AuthState {
  user: User | null;
  organizations: UserOrganization[];
  currentOrganization: Organization | null;
  loading: boolean;
  error: string | null;
}

// Enhanced AI Provider types
export interface AIProvider {
  id: string;
  name: string;
  display_name: string;
  base_url: string;
  logo_url?: string;
  website_url?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AIModel {
  id: string;
  provider_id: string;
  model_name: string;
  display_name: string;
  description?: string;
  model_type:
    | "chat"
    | "completion"
    | "embedding"
    | "image"
    | "audio"
    | "multimodal";
  max_tokens?: number;
  max_input_tokens?: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
  supports_vision: boolean;
  supports_audio: boolean;
  capabilities: Record<string, any>;
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModelPricing {
  id: string;
  model_id: string;
  pricing_type: "input" | "output" | "per_request" | "per_second";
  price_per_unit: number;
  unit: "token" | "request" | "second" | "minute";
  currency: string;
  region: string;
  effective_from: string;
  effective_until?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderCapability {
  id: string;
  provider_id: string;
  capability_name: string;
  capability_value?: Record<string, any>;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AIModelWithPricing extends AIModel {
  pricing: ModelPricing[];
}

export interface ApiKey {
  id: string;
  user_id: string;
  provider: "openai" | "anthropic" | "google";
  key_name: string;
  masked_key: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface RequestLog {
  id: string;
  user_id: string;
  provider: string;
  model: string;
  endpoint: string;
  tokens_used: number;
  cost: number;
  latency: number;
  status: "success" | "error";
  created_at: string;
}

export interface UsageMetrics {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  average_latency: number;
  success_rate: number;
}

// Component prop types
export interface ButtonProps {
  children: any;
  variant?: "primary" | "secondary" | "danger" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  className?: string;
}

export interface InputProps {
  label?: string;
  placeholder?: string;
  type?: "text" | "email" | "password" | "number";
  value?: string;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: any;
  size?: "sm" | "md" | "lg" | "xl";
}

export interface CardProps {
  children: any;
  title?: string;
  className?: string;
  padding?: boolean;
  onClick?: () => void;
}

// Playground types
export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
  name?: string;
}

export interface PlaygroundRequest {
  messages: ChatMessage[];
  model: string;
  provider?: string;
  project_id: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stop?: string | string[];
  stream?: boolean;
}

export interface ChatCompletionUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatCompletionChoice {
  index: number;
  message: ChatMessage;
  finish_reason?: string;
}

export interface PlaygroundResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  provider: string;
  choices: ChatCompletionChoice[];
  usage: ChatCompletionUsage;
  request_id?: string;
  processing_time_ms?: number;
}

export interface ProviderModelInfo {
  provider: string;
  model: string;
  display_name: string;
  max_tokens: number;
  supports_streaming: boolean;
  cost_per_1k_input_tokens: number;
  cost_per_1k_output_tokens: number;
}

export interface RequestHistoryItem {
  id: string;
  timestamp: string;
  request: PlaygroundRequest;
  response?: PlaygroundResponse;
  error?: string;
  cost?: number;
  duration?: number;
}

export interface PlaygroundState {
  selectedModel: string;
  messages: ChatMessage[];
  parameters: {
    temperature: number;
    max_tokens: number;
    top_p: number;
    frequency_penalty: number;
    presence_penalty: number;
    stop: string[];
  };
  isLoading: boolean;
  response?: PlaygroundResponse;
  error?: string;
}

// Dashboard Analytics Types
export interface UsageSummary {
  total_requests?: number;
  total_tokens?: number;
  total_cost?: number;
  average_latency?: number;
  success_rate?: number;
  failed_requests?: number;
  unique_users?: number;
  providers?: {
    [key: string]: {
      requests: number;
      tokens: number;
      cost: number;
    };
  };
}

export interface UsageTrend {
  date: string;
  requests: number;
  tokens: number;
  cost: number;
  latency: number;
  errors: number;
  provider?: string;
}

export interface CostAnalysis {
  total_cost: number;
  cost_by_provider: {
    provider: string;
    cost: number;
    percentage: number;
  }[];
  cost_by_model: {
    model: string;
    provider: string;
    cost: number;
    requests: number;
  }[];
  cost_trends: {
    date: string;
    cost: number;
    provider?: string;
  }[];
  daily_costs: {
    date: string;
    cost: number;
    provider?: string;
  }[];
}

export interface ProviderMetrics {
  provider: string;
  total_requests: number;
  success_rate: number;
  average_latency: number;
  total_cost: number;
  error_rate: number;
  most_used_model: string;
}

export interface TimeRange {
  label: string;
  value: string;
  days: number;
}

export interface DashboardFilters {
  timeRange: TimeRange;
  provider?: string;
  startDate?: string;
  endDate?: string;
}

export interface DashboardData {
  summary: UsageSummary;
  trends: UsageTrend[];
  costAnalysis: CostAnalysis;
  providerMetrics: ProviderMetrics[];
  recentRequests: RequestLog[];
  failedRequests: RequestLog[];
}

// Dashboard Component Props
export interface MetricsOverviewProps {
  summary?: UsageSummary;
  loading?: boolean;
}

export interface UsageChartProps {
  data: UsageTrend[];
  loading?: boolean;
  timeRange: TimeRange;
}

export interface CostAnalysisProps {
  data: CostAnalysis;
  loading?: boolean;
}

export interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
  options: TimeRange[];
}

export interface ProviderFilterProps {
  value?: string;
  onChange: (provider?: string) => void;
  providers: string[];
}
