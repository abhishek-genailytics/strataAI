-- Migration: Add Default PAT Creation for New Users
-- Created: 2024-12-26
-- Description: Automatically creates a default PAT when users join an organization

-- Step 1: Create function to create default PAT for new organization members
CREATE OR REPLACE FUNCTION create_default_pat_for_user()
RETURNS TRIGGER AS $$
DECLARE
    token_value TEXT;
    token_prefix TEXT;
    token_hash TEXT;
BEGIN
    -- Only create default PAT for new organization members
    IF TG_OP = 'INSERT' THEN
        -- Generate default PAT
        token_value := 'pat_' || encode(gen_random_bytes(32), 'base64');
        token_prefix := substring(token_value from 1 for 8) || '...' || substring(token_value from length(token_value) - 3);
        token_hash := encode(sha256(token_value::bytea), 'hex');
        
        -- Insert default PAT
        INSERT INTO personal_access_tokens (
            user_id,
            organization_id,
            name,
            token_hash,
            token_prefix,
            scopes,
            is_active
        ) VALUES (
            NEW.user_id,
            NEW.organization_id,
            'Default API Token',
            token_hash,
            token_prefix,
            '["api:read", "api:write"]'::jsonb,
            true
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 2: Create trigger to automatically create default PAT
DROP TRIGGER IF EXISTS on_user_organization_created ON user_organizations;
CREATE TRIGGER on_user_organization_created
    AFTER INSERT ON user_organizations
    FOR EACH ROW EXECUTE FUNCTION create_default_pat_for_user();

-- Step 3: Grant necessary permissions
GRANT EXECUTE ON FUNCTION create_default_pat_for_user() TO authenticated;

-- Step 4: Create function to get all users (including those without organizations)
CREATE OR REPLACE FUNCTION get_all_users_with_organizations()
RETURNS TABLE(
    user_id UUID,
    email VARCHAR,
    full_name VARCHAR,
    organization_id UUID,
    organization_name VARCHAR,
    role VARCHAR,
    joined_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as user_id,
        u.email,
        up.full_name,
        uo.organization_id,
        o.name as organization_name,
        uo.role,
        uo.joined_at,
        u.created_at
    FROM auth.users u
    LEFT JOIN user_profiles up ON u.id = up.id
    LEFT JOIN user_organizations uo ON u.id = uo.user_id AND uo.is_active = true
    LEFT JOIN organizations o ON uo.organization_id = o.id AND o.is_active = true
    WHERE u.email_confirmed_at IS NOT NULL  -- Only confirmed users
    ORDER BY u.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 5: Grant permissions for the new function
GRANT EXECUTE ON FUNCTION get_all_users_with_organizations() TO authenticated;
