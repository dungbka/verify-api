-- License Verification API - Database Schema
-- Run this script in Supabase SQL Editor to create the licenses table

-- Create licenses table
CREATE TABLE IF NOT EXISTS licenses (
    license_key VARCHAR(255) PRIMARY KEY,
    machine_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    expired_at TIMESTAMP,
    activated_at TIMESTAMP,
    last_verify_at TIMESTAMP
);

-- Create index on machine_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_machine_id ON licenses(machine_id);

-- Optional: Insert a sample license for testing
-- Uncomment the lines below if you want to seed a test license
-- INSERT INTO licenses (license_key, machine_id, status, expired_at)
-- VALUES ('DEMO-1234-5678', NULL, 'active', NOW() + INTERVAL '1 year')
-- ON CONFLICT (license_key) DO NOTHING;

