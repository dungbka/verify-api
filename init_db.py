"""
Database initialization script
Creates the licenses table if it doesn't exist on PostgreSQL (Supabase)
"""

import os
from pathlib import Path
import psycopg2
from datetime import datetime, timedelta

# Try to load .env file if it exists (for local development)
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please set it before running this script.")


def init_database():
    """Initialize database with licenses table"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Create licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                license_key VARCHAR(255) PRIMARY KEY,
                machine_id VARCHAR(255),
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                expired_at TIMESTAMP,
                activated_at TIMESTAMP,
                last_verify_at TIMESTAMP
            )
        """)
        
        # Create index on machine_id for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_machine_id ON licenses(machine_id)
        """)
        
        conn.commit()
        print("✓ Database initialized successfully")
    except Exception as e:
        conn.rollback()
        print(f"✗ Error initializing database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def seed_sample_license():
    """Seed a sample license for testing (optional)"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Check if sample license already exists
        cursor.execute("SELECT license_key FROM licenses WHERE license_key = %s", ("DEMO-1234-5678",))
        if cursor.fetchone():
            print("✓ Sample license already exists")
            return
        
        # Insert sample license (expires in 1 year)
        expired_at = datetime.now() + timedelta(days=365)
        cursor.execute("""
            INSERT INTO licenses (license_key, machine_id, status, expired_at)
            VALUES (%s, %s, %s, %s)
        """, ("DEMO-1234-5678", None, "active", expired_at))
        
        conn.commit()
        print("✓ Sample license seeded: DEMO-1234-5678 (expires in 1 year)")
    except Exception as e:
        conn.rollback()
        print(f"✗ Error seeding sample license: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    
    # Uncomment the line below to seed a sample license
    # seed_sample_license()
    
    print("Database setup complete!")

