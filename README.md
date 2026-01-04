# License Verification API

Production-ready FastAPI backend for license activation and verification.

## Features

- ✅ License activation with machine binding
- ✅ Periodic license verification
- ✅ One license per machine enforcement
- ✅ SQLite database (lightweight)
- ✅ Production-ready error handling
- ✅ Pydantic validation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

This creates `license.db` with the `licenses` table.

### 3. Run the API

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### POST /activate

Activate a license and bind it to a machine.

**Request:**
```json
{
  "license_key": "XXXX-XXXX",
  "machine_id": "HASH"
}
```

**Response (success):**
```json
{
  "status": "activated"
}
```

**Errors:**
- `400 Invalid license` - License doesn't exist
- `400 License revoked` - License status is not active
- `400 License expired` - License has expired
- `400 License already activated` - License is bound to different machine

### POST /verify

Verify a license status.

**Request:**
```json
{
  "license_key": "XXXX-XXXX",
  "machine_id": "HASH"
}
```

**Response:**
```json
{
  "valid": true
}
```

Returns `valid: false` if license is invalid, expired, revoked, or machine_id doesn't match.

## Database Schema

### licenses table

| Field          | Type       | Description                    |
| -------------- | ---------- | ------------------------------ |
| license_key    | TEXT (PK)  | License key                    |
| machine_id     | TEXT       | Machine ID (NULL if not bound) |
| status         | TEXT       | active / revoked               |
| expired_at     | TEXT (ISO) | Expiration date                |
| activated_at   | TEXT (ISO) | First activation timestamp     |
| last_verify_at | TEXT (ISO) | Last verification timestamp    |

## Managing Licenses

### Add a License

Connect to the database and insert:

```sql
INSERT INTO licenses (license_key, status, expired_at)
VALUES ('YOUR-LICENSE-KEY', 'active', '2025-12-31T23:59:59');
```

### Reset License (Re-issue)

To allow a license to be activated on a different machine:

```sql
UPDATE licenses 
SET machine_id = NULL, activated_at = NULL 
WHERE license_key = 'YOUR-LICENSE-KEY';
```

### Revoke License

```sql
UPDATE licenses 
SET status = 'revoked' 
WHERE license_key = 'YOUR-LICENSE-KEY';
```

## Deploy to Render (Free Tier)

### Prerequisites

1. GitHub account
2. Render account (sign up at https://render.com)

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/verrfy-api.git
git push -u origin main
```

### Step 2: Create Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

   **Settings:**
   - **Name:** `verrfy-api` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python init_db.py`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

5. Click **"Create Web Service"**

### Step 3: Environment Variables (Optional)

If needed, you can add environment variables in Render dashboard:
- `PORT` - Automatically set by Render
- Add any custom configs here

### Step 4: Deploy

Render will automatically:
1. Clone your repository
2. Install dependencies
3. Run `init_db.py` to create database
4. Start the FastAPI server

### Important Notes for Render Free Tier

⚠️ **Persistent Storage:**
- Render free tier **does NOT provide persistent disk storage**
- SQLite database will be **reset on each deploy**
- For production, consider:
  - Using Render PostgreSQL (paid)
  - Using external database (Supabase, Railway, etc.)
  - Or upgrade to paid tier with persistent disk

**Workaround for Free Tier:**
- Use external SQLite hosting (e.g., Dropbox, Google Drive with sync)
- Or migrate to PostgreSQL on a free tier service (Supabase, Railway)

### Step 5: Access Your API

After deployment, Render provides a URL like:
```
https://verrfy-api.onrender.com
```

Test endpoints:
- Health: `https://verrfy-api.onrender.com/health`
- Docs: `https://verrfy-api.onrender.com/docs`

## Development

### Run with Auto-reload

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Test Endpoints

```bash
# Activate
curl -X POST http://localhost:8000/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "DEMO-1234-5678", "machine_id": "machine-123"}'

# Verify
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"license_key": "DEMO-1234-5678", "machine_id": "machine-123"}'
```

## Project Structure

```
verrfy-api/
├── main.py          # FastAPI application
├── init_db.py       # Database initialization
├── requirements.txt # Python dependencies
├── README.md        # This file
├── license.db       # SQLite database (created after init)
└── .gitignore       # Git ignore rules
```

## Security Considerations

- ✅ Input validation with Pydantic
- ✅ HTTPS enforced on Render
- ⚠️ Consider adding API key authentication for production
- ⚠️ Consider rate limiting for public APIs
- ⚠️ Use environment variables for sensitive configs

## License

This project is for internal use.

