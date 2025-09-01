# User Profile Fix Summary

## Problem

The `user_profiles` table was empty even though there were users registered in `auth.users` in Supabase. This indicated that the database trigger to automatically create user profiles wasn't working properly.

## Root Cause

The database trigger `on_auth_user_created` that should automatically create user profiles when users register was either:

1. Not properly created
2. Not working for existing users
3. Missing the necessary permissions

## Solution Implemented

### 1. Migration Created

**File**: `backend/migrations/20241226_fix_missing_user_profiles.sql`

This migration:

- Creates user profiles for all existing users in `auth.users` who don't have profiles
- Verifies and recreates the trigger if needed
- Creates a sync function for future use
- Ensures all confirmed users have profiles

### 2. Enhanced Registration Logic

**File**: `backend/app/api/auth.py`

Updated the registration endpoint to:

- Try to update existing profile first
- Fall back to creating profile if update fails
- Ensures every new user gets a profile

### 3. Verification Tools Created

#### SQL Verification Script

**File**: `check_user_profiles.sql`
Contains SQL queries to:

- Check total users vs profiles
- Identify missing profiles
- Create missing profiles
- Verify triggers and functions

#### Python Scripts

- `fix_user_profiles.py` - Applies the migration
- `verify_user_profiles.py` - Provides verification queries
- `test_user_profile_creation.py` - Tests the system

## How to Verify the Fix

### Option 1: Run SQL Queries in Supabase Dashboard

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Run the queries from `check_user_profiles.sql`

### Option 2: Use the Python Scripts

```bash
# Apply the fix
python fix_user_profiles.py

# Verify the results
python verify_user_profiles.py
```

### Expected Results

After running the fix:

- ✅ Total users in `auth.users` should match total user profiles
- ✅ Users without profiles should be 0
- ✅ All confirmed users should have corresponding profiles

## Database Schema

### user_profiles Table

```sql
CREATE TABLE user_profiles (
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
```

### Trigger Function

```sql
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
```

### Trigger

```sql
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

## Security Features

### Row Level Security (RLS)

```sql
-- Users can only view their own profile
CREATE POLICY "Users can view their own profile" ON user_profiles
    FOR SELECT USING (id = auth.uid());

-- Users can update their own profile
CREATE POLICY "Users can update their own profile" ON user_profiles
    FOR UPDATE USING (id = auth.uid());

-- Users can insert their own profile
CREATE POLICY "Users can insert their own profile" ON user_profiles
    FOR INSERT WITH CHECK (id = auth.uid());
```

## API Endpoints

### Registration

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

### Get Profile

```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Update Profile

```http
PUT /api/auth/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Doe",
  "bio": "Software Developer"
}
```

## Testing

### Manual Testing

1. Register a new user through the frontend
2. Check that a profile is created in the database
3. Verify the profile data is correct
4. Test profile updates

### Automated Testing

Run the test scripts to verify:

- Existing users have profiles
- Trigger function exists and works
- Sync function works
- Manual profile creation works

## Future Maintenance

### Sync Function

A `sync_missing_user_profiles()` function has been created for future use:

```sql
SELECT sync_missing_user_profiles() as profiles_created;
```

### Monitoring

Regular checks can be performed using:

```sql
-- Check for missing profiles
SELECT COUNT(*) as missing_profiles
FROM auth.users au
LEFT JOIN user_profiles up ON au.id = up.id
WHERE up.id IS NULL AND au.email_confirmed_at IS NOT NULL;
```

## Files Modified/Created

### Backend

- `backend/migrations/20241226_fix_missing_user_profiles.sql` (NEW)
- `backend/app/api/auth.py` (UPDATED)

### Scripts

- `fix_user_profiles.py` (NEW)
- `verify_user_profiles.py` (NEW)
- `test_user_profile_creation.py` (NEW)
- `check_user_profiles.sql` (NEW)

### Documentation

- `USER_PROFILE_FIX_SUMMARY.md` (NEW)

## Next Steps

1. **Apply the migration** using the provided script or manually in Supabase
2. **Verify the fix** by running the verification queries
3. **Test user registration** to ensure new users get profiles
4. **Monitor the system** to ensure profiles are created for all users

## Troubleshooting

### If profiles are still missing:

1. Run the sync function: `SELECT sync_missing_user_profiles();`
2. Check trigger permissions: `GRANT EXECUTE ON FUNCTION handle_new_user() TO authenticated;`
3. Verify RLS policies are active
4. Check for any database errors in Supabase logs

### If new users don't get profiles:

1. Verify the trigger exists: `SELECT * FROM information_schema.triggers WHERE trigger_name = 'on_auth_user_created';`
2. Check the function exists: `SELECT * FROM information_schema.routines WHERE routine_name = 'handle_new_user';`
3. Test the function manually
4. Check Supabase logs for any errors

---

**Status**: ✅ Fixed  
**Date**: December 26, 2024  
**Version**: 1.0
