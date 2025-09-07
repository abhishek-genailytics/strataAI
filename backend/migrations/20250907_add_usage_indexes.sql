-- Migration: Add indexes for usage & cost totals performance
-- Date: 2025-09-07
-- Description: Add indexes to optimize session usage queries on api_requests and token_usage tables

-- Index for session filter + time on api_requests
-- This supports queries filtering by session_id in metadata and time ranges
CREATE INDEX IF NOT EXISTS idx_api_requests_meta_session
  ON api_requests USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_api_requests_session_time
  ON api_requests ((metadata->>'session_id'), created_at DESC);

-- Index for token_usage joins for message bubbles
-- This supports joining token_usage to messages by message_id
CREATE INDEX IF NOT EXISTS idx_token_usage_message 
  ON token_usage(message_id);

-- Additional composite index for api_requests filtering by endpoint and status
-- This optimizes the common query pattern for successful chat completions
CREATE INDEX IF NOT EXISTS idx_api_requests_endpoint_status_time
  ON api_requests (endpoint, status_code, created_at DESC)
  WHERE endpoint = '/v1/chat/completions' AND status_code BETWEEN 200 AND 299;
