import axios, { AxiosInstance, AxiosResponse, AxiosError } from "axios";
import {
  RequestLog,
  UsageMetrics,
  ApiResponse,
  PlaygroundRequest,
  PlaygroundResponse,
  ProviderModelInfo,
  UserOrganization,
} from "../types";
import { errorLoggingService } from "./errorLoggingService";

class ApiService {
  private api: AxiosInstance;
  private organizationId: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL:
        (process.env.REACT_APP_API_URL || "http://localhost:8000") + "/api/v1",
      timeout: 120000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add auth token and request ID
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
          console.log(
            `API Request: Adding auth token: ${token.substring(0, 20)}...`
          );
        } else {
          console.log("API Request: No auth token available");
        }

        // Add request ID for tracking
        const requestId = `req_${Date.now()}_${Math.random()
          .toString(36)
          .substr(2, 9)}`;
        config.headers["X-Request-ID"] = requestId;
        (config as any).metadata = { requestId, startTime: Date.now() };

        // Add organization context header if available
        if (this.organizationId) {
          config.headers["X-Organization-ID"] = this.organizationId;
          console.log(
            `API Request: Adding organization header: ${this.organizationId}`
          );
        } else {
          console.log("API Request: No organization ID available");
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling and logging
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        await this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private getAuthToken(): string | null {
    // Get token from Supabase auth or localStorage
    const supabaseAuth = localStorage.getItem(
      "sb-pucvturagllxmkvmwoqv-auth-token"
    );
    console.log(
      "Getting auth token from localStorage:",
      supabaseAuth ? "Found" : "Not found"
    );
    if (supabaseAuth) {
      try {
        const parsed = JSON.parse(supabaseAuth);
        console.log("Parsed auth data:", parsed);
        return parsed.access_token;
      } catch (error) {
        console.error("Error parsing auth token:", error);
        return null;
      }
    }
    return null;
  }

  private async handleApiError(error: AxiosError) {
    // Extract request metadata
    const config = error.config as any;
    const requestId = config?.metadata?.requestId;

    // Log the API error
    await errorLoggingService.logApiError({
      message: error.message,
      status: error.response?.status || 0,
      endpoint: error.config?.url || "unknown",
      method: error.config?.method?.toUpperCase() || "UNKNOWN",
      timestamp: new Date().toISOString(),
      userId: this.getCurrentUserId(),
      requestId,
      responseData: error.response?.data,
    });

    // Handle specific error types
    if (error.response?.status === 401) {
      this.handleAuthError();
    }
  }

  private handleAuthError() {
    // Clear auth data and redirect to login
    localStorage.clear();
    window.location.href = "/login";
  }

  private getCurrentUserId(): string | null {
    try {
      const supabaseAuth = localStorage.getItem(
        "sb-pucvturagllxmkvmwoqv-auth-token"
      );
      if (supabaseAuth) {
        const parsed = JSON.parse(supabaseAuth);
        return parsed.user?.id || null;
      }
    } catch {
      // Ignore parsing errors
    }
    return null;
  }

  private async handleResponse<T>(
    promise: Promise<AxiosResponse<T>>
  ): Promise<ApiResponse<T>> {
    try {
      const response = await promise;
      return {
        data: response.data,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        return {
          error:
            error.response?.data?.message ||
            error.message ||
            "An error occurred",
        };
      }
      return {
        error: "An unexpected error occurred",
      };
    }
  }

  // Generic HTTP methods
  async get<T = any>(url: string, params?: any): Promise<ApiResponse<T>> {
    return this.handleResponse(this.api.get(url, { params }));
  }

  async post<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.handleResponse(this.api.post(url, data));
  }

  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.handleResponse(this.api.put(url, data));
  }

  async delete<T = any>(url: string, config?: any): Promise<ApiResponse<T>> {
    return this.handleResponse(this.api.delete(url, config));
  }

  // Chat Completions
  async createChatCompletion(
    data: PlaygroundRequest
  ): Promise<ApiResponse<PlaygroundResponse>> {
    return this.handleResponse(this.api.post("/chat/completions", data));
  }

  async getModels(
    provider?: string
  ): Promise<ApiResponse<ProviderModelInfo[]>> {
    const url = provider ? `/models/${provider}` : "/models";
    return this.handleResponse(this.api.get(url));
  }

  async getProviderModels(provider: string): Promise<ApiResponse<string[]>> {
    return this.handleResponse(this.api.get(`/models/${provider}`));
  }

  // Usage Analytics
  async getUsageMetrics(params?: {
    start_date?: string;
    end_date?: string;
    provider?: string;
    project_id?: string;
  }): Promise<ApiResponse<UsageMetrics>> {
    return this.handleResponse(
      this.api.get("/analytics/usage-metrics", { params })
    );
  }

  async getUsageSummary(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(
      this.api.get("/mock-analytics/usage-summary", { params })
    );
  }

  async getUsageTrends(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: string;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(
      this.api.get("/mock-analytics/usage-trends", { params })
    );
  }

  async getCurrentUsage(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get("/analytics/current-usage"));
  }

  async getApiRequests(params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResponse<RequestLog[]>> {
    return this.handleResponse(
      this.api.get("/analytics/api-requests", { params })
    );
  }

  async getFailedRequests(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<RequestLog[]>> {
    return this.handleResponse(
      this.api.get("/analytics/failed-requests", { params })
    );
  }

  async getCostAnalysis(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: string;
  }): Promise<ApiResponse<any>> {
    return this.handleResponse(
      this.api.get("/mock-analytics/cost-analysis", { params })
    );
  }

  // Cache Management
  async getCacheStats(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get("/system/cache/stats"));
  }

  async clearCache(): Promise<ApiResponse<void>> {
    return this.handleResponse(this.api.delete("/system/cache/clear"));
  }

  async clearUserCache(userId: string): Promise<ApiResponse<void>> {
    return this.handleResponse(this.api.delete(`/system/cache/user/${userId}`));
  }

  async getRateLimitStatus(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get("/system/rate-limit/status"));
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.handleResponse(this.api.get("/health"));
  }

  // Organization Management
  async getUserOrganizations(): Promise<ApiResponse<UserOrganization[]>> {
    return this.handleResponse(this.api.get("/organizations/"));
  }

  // API Keys Management
  async getApiKeys(): Promise<ApiResponse<any[]>> {
    return this.handleResponse(this.api.get("/api-keys/"));
  }

  // Playground-specific endpoints (direct auth, no PAT)
  async getPlaygroundModels(): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get("/playground/models"));
  }

  async playgroundChatCompletion(data: any): Promise<ApiResponse<any>> {
    if (data.stream) {
      // Handle streaming response
      return this.handleStreamingResponse("/playground/chat/completions", data);
    } else {
      // Handle regular response
      return this.handleResponse(this.api.post("/playground/chat/completions", data));
    }
  }

  // Chat Session Management
  async getChatSessions(limit: number = 5, offset: number = 0): Promise<ApiResponse<any[]>> {
    return this.handleResponse(this.api.get(`/chat/sessions?limit=${limit}&offset=${offset}`));
  }

  async createChatSession(data: { provider: string; model: string; session_name?: string }): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.post("/chat/sessions", data));
  }

  async getChatSession(sessionId: string): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.get(`/chat/sessions/${sessionId}`));
  }

  async getSessionMessages(sessionId: string): Promise<ApiResponse<any[]>> {
    return this.handleResponse(this.api.get(`/chat/sessions/${sessionId}/messages`));
  }

  async updateSessionName(sessionId: string, sessionName: string): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.put(`/chat/sessions/${sessionId}/name`, null, {
      params: { session_name: sessionName }
    }));
  }

  async deleteChatSession(sessionId: string): Promise<ApiResponse<any>> {
    return this.handleResponse(this.api.delete(`/chat/sessions/${sessionId}`));
  }

  private async handleStreamingResponse(endpoint: string, data: any): Promise<ApiResponse<any>> {
    try {
      const token = this.getAuthToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      if (this.organizationId) {
        headers['X-Organization-ID'] = this.organizationId;
      }

      const response = await fetch(`${this.api.defaults.baseURL}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body for streaming');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                break;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.choices?.[0]?.delta?.content) {
                  fullContent += parsed.choices[0].delta.content;
                }
              } catch (e) {
                // Skip invalid JSON chunks
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Extract session ID from response headers
      const sessionId = response.headers.get('X-Session-ID');
      
      // Return in OpenAI format
      return {
        data: {
          choices: [{
            message: {
              role: 'assistant',
              content: fullContent
            },
            finish_reason: 'stop'
          }],
          session_id: sessionId
        },
        error: undefined
      };

    } catch (error) {
      console.error('Streaming error:', error);
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Streaming failed'
      };
    }
  }

  // Organization Context Management
  setOrganizationContext(organizationId: string): void {
    console.log(
      `API Service: Setting organization context to: ${organizationId}`
    );
    this.organizationId = organizationId;
  }

  clearOrganizationContext(): void {
    this.organizationId = null;
  }

  getCurrentOrganizationId(): string | null {
    return this.organizationId;
  }
}

export const apiService = new ApiService();
