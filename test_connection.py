#!/usr/bin/env python3
"""
Test database connection to Supabase
Run this script to verify your database connection
"""

import os
import sys
from pathlib import Path

# Load .env file
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('✗ DATABASE_URL not found in .env file')
    sys.exit(1)

try:
    import psycopg2
    print('🔌 Testing database connection to Supabase...')
    print('')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Test 1: Check PostgreSQL version
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print('✅ Connection successful!')
    print(f'   PostgreSQL: {version.split(",")[0]}')
    print('')
    
    # Test 2: Check if licenses table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'licenses'
        );
    """)
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print('✅ Table "licenses" exists')
        
        # Count rows
        cursor.execute('SELECT COUNT(*) FROM licenses;')
        count = cursor.fetchone()[0]
        print(f'   Current licenses: {count}')
        
        # Show table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'licenses'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print('')
        print('   Table structure:')
        for col in columns:
            nullable = 'NULL' if col[2] == 'YES' else 'NOT NULL'
            print(f'     - {col[0]}: {col[1]} ({nullable})')
    else:
        print('⚠️  Table "licenses" does not exist yet')
        print('   → Run schema.sql in Supabase SQL Editor to create it')
    
    cursor.close()
    conn.close()
    print('')
    print('🎉 All checks passed! Database is ready.')
    
except ImportError:
    print('✗ Error: psycopg2 not installed')
    print('   Run: pip install psycopg2-binary')
    sys.exit(1)
except psycopg2.OperationalError as e:
    print('✗ Connection failed!')
    print(f'   Error: {str(e)}')
    print('')
    print('   Possible issues:')
    print('   - Supabase project is paused (free tier auto-pauses)')
    print('   - Wrong password or connection string')
    print('   - Network/firewall blocking connection')
    print('')
    print('   To fix:')
    print('   1. Go to https://supabase.com/dashboard')
    print('   2. Click on your project to wake it up')
    print('   3. Wait a few seconds for it to start')
    print('   4. Run this script again')
    sys.exit(1)
except Exception as e:
    print(f'✗ Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

