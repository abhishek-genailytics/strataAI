export type OpenAIError = {
  error: { message: string; type?: string; param?: string; code?: string | number };
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: OpenAIError['error'] };
