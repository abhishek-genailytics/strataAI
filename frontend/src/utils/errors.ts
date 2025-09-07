import type { OpenAIError } from '../types/api';

export function normalizeApiError(err: any): OpenAIError {
  // If backend already returns OpenAI-style { error: {...} }
  if (err?.response?.data?.error) return err.response.data as OpenAIError;

  // Network/timeouts
  if (err?.code === 'ECONNABORTED') {
    return { error: { message: 'Request timed out', type: 'timeout_error', code: 'ETIMEOUT' } };
  }
  if (err?.message === 'Network Error') {
    return { error: { message: 'Network error', type: 'network_error', code: 'ENET' } };
  }

  // Fallback (status text or generic)
  const status = err?.response?.status;
  const statusText = err?.response?.statusText;
  const message = err?.message ?? 'Unexpected error';
  return {
    error: {
      message: statusText ? `${status} ${statusText}` : message,
      type: 'api_error',
      code: status ?? 'EUNKNOWN',
    },
  };
}

export function toApiResult<T>(fn: () => Promise<{ data: T }>) {
  return fn()
    .then((res) => ({ ok: true, data: res.data } as const))
    .catch((e) => ({ ok: false, error: normalizeApiError(e).error } as const));
}
