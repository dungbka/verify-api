"""
FastAPI License Verification API
Production-ready backend for license activation and verification
Using Supabase REST API
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path
import requests

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

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://iwxrpjeowtnhsacaonhz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable__sHAilM6z41QSb72bXUckg_wYKIY9jp")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY environment variables are required. "
        "Please set them in Render dashboard Environment variables."
    )

# Supabase REST API headers
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

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


# Supabase REST API utilities
def get_license(license_key: str) -> Optional[dict]:
    """Get license by license_key using Supabase REST API"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=SUPABASE_HEADERS,
            params={
                "license_key": f"eq.{license_key}",
                "select": "license_key,machine_id,status,expired_at,activated_at,last_verify_at"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]
        elif response.status_code == 404:
            # Table doesn't exist
            return None
        elif response.status_code == 401:
            raise Exception("Supabase authentication failed. Check API key.")
        else:
            print(f"Supabase API error: {response.status_code} - {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Supabase: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def update_license(license_key: str, updates: dict):
    """Update license fields using Supabase REST API"""
    try:
        # Convert datetime to ISO format strings if needed
        formatted_updates = {}
        for key, value in updates.items():
            if isinstance(value, datetime):
                formatted_updates[key] = value.isoformat()
            else:
                formatted_updates[key] = value
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=SUPABASE_HEADERS,
            params={"license_key": f"eq.{license_key}"},
            json=formatted_updates,
            timeout=10
        )
        
        if response.status_code not in [200, 204]:
            print(f"Failed to update license: {response.status_code} - {response.text[:200]}")
            raise Exception(f"Failed to update license: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error updating license in Supabase: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error updating license: {e}")
        raise


def is_expired(expired_at) -> bool:
    """Check if license is expired"""
    if expired_at is None:
        return False
    try:
        # Handle both datetime object and string
        if isinstance(expired_at, datetime):
            expired_date = expired_at
        elif isinstance(expired_at, str):
            # Parse ISO format string
            expired_date = datetime.fromisoformat(expired_at.replace('Z', '+00:00'))
        else:
            return False
        return datetime.now() > expired_date.replace(tzinfo=None) if expired_date.tzinfo else datetime.now() > expired_date
    except (ValueError, TypeError, AttributeError):
        return False


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "License Verification API", "status": "running"}


@app.get("/health")
@app.head("/health")
async def health():
    """Health check endpoint with database status"""
    db_status = "unknown"
    try:
        # Test Supabase connection by making a simple query
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/licenses",
            headers=SUPABASE_HEADERS,
            params={"select": "license_key", "limit": "1"},
            timeout=5
        )
        
        if response.status_code == 200:
            db_status = "connected"
        elif response.status_code == 401:
            db_status = "authentication_error"
        elif response.status_code == 404:
            db_status = "table_not_found"
        else:
            db_status = f"error_{response.status_code}"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "supabase_url": SUPABASE_URL
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
    if license_data.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License revoked"
        )
    
    # Check if license is expired
    if is_expired(license_data.get("expired_at")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License expired"
        )
    
    # Check machine_id binding
    current_machine_id = license_data.get("machine_id")
    
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
        if license_data.get("activated_at") is None:
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
    if license_data.get("status") != "active":
        return VerifyResponse(valid=False)
    
    # Check if license is expired
    if is_expired(license_data.get("expired_at")):
        return VerifyResponse(valid=False)
    
    # Check machine_id match
    if license_data.get("machine_id") != request.machine_id:
        return VerifyResponse(valid=False)
    
    # License is valid - update last_verify_at
    now = datetime.now().isoformat()
    update_license(request.license_key, {"last_verify_at": now})
    
    return VerifyResponse(valid=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
