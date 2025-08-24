// Common types used throughout the application

export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export interface ApiKey {
  id: string;
  user_id: string;
  provider: 'openai' | 'anthropic' | 'google';
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
  status: 'success' | 'error';
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
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export interface InputProps {
  label?: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number';
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  padding?: boolean;
}
