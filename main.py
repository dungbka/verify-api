"""
FastAPI License Verification API
Production-ready backend for license activation and verification
"""

from datetime import datetime
from typing import Optional
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Database path
DB_PATH = Path("license.db")

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
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_license(license_key: str) -> Optional[dict]:
    """Get license by license_key"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT license_key, machine_id, status, expired_at, activated_at, last_verify_at "
            "FROM licenses WHERE license_key = ?",
            (license_key,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def update_license(license_key: str, updates: dict):
    """Update license fields"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [license_key]
        cursor.execute(
            f"UPDATE licenses SET {set_clause} WHERE license_key = ?",
            values
        )
        conn.commit()
    finally:
        conn.close()


def is_expired(expired_at: Optional[str]) -> bool:
    """Check if license is expired"""
    if expired_at is None:
        return False
    try:
        expired_date = datetime.fromisoformat(expired_at)
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
    return {"status": "healthy"}


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

