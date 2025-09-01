-- Migration: Remove ScaleKit Dependencies and Add User Profiles
-- Created: 2024-12-25
-- Description: Migrates from ScaleKit to Supabase Authentication with user profiles

-- Step 1: Create user_profiles table to extend auth.users
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    website VARCHAR(255),
    location VARCHAR(255),
    timezone VARCHAR(50),
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_full_name ON user_profiles(full_name);
CREATE INDEX IF NOT EXISTS idx_user_profiles_active ON user_profiles(is_active);

-- Step 2: Remove ScaleKit-specific columns from organizations table
ALTER TABLE organizations DROP COLUMN IF EXISTS scalekit_organization_id;

-- Step 3: Remove ScaleKit-specific columns from user_organizations table
ALTER TABLE user_organizations DROP COLUMN IF EXISTS scalekit_user_id;

-- Step 4: Drop ScaleKit-specific indexes
DROP INDEX IF EXISTS idx_organizations_scalekit_id;
DROP INDEX IF EXISTS idx_user_organizations_scalekit_user;

-- Step 5: Update organizations table to make name unique (since we removed scalekit_organization_id)
ALTER TABLE organizations ADD CONSTRAINT organizations_name_unique UNIQUE (name);

-- Step 6: Add updated_at trigger for user_profiles
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Step 7: Enable Row Level Security for user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Step 8: Create RLS policies for user_profiles
CREATE POLICY "Users can view their own profile" ON user_profiles
    FOR SELECT USING (id = auth.uid());

CREATE POLICY "Users can update their own profile" ON user_profiles
    FOR UPDATE USING (id = auth.uid());

CREATE POLICY "Users can insert their own profile" ON user_profiles
    FOR INSERT WITH CHECK (id = auth.uid());

-- Step 9: Update the get_user_organizations function to remove scalekit_organization_id
CREATE OR REPLACE FUNCTION get_user_organizations(user_uuid UUID)
RETURNS TABLE(
    organization_id UUID,
    organization_name VARCHAR,
    organization_display_name VARCHAR,
    user_role VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.name,
        o.display_name,
        uo.role
    FROM organizations o
    JOIN user_organizations uo ON o.id = uo.organization_id
    WHERE uo.user_id = user_uuid AND uo.is_active = true AND o.is_active = true
    ORDER BY uo.joined_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 10: Create function to automatically create user profile on user registration
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (id, full_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 11: Create trigger to automatically create user profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Step 12: Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON user_profiles TO authenticated;
GRANT EXECUTE ON FUNCTION handle_new_user() TO authenticated;

-- Step 13: Create function to get user profile with organizations
CREATE OR REPLACE FUNCTION get_user_profile_with_organizations(user_uuid UUID)
RETURNS TABLE(
    user_id UUID,
    email VARCHAR,
    full_name VARCHAR,
    avatar_url TEXT,
    bio TEXT,
    website VARCHAR,
    location VARCHAR,
    timezone VARCHAR,
    preferences JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    organizations JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        up.id,
        au.email,
        up.full_name,
        up.avatar_url,
        up.bio,
        up.website,
        up.location,
        up.timezone,
        up.preferences,
        up.metadata,
        up.created_at,
        COALESCE(
            (SELECT json_agg(
                json_build_object(
                    'id', o.id,
                    'name', o.name,
                    'display_name', o.display_name,
                    'role', uo.role,
                    'joined_at', uo.joined_at
                )
            )
            FROM organizations o
            JOIN user_organizations uo ON o.id = uo.organization_id
            WHERE uo.user_id = user_uuid AND uo.is_active = true AND o.is_active = true),
            '[]'::json
        ) as organizations
    FROM user_profiles up
    JOIN auth.users au ON up.id = au.id
    WHERE up.id = user_uuid AND up.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 14: Grant permissions for the new function
GRANT EXECUTE ON FUNCTION get_user_profile_with_organizations(UUID) TO authenticated;
