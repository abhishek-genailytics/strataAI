// Organizations
export type Organization = { id: string; name: string };

// Users / Profile
export type Profile = {
  id: string;
  email: string;
  name?: string;
  role?: "owner" | "admin" | "member";
};

// Providers & Keys
export type Provider = { 
  id: string; 
  name: string; 
  display_name: string;
  logo_url?: string;
  website_url?: string;
  description?: string;
  base_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  configured?: boolean; // Added by frontend logic
};
export type ApiKey = {
  id: string;
  provider: string;
  label: string;
  created_at: string;
  last_used?: string | null;
};

// Models
export type ModelInfo = {
  id: string; // provider/model-id e.g., openai/gpt-4o
  provider: string;
  provider_display_name: string;
  provider_logo_url?: string;
  model_name: string;
  display_name: string;
  type: string; // 'chat', 'completion', etc.
  capabilities?: {
    supports_streaming?: boolean;
    supports_function_calling?: boolean;
    vision?: boolean;
    supports_audio?: boolean;
  };
  limits?: {
    max_input_tokens?: number;
    max_output_tokens?: number;
  };
  pricing?: {
    input?: { price: number; unit: string; currency: string };
    output?: { price: number; unit: string; currency: string };
  };
  availability?: {
    org_enabled: boolean;
    has_org_api_key: boolean;
    user_enabled: boolean;
    locked_reason?: string;
  };
  is_default_for_user?: boolean;
  metadata?: Record<string, any>;
  // Legacy fields for backward compatibility
  context_window?: number;
  output_limit?: number;
  enabled?: boolean;
};

// Playground sessions
export type ChatMessage = {
  id?: string;
  role: "system" | "user" | "assistant";
  content: string;
};
export type Session = {
  id: string;
  name: string;
  model: string;
  created_at: string;
  updated_at: string;
};
export type UsageSummary = {
  requests: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
};

// Analytics
export type BreakdownRow = {
  key: string;
  requests: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
};
export type ErrorRow = {
  timestamp: string;
  endpoint: string;
  status: number;
  provider?: string;
  model?: string;
  error: string;
};

// PATs
export type TokenRow = {
  id: string;
  name: string;
  scopes: string[];
  expires_at: string | null;
  last_used?: string | null;
};

export type SeriesPoint = {
  ts: string;
  requests: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
};
