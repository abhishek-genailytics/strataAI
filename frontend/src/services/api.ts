import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { ApiResponse, ApiKey, RequestLog, UsageMetrics } from '../types';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.handleAuthError();
        }
        return Promise.reject(error);
      }
    );
  }

  private getAuthToken(): string | null {
    // Get token from Supabase auth or localStorage
    const supabaseAuth = localStorage.getItem('sb-' + process.env.REACT_APP_SUPABASE_URL?.split('//')[1]?.split('.')[0] + '-auth-token');
    if (supabaseAuth) {
      try {
        const parsed = JSON.parse(supabaseAuth);
        return parsed.access_token;
      } catch {
        return null;
      }
    }
    return null;
  }

  private handleAuthError() {
    // Clear auth data and redirect to login
    localStorage.clear();
    window.location.href = '/login';
  }

  private async handleResponse<T>(promise: Promise<AxiosResponse<T>>): Promise<ApiResponse<T>> {
    try {
      const response = await promise;
      return {
        data: response.data,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        return {
          error: error.response?.data?.message || error.message || 'An error occurred',
        };
      }
      return {
        error: 'An unexpected error occurred',
      };
    }
  }

  // API Key Management
  async getApiKeys(): Promise<ApiResponse<ApiKey[]>> {
    return this.handleResponse(this.api.get('/api-keys/'));
  }

  async createApiKey(data: {
    provider: string;
    key_name: string;
    api_key: string;
  }): Promise<ApiResponse<ApiKey>> {
    return this.handleResponse(this.api.post('/api-keys/', data));
  }

  async updateApiKey(id: string, data: {
    key_name?: string;
    api_key?: string;
  }): Promise<ApiResponse<ApiKey>> {
    return this.handleResponse(this.api.put(`/api-keys/${id}`, data));
  }

  async deleteApiKey(id: string): Promise<ApiResponse<void>> {
    return this.handleResponse(this.api.delete(`/api-keys/${id}`));
  }

  async validateApiKey(id: string): Promise<ApiResponse<{ valid: boolean }>> {
    return this.handleResponse(this.api.post(`/api-keys/${id}/validate`));
  }

  async revealApiKey(id: string): Promise<ApiResponse<{ api_key: string }>> {
    return this.handleResponse(this.api.get(`/api-keys/${id}/reveal`));
  }

  // Chat Completions
  async createChatCompletion(data: {
    model: string;
    messages: Array<{ role: string; content: string }>;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.post('/chat/completions', data));
  }

  async getModels(provider?: string): Promise<ApiResponse<string[]>> {
    const url = provider ? `/models/${provider}` : '/models';
    return this.handleResponse(this.api.get(url));
  }

  // Usage Analytics
  async getUsageMetrics(params?: {
    start_date?: string;
    end_date?: string;
    provider?: string;
    project_id?: string;
  }): Promise<ApiResponse<UsageMetrics>> {
    return this.handleResponse(this.api.get('/analytics/usage-metrics', { params }));
  }

  async getUsageSummary(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get('/analytics/usage-summary', { params }));
  }

  async getUsageTrends(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: string;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get('/analytics/usage-trends', { params }));
  }

  async getCurrentUsage(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get('/analytics/current-usage'));
  }

  async getApiRequests(params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResponse<RequestLog[]>> {
    return this.handleResponse(this.api.get('/analytics/api-requests', { params }));
  }

  async getFailedRequests(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<RequestLog[]>> {
    return this.handleResponse(this.api.get('/analytics/failed-requests', { params }));
  }

  async getCostAnalysis(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: string;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get('/analytics/cost-analysis', { params }));
  }

  // Cache Management
  async getCacheStats(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get('/system/cache/stats'));
  }

  async clearCache(): Promise<ApiResponse<void>> {
    return this.handleResponse(this.api.delete('/system/cache/clear'));
  }

  async clearUserCache(userId: string): Promise<ApiResponse<void>> {
    return this.handleResponse(this.api.delete(`/system/cache/user/${userId}`));
  }

  async getRateLimitStatus(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get('/system/rate-limit/status'));
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.handleResponse(this.api.get('/health'));
  }
}

export const apiService = new ApiService();
