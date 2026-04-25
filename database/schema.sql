-- ─────────────────────────────────────────────────────────────────────────────
-- The Electric Curator — Portal API Database Schema
-- PostgreSQL 15
-- Current state: post-migration 010. Idempotent — safe to run on fresh or
-- existing databases. Seeds alembic_version so `alembic upgrade head` is a no-op.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─── Users ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id                       UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    email                    VARCHAR(255)  NOT NULL,
    username                 VARCHAR(100)  NOT NULL,
    hashed_password          VARCHAR(255)  NOT NULL,
    full_name                VARCHAR(255),
    avatar_url               TEXT,
    is_active                BOOLEAN       NOT NULL DEFAULT TRUE,
    is_verified              BOOLEAN       NOT NULL DEFAULT FALSE,
    refresh_token            TEXT,
    refresh_token_expires_at TIMESTAMPTZ,
    preferred_budget         VARCHAR(10),
    preferred_location       VARCHAR(255),
    preferred_location_lat   DOUBLE PRECISION,
    preferred_location_lng   DOUBLE PRECISION,
    preferred_categories     TEXT[],
    created_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email       ON users (email);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username    ON users (username);
CREATE        INDEX IF NOT EXISTS idx_users_active_email
    ON users (email) WHERE is_active = TRUE;

-- ─── Saved Events ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS saved_events (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id        TEXT        NOT NULL,
    event_title     TEXT,
    event_venue     TEXT,
    event_date      TEXT,
    event_time      TEXT,
    event_image_url TEXT,
    event_url       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_saved_events_user_event
    ON saved_events (user_id, event_id);
CREATE        INDEX IF NOT EXISTS idx_saved_events_user_id
    ON saved_events (user_id);

-- ─── Column reconciliation for pre-existing tables ───────────────────────────
-- CREATE TABLE IF NOT EXISTS skips the body when the table already exists, so
-- databases provisioned before migrations 006/008/009 are missing columns.
-- These ALTERs bring any old schema up to the post-009 state.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS preferred_location_lat DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS preferred_location_lng DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS preferred_categories   TEXT[];

ALTER TABLE saved_events
    ADD COLUMN IF NOT EXISTS event_url TEXT;

-- ─── Dropped tables (migration 007) ──────────────────────────────────────────
-- event_reviews was removed; drop if leftover from earlier deployment.
DROP TABLE IF EXISTS event_reviews;

-- ─── Alembic version stamp ───────────────────────────────────────────────────
-- Mark DB as at revision 009 so `alembic upgrade head` is a no-op and future
-- migrations chain cleanly. Fixes DuplicateTable on redeploy when tables were
-- created outside alembic.

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

DELETE FROM alembic_version WHERE version_num <> '010';
INSERT INTO alembic_version (version_num)
VALUES ('010')
ON CONFLICT (version_num) DO NOTHING;
