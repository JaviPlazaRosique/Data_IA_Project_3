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
    created_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_users_email    ON users (email);
CREATE UNIQUE INDEX uq_users_username ON users (username);
CREATE        INDEX idx_users_email   ON users (email);
CREATE        INDEX idx_users_username ON users (username);
