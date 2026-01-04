# License Verification API

Production-ready FastAPI backend for license activation and verification.

## Features

- ✅ License activation with machine binding
- ✅ Periodic license verification
- ✅ One license per machine enforcement
- ✅ PostgreSQL database (Supabase free tier)
- ✅ Production-ready error handling
- ✅ Pydantic validation

## Quick Start

### 1. Setup Supabase Database (Free Tier)

1. Go to [Supabase](https://supabase.com) and sign up/login
2. Create a new project
3. Go to **Settings** → **Database**
4. Copy the **Connection string** (URI format)
   - It looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
5. Set it as environment variable:

```bash
export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```

Or create a `.env` file:
```bash
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

1. Go to your Supabase project → **SQL Editor**
2. Click **"New query"**
3. Copy and paste the contents of `schema.sql`
4. Click **"Run"** to execute

This creates the `licenses` table in your Supabase PostgreSQL database.

> **Note:** The `init_db.py` script is available as an alternative method, but using SQL Editor is recommended.

### 4. Run the API

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 5. API Documentation

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
| license_key    | VARCHAR(255) (PK) | License key                    |
| machine_id     | VARCHAR(255) | Machine ID (NULL if not bound) |
| status         | VARCHAR(50) | active / revoked               |
| expired_at     | TIMESTAMP  | Expiration date                |
| activated_at   | TIMESTAMP  | First activation timestamp     |
| last_verify_at | TIMESTAMP  | Last verification timestamp    |

## Managing Licenses

### Add a License

Connect to Supabase SQL Editor or use psql:

```sql
INSERT INTO licenses (license_key, status, expired_at)
VALUES ('YOUR-LICENSE-KEY', 'active', '2025-12-31 23:59:59');
```

Or use Supabase Dashboard → SQL Editor to run the query.

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

### Step 3: Environment Variables

**Required:** Add `DATABASE_URL` environment variable in Render dashboard:

1. Go to your service → **Environment**
2. Add new environment variable:
   - **Key:** `DATABASE_URL`
   - **Value:** Your Supabase connection string
     ```
     postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
     ```

**Note:** `PORT` is automatically set by Render

### Step 4: Deploy

Render will automatically:
1. Clone your repository
2. Install dependencies
3. Start the FastAPI server

**Note:** The database table should already be created in Supabase using `schema.sql` before deployment.

### Important Notes

✅ **Database Persistence:**
- Using Supabase PostgreSQL ensures data persistence
- Database is hosted separately and won't be reset on deploy
- Supabase free tier includes:
  - 500 MB database storage
  - Unlimited API requests
  - Perfect for this use case

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
├── init_db.py       # Database initialization (Python script)
├── schema.sql       # Database schema (SQL file for Supabase)
├── requirements.txt # Python dependencies
├── README.md        # This file
└── .gitignore       # Git ignore rules
```

## Security Considerations

- ✅ Input validation with Pydantic
- ✅ HTTPS enforced on Render
- ✅ Database credentials stored in environment variables
- ⚠️ Consider adding API key authentication for production
- ⚠️ Consider rate limiting for public APIs
- ⚠️ Never commit `DATABASE_URL` to version control

## License

This project is for internal use.

