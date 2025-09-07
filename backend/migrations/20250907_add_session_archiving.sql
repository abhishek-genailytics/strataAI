-- Add session archiving support to chat_sessions table
-- PG-5: Session lifecycle (create → manage → archive)

-- Add is_archived column with default false
ALTER TABLE chat_sessions 
ADD COLUMN is_archived BOOLEAN DEFAULT FALSE NOT NULL;

-- Add message_index column to chat_messages for reliable ordering
ALTER TABLE chat_messages 
ADD COLUMN message_index INTEGER DEFAULT 0 NOT NULL;

-- Create unique constraint for session_id + message_index to prevent conflicts
ALTER TABLE chat_messages 
ADD CONSTRAINT chat_messages_session_message_idx_unique 
UNIQUE (session_id, message_index);

-- Add organization_id to chat_sessions for proper multi-tenancy
ALTER TABLE chat_sessions 
ADD COLUMN organization_id UUID REFERENCES organizations(id);

-- Update existing sessions to have organization_id based on user's primary organization
UPDATE chat_sessions 
SET organization_id = (
    SELECT organization_id 
    FROM user_profiles 
    WHERE user_profiles.id = chat_sessions.user_id
    LIMIT 1
)
WHERE organization_id IS NULL;

-- Make organization_id NOT NULL after backfill
ALTER TABLE chat_sessions 
ALTER COLUMN organization_id SET NOT NULL;

-- Add indexes for performance
CREATE INDEX idx_chat_sessions_org_user_archived 
ON chat_sessions(organization_id, user_id, is_archived, updated_at DESC);

CREATE INDEX idx_chat_messages_session_index 
ON chat_messages(session_id, message_index);

-- Add title column (rename from session_name for consistency)
ALTER TABLE chat_sessions 
ADD COLUMN title TEXT;

-- Copy session_name to title
UPDATE chat_sessions 
SET title = COALESCE(session_name, 'New Chat');

-- Make title NOT NULL
ALTER TABLE chat_sessions 
ALTER COLUMN title SET NOT NULL;

-- Add metadata JSONB column for extensible session configuration
ALTER TABLE chat_sessions 
ADD COLUMN metadata JSONB DEFAULT '{}' NOT NULL;

-- Update RLS policies to include organization_id filtering
DROP POLICY IF EXISTS "Users can only access their own chat sessions" ON chat_sessions;

CREATE POLICY "Users can access sessions in their organizations" ON chat_sessions
    FOR ALL USING (
        organization_id IN (
            SELECT uo.organization_id 
            FROM user_organizations uo 
            WHERE uo.user_id = auth.uid() 
            AND uo.is_active = true
        )
        AND user_id = auth.uid()
    );

-- Backfill message_index for existing messages
WITH indexed_messages AS (
    SELECT 
        id,
        session_id,
        ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) - 1 as new_index
    FROM chat_messages
    WHERE message_index = 0
)
UPDATE chat_messages 
SET message_index = indexed_messages.new_index
FROM indexed_messages
WHERE chat_messages.id = indexed_messages.id;
