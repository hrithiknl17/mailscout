-- MailScout initial schema
-- Run this in Supabase SQL Editor (or psql against your Supabase project)
-- auth.users is managed by Supabase — we reference it but do not create it.

-- ────────────────────────────────────────────────────────────────
-- Enums
-- ────────────────────────────────────────────────────────────────

-- Type names must match SQLAlchemy's default: lowercase Python class name (no underscores).
CREATE TYPE IF NOT EXISTS verificationstatus AS ENUM (
    'deliverable',
    'undeliverable',
    'risky',
    'invalid_syntax',
    'dead_domain',
    'no_mail_server',
    'temporary_failure',
    'unknown'
);

CREATE TYPE IF NOT EXISTS jobstatus AS ENUM (
    'queued',
    'running',
    'completed',
    'failed'
);

-- ────────────────────────────────────────────────────────────────
-- verifications
-- ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS verifications (
    id               UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          TEXT              NOT NULL,
    email            TEXT              NOT NULL,
    status           verificationstatus NOT NULL,
    confidence       DOUBLE PRECISION  NOT NULL DEFAULT 0.0,
    reason           TEXT              NOT NULL DEFAULT '',
    mx_record        TEXT,
    is_catch_all     BOOLEAN           NOT NULL DEFAULT FALSE,
    is_disposable    BOOLEAN           NOT NULL DEFAULT FALSE,
    is_role          BOOLEAN           NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verifications_user_id     ON verifications (user_id);
CREATE INDEX IF NOT EXISTS idx_verifications_created_at  ON verifications (created_at DESC);

-- RLS: users can only see their own rows
ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY verifications_select ON verifications
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY verifications_insert ON verifications
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- ────────────────────────────────────────────────────────────────
-- jobs
-- ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS jobs (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             TEXT        NOT NULL,
    status              jobstatus   NOT NULL DEFAULT 'queued',
    total_emails        INTEGER     NOT NULL,
    processed           INTEGER     NOT NULL DEFAULT 0,
    deliverable_count   INTEGER     NOT NULL DEFAULT 0,
    risky_count         INTEGER     NOT NULL DEFAULT 0,
    undeliverable_count INTEGER     NOT NULL DEFAULT 0,
    dead_domain_count   INTEGER     NOT NULL DEFAULT 0,
    unknown_count       INTEGER     NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    result_csv_url      TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs (user_id);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY jobs_select ON jobs
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY jobs_insert ON jobs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);
