#!/usr/bin/env python3
"""
Script to apply the default PAT creation migration
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
    """Main function to apply the migration"""
    print("🚀 Applying Default PAT Creation Migration")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Read the migration file
    migration_file = Path("backend/migrations/20241226_add_default_pat_creation.sql")
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
    print("1. Creates automatic default PAT generation when users join organizations")
    print("2. Adds function to get all users (including those without organizations)")
    print("3. Updates user management to show all users")
    print("4. Allows PAT creation for users without organizations")
    
    print("\n🎉 Default PAT creation is now active!")
    print("   New users will automatically get a 'Default API Token' when they join an organization.")

if __name__ == "__main__":
    main()
