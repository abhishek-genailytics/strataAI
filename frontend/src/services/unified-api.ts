// Enhanced version of the existing API service that integrates with F1 infrastructure
import { useAuthorizedHttp } from '../utils/http';
import { toApiResult } from '../utils/errors';
import type { ApiResult } from '../types/api';
import type { ChatMessage, ChatCompletionsRequest, ChatCompletionsResponse } from './openai';

// Re-export types for backward compatibility
export type { ChatMessage, ChatCompletionsRequest, ChatCompletionsResponse };

// Legacy types from existing codebase
export interface PlaygroundRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface PlaygroundResponse {
  choices: Array<{
    message: ChatMessage;
    finish_reason: string | null;
  }>;
  session_id?: string;
}

export interface ProviderModelInfo {
  id: string;
  provider: string;
  model_name: string;
  display_name: string;
  type: string;
  capabilities?: {
    supports_streaming: boolean;
    supports_function_calling: boolean;
    vision: boolean;
  };
  limits?: {
    max_input_tokens: number;
    max_output_tokens: number;
  };
  pricing?: {
    input: { unit: string; price: number; currency: string };
    output: { unit: string; price: number; currency: string };
  };
  availability?: {
    org_enabled: boolean;
    has_org_api_key: boolean;
    user_enabled: boolean;
    locked_reason: string | null;
  };
  is_default_for_user?: boolean;
}

export interface UserOrganization {
  id: string;
  name: string;
  role: string;
  is_active: boolean;
}

export interface RequestLog {
  id: string;
  endpoint: string;
  method: string;
  status: number;
  timestamp: string;
  userId?: string;
  requestId?: string;
}

export interface UsageMetrics {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  total_cost: number;
}

/**
 * Unified API service that provides both legacy compatibility and new F1 functionality
 * This service bridges the gap between the existing codebase and the new OpenAI-compatible API
 */
export function useUnifiedApiService(accessToken?: string) {
  const client = useAuthorizedHttp(accessToken);

  // ==================== UNIFIED API (F1) METHODS ====================
  
  /**
   * OpenAI-compatible chat completions using the unified /v1/chat/completions endpoint
   * This is the new F1 method that supports PAT authentication and provider abstraction
   */
  async function createChatCompletion(
    body: ChatCompletionsRequest
  ): Promise<ApiResult<ChatCompletionsResponse>> {
    return toApiResult(() => client.post('/v1/chat/completions', body));
  }

  // ==================== LEGACY PLAYGROUND METHODS ====================
  
  /**
   * Legacy playground chat completions (maintains existing behavior)
   * Uses the direct playground endpoints with Supabase JWT authentication
   */
  async function playgroundChatCompletion(data: PlaygroundRequest): Promise<ApiResult<PlaygroundResponse>> {
    if (data.stream) {
      return handleStreamingResponse('/api/v1/playground/chat/completions', data);
    } else {
      return toApiResult(() => client.post('/api/v1/playground/chat/completions', data));
    }
  }

  /**
   * Get available models for playground (legacy endpoint)
   */
  async function getPlaygroundModels(): Promise<ApiResult<ProviderModelInfo[]>> {
    return toApiResult(() => client.get('/api/v1/playground/models'));
  }

  // ==================== ORGANIZATION & USER MANAGEMENT ====================
  
  async function getUserOrganizations(): Promise<ApiResult<UserOrganization[]>> {
    return toApiResult(() => client.get('/api/v1/organizations/'));
  }

  async function getApiKeys(): Promise<ApiResult<any[]>> {
    return toApiResult(() => client.get('/api/v1/api-keys/'));
  }

  // ==================== CHAT SESSION MANAGEMENT ====================
  
  async function getChatSessions(limit: number = 5, offset: number = 0): Promise<ApiResult<any[]>> {
    return toApiResult(() => client.get(`/api/v1/chat/sessions?limit=${limit}&offset=${offset}`));
  }

  async function createChatSession(data: { provider: string; model: string; session_name?: string }): Promise<ApiResult<any>> {
    return toApiResult(() => client.post('/api/v1/chat/sessions', data));
  }

  async function getChatSession(sessionId: string): Promise<ApiResult<any>> {
    return toApiResult(() => client.get(`/api/v1/chat/sessions/${sessionId}`));
  }

  async function getSessionMessages(sessionId: string): Promise<ApiResult<any[]>> {
    return toApiResult(() => client.get(`/api/v1/chat/sessions/${sessionId}/messages`));
  }

  async function updateSessionName(sessionId: string, sessionName: string): Promise<ApiResult<any>> {
    return toApiResult(() => client.put(`/api/v1/chat/sessions/${sessionId}/name`, null, {
      params: { session_name: sessionName }
    }));
  }

  async function deleteChatSession(sessionId: string): Promise<ApiResult<any>> {
    return toApiResult(() => client.delete(`/api/v1/chat/sessions/${sessionId}`));
  }

  // ==================== ANALYTICS & MONITORING ====================
  
  async function getUsageMetrics(params?: {
    start_date?: string;
    end_date?: string;
    provider?: string;
    project_id?: string;
  }): Promise<ApiResult<UsageMetrics>> {
    return toApiResult(() => client.get('/api/v1/analytics/usage-metrics', { params }));
  }

  async function getApiRequests(params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResult<RequestLog[]>> {
    return toApiResult(() => client.get('/api/v1/analytics/api-requests', { params }));
  }

  async function healthCheck(): Promise<ApiResult<{ status: string }>> {
    return toApiResult(() => client.get('/api/v1/health'));
  }

  // ==================== STREAMING HELPER ====================
  
  async function handleStreamingResponse(endpoint: string, data: any): Promise<ApiResult<PlaygroundResponse>> {
    try {
      const response = await fetch(`${client.defaults.baseURL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': client.defaults.headers.Authorization as string,
          'X-Organization-ID': client.defaults.headers['X-Organization-ID'] as string,
          'X-Client-Request-ID': client.defaults.headers['X-Client-Request-ID'] as string,
        },
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

      const sessionId = response.headers.get('X-Session-ID') || undefined;
      
      return {
        ok: true,
        data: {
          choices: [{
            message: {
              role: 'assistant',
              content: fullContent
            },
            finish_reason: 'stop'
          }],
          session_id: sessionId
        }
      };

    } catch (error) {
      console.error('Streaming error:', error);
      return {
        ok: false,
        error: {
          message: error instanceof Error ? error.message : 'Streaming failed',
          type: 'streaming_error',
          code: 'ESTREAM'
        }
      };
    }
  }

  return {
    // F1 Unified API methods
    createChatCompletion,
    
    // Legacy playground methods
    playgroundChatCompletion,
    getPlaygroundModels,
    
    // Organization & user management
    getUserOrganizations,
    getApiKeys,
    
    // Chat session management
    getChatSessions,
    createChatSession,
    getChatSession,
    getSessionMessages,
    updateSessionName,
    deleteChatSession,
    
    // Analytics
    getUsageMetrics,
    getApiRequests,
    healthCheck,
  };
}
