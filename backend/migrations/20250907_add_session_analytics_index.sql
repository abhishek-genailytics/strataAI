-- Add index for session analytics aggregation (PG-8/PG-9)
-- Enables efficient queries for session-based usage analytics in playground HUD

-- Index for session-based analytics queries on api_requests table
-- Used by PG-8 usage aggregation service to efficiently filter by session_id
CREATE INDEX IF NOT EXISTS idx_api_requests_session_analytics 
ON api_requests USING btree ((metadata->>'session_id'), created_at)
WHERE metadata->>'session_id' IS NOT NULL;

-- Add comment for documentation
COMMENT ON INDEX idx_api_requests_session_analytics IS 
'Optimizes session-based analytics queries for playground usage tracking (PG-8/PG-9)';
