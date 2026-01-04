"""
FastAPI License Verification API
Production-ready backend for license activation and verification
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Try to load .env file if it exists (for local development)
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Database connection string from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please set it in Render dashboard Environment variables.")

# Connection pool - lazy initialization to avoid connection errors at startup
db_pool = None

def get_db_pool():
    """Get or create database connection pool (lazy initialization)"""
    global db_pool
    if db_pool is None:
        try:
            db_pool = SimpleConnectionPool(1, 20, DATABASE_URL)
        except Exception as e:
            # Log error but don't fail at startup - connection will be retried on first request
            print(f"Warning: Could not create database pool at startup: {e}")
            print("Connection will be retried on first database request.")
    return db_pool

# Initialize FastAPI app
app = FastAPI(
    title="License Verification API",
    description="Backend API for license activation and verification",
    version="1.0.0",
)

# CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class ActivateRequest(BaseModel):
    license_key: str = Field(..., min_length=1, description="License key to activate")
    machine_id: str = Field(..., min_length=1, description="Machine ID to bind with license")


class ActivateResponse(BaseModel):
    status: str = Field(..., description="Activation status")


class VerifyRequest(BaseModel):
    license_key: str = Field(..., min_length=1, description="License key to verify")
    machine_id: str = Field(..., min_length=1, description="Machine ID to verify against")


class VerifyResponse(BaseModel):
    valid: bool = Field(..., description="Whether the license is valid")


# Database utilities
def get_db_connection():
    """Get PostgreSQL database connection from pool"""
    pool = get_db_pool()
    if pool:
        try:
            return pool.getconn()
        except Exception:
            # If pool fails, try direct connection
            pass
    return psycopg2.connect(DATABASE_URL)


def return_db_connection(conn):
    """Return connection to pool"""
    if db_pool:
        db_pool.putconn(conn)
    else:
        conn.close()


def get_license(license_key: str) -> Optional[dict]:
    """Get license by license_key"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT license_key, machine_id, status, expired_at, activated_at, last_verify_at "
            "FROM licenses WHERE license_key = %s",
            (license_key,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        return_db_connection(conn)


def update_license(license_key: str, updates: dict):
    """Update license fields"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [license_key]
        cursor.execute(
            f"UPDATE licenses SET {set_clause} WHERE license_key = %s",
            values
        )
        conn.commit()
    finally:
        return_db_connection(conn)


def is_expired(expired_at) -> bool:
    """Check if license is expired"""
    if expired_at is None:
        return False
    try:
        # Handle both datetime object (from PostgreSQL) and string
        if isinstance(expired_at, datetime):
            expired_date = expired_at
        else:
            expired_date = datetime.fromisoformat(str(expired_at))
        return datetime.now() > expired_date
    except (ValueError, TypeError):
        return False


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "License Verification API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Test database connection
    db_status = "unknown"
    try:
        conn = get_db_connection()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
    
    return {
        "status": "healthy",
        "database": db_status
    }


@app.post("/activate", response_model=ActivateResponse, status_code=status.HTTP_200_OK)
async def activate(request: ActivateRequest):
    """
    Activate a license and bind it to a machine_id
    
    - First-time activation binds license to machine_id
    - License can only be bound to one machine
    """
    # Get license from database
    license_data = get_license(request.license_key)
    
    # Check if license exists
    if license_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license"
        )
    
    # Check if license is active
    if license_data["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License revoked"
        )
    
    # Check if license is expired
    if is_expired(license_data["expired_at"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License expired"
        )
    
    # Check machine_id binding
    current_machine_id = license_data["machine_id"]
    
    if current_machine_id is None:
        # First activation - bind machine_id
        now = datetime.now().isoformat()
        update_license(request.license_key, {
            "machine_id": request.machine_id,
            "activated_at": now
        })
        return ActivateResponse(status="activated")
    
    elif current_machine_id != request.machine_id:
        # License already bound to different machine
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License already activated"
        )
    
    else:
        # Already activated on same machine - update activated_at if needed
        if license_data["activated_at"] is None:
            now = datetime.now().isoformat()
            update_license(request.license_key, {"activated_at": now})
        return ActivateResponse(status="activated")


@app.post("/verify", response_model=VerifyResponse, status_code=status.HTTP_200_OK)
async def verify(request: VerifyRequest):
    """
    Verify a license status
    
    - Checks if license exists, is active, not expired, and matches machine_id
    - Updates last_verify_at timestamp
    """
    # Get license from database
    license_data = get_license(request.license_key)
    
    # Check if license exists
    if license_data is None:
        return VerifyResponse(valid=False)
    
    # Check if license is active
    if license_data["status"] != "active":
        return VerifyResponse(valid=False)
    
    # Check if license is expired
    if is_expired(license_data["expired_at"]):
        return VerifyResponse(valid=False)
    
    # Check machine_id match
    if license_data["machine_id"] != request.machine_id:
        return VerifyResponse(valid=False)
    
    # License is valid - update last_verify_at
    now = datetime.now().isoformat()
    update_license(request.license_key, {"last_verify_at": now})
    
    return VerifyResponse(valid=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

