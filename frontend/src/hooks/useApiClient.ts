import { useMemo } from 'react';
import { useOpenAIService } from '../services/openai';

export function useApiClient(accessToken?: string) {
  const openai = useOpenAIService(accessToken);
  return useMemo(() => ({ openai }), [accessToken]);
}
