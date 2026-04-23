-- ─────────────────────────────────────────────────────────────────────────────
-- The Electric Curator — Portal API Database Schema
-- PostgreSQL 15
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─── Users ───────────────────────────────────────────────────────────────────

CREATE TABLE users (
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
    created_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- UNIQUE constraints already create unique indexes; no additional plain indexes needed
CREATE UNIQUE INDEX uq_users_email    ON users (email);
CREATE UNIQUE INDEX uq_users_username ON users (username);
-- Partial index for login/register queries — only indexes active (non-deleted) users
CREATE        INDEX idx_users_active_email ON users (email) WHERE is_active = TRUE;

-- ─── Saved Events ─────────────────────────────────────────────────────────────

CREATE TABLE saved_events (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id        TEXT        NOT NULL,
    event_title     TEXT,
    event_venue     TEXT,
    event_date      TEXT,
    event_time      TEXT,
    event_image_url TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_saved_events_user_event ON saved_events (user_id, event_id);
CREATE        INDEX idx_saved_events_user_id   ON saved_events (user_id);

