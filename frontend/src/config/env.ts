export const Env = {
  apiBaseUrl: process.env.REACT_APP_API_BASE_URL ?? '',
  appEnv: process.env.REACT_APP_APP_ENV ?? 'development',
  supabaseUrl: process.env.REACT_APP_SUPABASE_URL ?? '',
  supabaseAnonKey: process.env.REACT_APP_SUPABASE_ANON_KEY ?? '',
};
