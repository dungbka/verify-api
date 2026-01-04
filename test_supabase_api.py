#!/usr/bin/env python3
"""
Test Supabase REST API connection
"""

import requests
import json

# Supabase API credentials
SUPABASE_URL = "https://iwxrpjeowtnhsacaonhz.supabase.co"
SUPABASE_KEY = "sb_publishable__sHAilM6z41QSb72bXUckg_wYKIY9jp"

def test_supabase_api():
    """Test Supabase REST API connection"""
    print("🔌 Testing Supabase REST API connection...")
    print("")
    
    # Test 1: Check if API is accessible
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test basic connection
        response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=10)
        print(f"✓ API endpoint accessible (Status: {response.status_code})")
        print("")
        
        # Test 2: Try to query licenses table
        print("Testing licenses table access...")
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=headers,
            params={"select": "license_key"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully connected to licenses table!")
            print(f"  Current licenses count: {len(data)}")
            if data:
                print(f"  Sample license keys: {[row.get('license_key') for row in data[:3]]}")
            else:
                print("  Table is empty (no licenses yet)")
        elif response.status_code == 404:
            print("⚠ Table 'licenses' does not exist yet")
            print("  → Run schema.sql in Supabase SQL Editor to create it")
        elif response.status_code == 401:
            print("✗ Authentication failed")
            print("  → Check if API key is correct")
        elif response.status_code == 406:
            print("⚠ API not properly configured")
            print("  → Make sure REST API is enabled in Supabase")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
        
        print("")
        print("✅ Supabase REST API test completed!")
        
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed!")
        print("  → Supabase project might be paused")
        print("  → Go to https://supabase.com/dashboard and wake up your project")
    except requests.exceptions.Timeout:
        print("✗ Request timeout")
        print("  → Check your internet connection")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supabase_api()

