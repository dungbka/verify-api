"""
Database initialization script
Creates the licenses table if it doesn't exist
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("license.db")


def init_database():
    """Initialize database with licenses table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create licenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            license_key TEXT PRIMARY KEY,
            machine_id TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            expired_at TEXT,
            activated_at TEXT,
            last_verify_at TEXT
        )
    """)
    
    # Create index on machine_id for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_machine_id ON licenses(machine_id)
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH.absolute()}")


def seed_sample_license():
    """Seed a sample license for testing (optional)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if sample license already exists
    cursor.execute("SELECT license_key FROM licenses WHERE license_key = ?", ("DEMO-1234-5678",))
    if cursor.fetchone():
        print("✓ Sample license already exists")
        conn.close()
        return
    
    # Insert sample license (expires in 1 year)
    expired_at = (datetime.now() + timedelta(days=365)).isoformat()
    cursor.execute("""
        INSERT INTO licenses (license_key, machine_id, status, expired_at)
        VALUES (?, ?, ?, ?)
    """, ("DEMO-1234-5678", None, "active", expired_at))
    
    conn.commit()
    conn.close()
    print("✓ Sample license seeded: DEMO-1234-5678 (expires in 1 year)")


if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    
    # Uncomment the line below to seed a sample license
    # seed_sample_license()
    
    print("Database setup complete!")

