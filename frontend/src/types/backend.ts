// Organizations
export type Organization = { id: string; name: string }

// Users / Profile
export type Profile = { id: string; email: string; name?: string; role?: 'owner'|'admin'|'member' }

// Providers & Keys
export type Provider = { id: string; name: string; configured: boolean }
export type ApiKey = { id: string; provider: string; label: string; created_at: string; last_used?: string | null }

// Models
export type ModelInfo = {
  id: string // provider/model-id e.g., openai/gpt-4o
  provider: string
  display_name: string
  type: 'chat'
  context_window: number
  output_limit?: number
  pricing?: { input_per_1k?: number; output_per_1k?: number; currency?: 'USD'|'INR' }
  capabilities?: { streaming?: boolean; tools?: boolean; vision?: boolean }
  enabled?: boolean
}

// Playground sessions
export type ChatMessage = { id?: string; role: 'system' | 'user' | 'assistant'; content: string }
export type Session = { id: string; name: string; model: string; created_at: string; updated_at: string }
export type UsageSummary = { requests: number; input_tokens: number; output_tokens: number; cost_usd: number }

// Analytics
export type BreakdownRow = { key: string; requests: number; input_tokens: number; output_tokens: number; cost_usd: number }
export type ErrorRow = { timestamp: string; endpoint: string; status: number; provider?: string; model?: string; error: string }

// PATs
export type TokenRow = { id: string; name: string; scopes: string[]; expires_at: string | null; last_used?: string | null }

export type SeriesPoint = {
  ts: string
  requests: number
  input_tokens: number
  output_tokens: number
  cost_usd: number
}
