import { useAuthorizedHttp } from '../utils/http';
import { toApiResult } from '../utils/errors';
import type { ApiResult } from '../types/api';

// Minimal types for chat.completions
export type ChatMessage = { role: 'system' | 'user' | 'assistant'; content: string };

export type ChatCompletionsRequest = {
  model: string; // e.g., "openai/gpt-4" or "anthropic/claude-3.5"
  messages: ChatMessage[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  // streaming intentionally omitted for MVP
};

export type ChatChoice = { 
  index: number; 
  message: ChatMessage; 
  finish_reason: string | null 
};

export type ChatCompletionsResponse = {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: ChatChoice[];
  usage?: { 
    prompt_tokens: number; 
    completion_tokens: number; 
    total_tokens: number; 
    cost_usd?: number 
  };
};

export function useOpenAIService(accessToken?: string) {
  const client = useAuthorizedHttp(accessToken);

  async function createChatCompletion(
    body: ChatCompletionsRequest
  ): Promise<ApiResult<ChatCompletionsResponse>> {
    return toApiResult(() => client.post('/v1/chat/completions', body));
  }

  return { createChatCompletion };
}
