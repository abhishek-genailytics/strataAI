-- Migration: Fix Missing User Profiles
-- Created: 2024-12-26
-- Description: Creates user profiles for all existing users in auth.users who don't have profiles

-- Step 1: Create user profiles for all existing users who don't have profiles
INSERT INTO user_profiles (id, full_name, created_at, updated_at)
SELECT 
    au.id,
    COALESCE(au.raw_user_meta_data->>'full_name', ''),
    au.created_at,
    au.updated_at
FROM auth.users au
LEFT JOIN user_profiles up ON au.id = up.id
WHERE up.id IS NULL
  AND au.email_confirmed_at IS NOT NULL;  -- Only confirmed users

-- Step 2: Verify the trigger is working by checking if it exists
DO $$
BEGIN
    -- Check if the trigger exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'on_auth_user_created' 
        AND tgrelid = 'auth.users'::regclass
    ) THEN
        -- Recreate the trigger if it doesn't exist
        CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW EXECUTE FUNCTION handle_new_user();
        
        RAISE NOTICE 'Recreated trigger on_auth_user_created';
    ELSE
        RAISE NOTICE 'Trigger on_auth_user_created already exists';
    END IF;
END $$;

-- Step 3: Verify the function exists
DO $$
BEGIN
    -- Check if the function exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'handle_new_user'
    ) THEN
        -- Recreate the function if it doesn't exist
        CREATE OR REPLACE FUNCTION handle_new_user()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO user_profiles (id, full_name, created_at, updated_at)
            VALUES (
                NEW.id,
                COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
                NEW.created_at,
                NEW.updated_at
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        RAISE NOTICE 'Recreated function handle_new_user';
    ELSE
        RAISE NOTICE 'Function handle_new_user already exists';
    END IF;
END $$;

-- Step 4: Grant necessary permissions
GRANT SELECT, INSERT, UPDATE ON user_profiles TO authenticated;
GRANT EXECUTE ON FUNCTION handle_new_user() TO authenticated;

-- Step 5: Create a function to manually sync user profiles (for future use)
CREATE OR REPLACE FUNCTION sync_missing_user_profiles()
RETURNS INTEGER AS $$
DECLARE
    sync_count INTEGER := 0;
BEGIN
    -- Insert missing user profiles
    INSERT INTO user_profiles (id, full_name, created_at, updated_at)
    SELECT 
        au.id,
        COALESCE(au.raw_user_meta_data->>'full_name', ''),
        au.created_at,
        au.updated_at
    FROM auth.users au
    LEFT JOIN user_profiles up ON au.id = up.id
    WHERE up.id IS NULL
      AND au.email_confirmed_at IS NOT NULL;
    
    GET DIAGNOSTICS sync_count = ROW_COUNT;
    
    RETURN sync_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 6: Grant permissions for the sync function
GRANT EXECUTE ON FUNCTION sync_missing_user_profiles() TO authenticated;

-- Step 7: Run the sync function to ensure all users have profiles
SELECT sync_missing_user_profiles() as profiles_created;
