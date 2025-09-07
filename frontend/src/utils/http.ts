import axios from 'axios';
import { Env } from '../config/env';
import { useOrg } from '../contexts/OrgContext';
import { normalizeApiError } from './errors';

export const http = axios.create({
  baseURL: Env.apiBaseUrl,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// hook-friendly header injector for components/hooks
export function useAuthorizedHttp(accessToken?: string) {
  const { orgId } = useOrg();

  const instance = http; // reuse singleton + attach per-request config below

  instance.interceptors.request.use((config) => {
    // Authorization: Bearer <user session token or PAT>
    if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
    // X-Organization-ID for multi-tenant routing
    if (orgId) config.headers['X-Organization-ID'] = orgId;
    // Opt-in request id (helps correlating logs)
    if (!config.headers['X-Client-Request-ID']) {
      config.headers['X-Client-Request-ID'] = crypto.randomUUID?.() ?? String(Date.now());
    }
    return config;
  });

  instance.interceptors.response.use(
    (res) => res,
    (err) => Promise.reject(normalizeApiError(err))
  );

  return instance;
}
