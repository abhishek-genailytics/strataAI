-- Migration: Add Organizations and User-Organization Relationships
-- Created: 2024-12-24
-- Description: Adds multi-tenant organization support with ScaleKit integration

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scalekit_organization_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    domain VARCHAR(255),
    external_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_scalekit_id ON organizations(scalekit_organization_id);
CREATE INDEX IF NOT EXISTS idx_organizations_domain ON organizations(domain);
CREATE INDEX IF NOT EXISTS idx_organizations_external_id ON organizations(external_id);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations(is_active);

-- Create user_organizations junction table for many-to-many relationship
CREATE TABLE IF NOT EXISTS user_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    scalekit_user_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

-- Create indexes for user_organizations
CREATE INDEX IF NOT EXISTS idx_user_organizations_user_id ON user_organizations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_org_id ON user_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_scalekit_user ON user_organizations(scalekit_user_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_active ON user_organizations(is_active);

-- Add organization_id to existing tables for multi-tenant support
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE request_logs ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE usage_metrics ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Create indexes for organization_id foreign keys
CREATE INDEX IF NOT EXISTS idx_api_keys_organization_id ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_request_logs_organization_id ON request_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_organization_id ON usage_metrics(organization_id);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_organizations_updated_at ON user_organizations;
CREATE TRIGGER update_user_organizations_updated_at
    BEFORE UPDATE ON user_organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_organizations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for organizations
CREATE POLICY "Users can view organizations they belong to" ON organizations
    FOR SELECT USING (
        id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "Organization admins can update their organization" ON organizations
    FOR UPDATE USING (
        id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND role IN ('admin', 'owner') AND is_active = true
        )
    );

-- Create RLS policies for user_organizations
CREATE POLICY "Users can view their organization memberships" ON user_organizations
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Organization admins can manage memberships" ON user_organizations
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND role IN ('admin', 'owner') AND is_active = true
        )
    );

-- Update existing RLS policies for multi-tenant support
-- API Keys: Users can only access their own keys within their organizations
DROP POLICY IF EXISTS "Users can view their own API keys" ON api_keys;
CREATE POLICY "Users can view their own API keys" ON api_keys
    FOR SELECT USING (
        user_id = auth.uid() AND 
        (organization_id IS NULL OR organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        ))
    );

DROP POLICY IF EXISTS "Users can insert their own API keys" ON api_keys;
CREATE POLICY "Users can insert their own API keys" ON api_keys
    FOR INSERT WITH CHECK (
        user_id = auth.uid() AND 
        (organization_id IS NULL OR organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        ))
    );

DROP POLICY IF EXISTS "Users can update their own API keys" ON api_keys;
CREATE POLICY "Users can update their own API keys" ON api_keys
    FOR UPDATE USING (
        user_id = auth.uid() AND 
        (organization_id IS NULL OR organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        ))
    );

DROP POLICY IF EXISTS "Users can delete their own API keys" ON api_keys;
CREATE POLICY "Users can delete their own API keys" ON api_keys
    FOR DELETE USING (
        user_id = auth.uid() AND 
        (organization_id IS NULL OR organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        ))
    );

-- Request Logs: Users can view logs for their requests within their organizations
DROP POLICY IF EXISTS "Users can view their own request logs" ON request_logs;
CREATE POLICY "Users can view their own request logs" ON request_logs
    FOR SELECT USING (
        user_id = auth.uid() AND 
        (organization_id IS NULL OR organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        ))
    );

-- Usage Metrics: Users can view metrics for their organizations
DROP POLICY IF EXISTS "Users can view their own usage metrics" ON usage_metrics;
CREATE POLICY "Users can view their own usage metrics" ON usage_metrics
    FOR SELECT USING (
        user_id = auth.uid() AND 
        (organization_id IS NULL OR organization_id IN (
            SELECT organization_id 
            FROM user_organizations 
            WHERE user_id = auth.uid() AND is_active = true
        ))
    );

-- Create function to get user's organizations
CREATE OR REPLACE FUNCTION get_user_organizations(user_uuid UUID)
RETURNS TABLE(
    organization_id UUID,
    organization_name VARCHAR,
    organization_display_name VARCHAR,
    user_role VARCHAR,
    scalekit_organization_id VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.name,
        o.display_name,
        uo.role,
        o.scalekit_organization_id
    FROM organizations o
    JOIN user_organizations uo ON o.id = uo.organization_id
    WHERE uo.user_id = user_uuid AND uo.is_active = true AND o.is_active = true
    ORDER BY uo.joined_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check if user belongs to organization
CREATE OR REPLACE FUNCTION user_belongs_to_organization(user_uuid UUID, org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 
        FROM user_organizations 
        WHERE user_id = user_uuid 
        AND organization_id = org_id 
        AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT SELECT ON organizations TO authenticated;
GRANT SELECT ON user_organizations TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_organizations(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION user_belongs_to_organization(UUID, UUID) TO authenticated;
