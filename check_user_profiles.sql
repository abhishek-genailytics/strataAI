-- User Profile Verification and Fix Script
-- Run these queries in your Supabase SQL Editor

-- 1. Check total users in auth.users
SELECT COUNT(*) as total_auth_users 
FROM auth.users 
WHERE email_confirmed_at IS NOT NULL;

-- 2. Check total user profiles
SELECT COUNT(*) as total_user_profiles 
FROM user_profiles;

-- 3. Check users without profiles
SELECT COUNT(*) as users_without_profiles
FROM auth.users au
LEFT JOIN user_profiles up ON au.id = up.id
WHERE up.id IS NULL AND au.email_confirmed_at IS NOT NULL;

-- 4. Show sample users without profiles
SELECT au.id, au.email, au.created_at, au.raw_user_meta_data
FROM auth.users au
LEFT JOIN user_profiles up ON au.id = up.id
WHERE up.id IS NULL AND au.email_confirmed_at IS NOT NULL
LIMIT 5;

-- 5. Show sample user profiles
SELECT up.id, up.full_name, up.created_at, au.email
FROM user_profiles up
JOIN auth.users au ON up.id = au.id
LIMIT 5;

-- 6. Create missing user profiles (run this if step 3 shows missing profiles)
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

-- 7. Verify the trigger exists
SELECT 
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- 8. Verify the function exists
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines 
WHERE routine_name = 'handle_new_user';

-- 9. Test the sync function (run this to create any remaining missing profiles)
SELECT sync_missing_user_profiles() as profiles_created;

-- 10. Final verification - should show 0 missing profiles
SELECT COUNT(*) as remaining_users_without_profiles
FROM auth.users au
LEFT JOIN user_profiles up ON au.id = up.id
WHERE up.id IS NULL AND au.email_confirmed_at IS NOT NULL;
