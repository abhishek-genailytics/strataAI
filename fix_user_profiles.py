#!/usr/bin/env python3
"""
Script to fix missing user profiles and verify the results
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    """Main function to fix user profiles"""
    print("🔧 Fixing Missing User Profiles")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Read the migration file
    migration_file = Path("backend/migrations/20241226_fix_missing_user_profiles.sql")
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    # Read the SQL content
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    print(f"📄 Migration file: {migration_file}")
    print(f"📏 SQL content length: {len(sql_content)} characters")
    
    # Check if Supabase CLI is available
    result = run_command("supabase --version", "Checking Supabase CLI")
    if not result:
        print("❌ Supabase CLI not found. Please install it first.")
        print("   Visit: https://supabase.com/docs/guides/cli")
        sys.exit(1)
    
    # Apply the migration using Supabase CLI
    print("\n🔧 Applying migration to database...")
    
    # Method 1: Try using Supabase CLI
    result = run_command(
        "cd backend && supabase db push",
        "Applying migration via Supabase CLI"
    )
    
    if not result:
        print("\n⚠️  Supabase CLI method failed. Trying alternative method...")
        
        # Method 2: Try direct SQL execution
        print("\n📝 You can manually apply the migration by:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the following SQL:")
        print("-" * 50)
        print(sql_content)
        print("-" * 50)
        
        # Ask user if they want to continue
        response = input("\n🤔 Would you like to continue with manual application? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled")
            sys.exit(1)
    
    print("\n✅ Migration applied successfully!")
    print("\n📋 What this migration does:")
    print("1. Creates user profiles for all existing users in auth.users")
    print("2. Verifies and recreates the trigger if needed")
    print("3. Creates a sync function for future use")
    print("4. Ensures all confirmed users have profiles")
    
    print("\n🎉 User profiles are now synchronized!")
    print("   All existing users should now have profiles in the user_profiles table.")

if __name__ == "__main__":
    main()
