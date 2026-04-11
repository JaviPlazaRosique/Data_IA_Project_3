# GDPR Remediation Plan — The Electric Curator

> **Last updated:** April 2026  
> **Status:** All Phase 1 and Phase 2 items implemented. Phase 3 implemented.

---

## Audit Summary

A pre-launch GDPR audit identified **14 findings** (4 High, 7 Medium, 3 Low) across the backend
(FastAPI + CloudSQL + Firestore) and frontend (React). The core issue was a solid technical
foundation entirely missing the legal/transparency layer. All findings are addressed below.

---

## Phase 1 — Critical Code Changes ✅

### 1.1 Hash refresh tokens at rest — Art. 32 🔴 HIGH
**Files changed:**
- `backend/portal-api/app/core/security.py` — added `hash_token()` using SHA-256
- `backend/portal-api/app/api/v1/endpoints/auth.py` — login/refresh store and compare hashed tokens
- `database/versions/005_clear_refresh_tokens.py` — migration invalidates all plain-text tokens

Refresh tokens are now stored as 64-char SHA-256 hex digests. Users had to re-login once after
migration 005 ran.

### 1.2 True erasure endpoint — Art. 17 🔴 HIGH
**File changed:** `backend/portal-api/app/api/v1/endpoints/users.py`

Added `DELETE /api/v1/users/me/data` — requires `{"confirm": "DELETE MY ACCOUNT"}`:
1. Deletes all Firestore plans for the user
2. Hard-deletes the user row — `ON DELETE CASCADE` removes `saved_events` and `event_reviews`

The existing `DELETE /api/v1/users/me` (soft-delete / `is_active = False`) is retained for
account deactivation. It does not constitute GDPR erasure.

### 1.3 Firestore plan TTL / retention — Art. 5(1)(e) 🔴 HIGH
**File changed:** `backend/portal-api/app/api/v1/endpoints/plans.py`

Every plan document now includes an `expires_at` field (ISO timestamp = now + 365 days).
On every `PUT /plans/{plan_id}`, `expires_at` is extended (activity resets the clock).

**Action required in GCP Console:** Enable Firestore TTL policy on field `expires_at` in
collection `plans` (Firestore → Indexes → TTL). Firestore handles deletion automatically.

### 1.4 Data export endpoint — Art. 15 / Art. 20 🔴 HIGH
**File changed:** `backend/portal-api/app/api/v1/endpoints/users.py`

Added `GET /api/v1/users/me/export` — returns a JSON file (`my-data.json`) containing:
- User profile
- Saved events
- Reviews
- Note directing user to `GET /api/v1/plans` for AI planning conversations

### 1.5 In-app AI processing disclosure — Art. 13 / Art. 6 🟡 MEDIUM
**File changed:** `frontend/portal/src/pages/AIPlannerPage.tsx`

Added dismissible info banner (dismissed state stored in `localStorage` key
`planner_disclosure_seen`):

> "Your conversations are saved to your account so you can continue planning later. Privacy Notice"

Shown only when the user is authenticated.

### 1.6 Privacy Notice page — Art. 13 🔴 HIGH
**Files changed:**
- `frontend/portal/src/pages/PrivacyPage.tsx` — full Art. 13 privacy notice
- `frontend/portal/src/App.tsx` — added route `/privacy` + `StorageNotice` banner
- `frontend/portal/src/pages/RegisterPage.tsx` — required privacy consent checkbox
- `frontend/portal/src/components/layout/Footer.tsx` — Privacy Policy link wired to `/privacy`

The Privacy Notice covers all Art. 13 mandatory fields. Placeholders (`[like this]`) must be
completed with real organisation details and reviewed by a DPO/lawyer before launch.

---

## Phase 2 — Documentation ✅

### 2.1 Record of Processing Activities — Art. 30
**File:** `docs/gdpr/ropa.md`

Covers 6 processing activities: account management, saved events, reviews, AI planning,
event catalogue, weather data.

### 2.2 Processors list / DPA tracking — Art. 28
**File:** `docs/gdpr/processors.md`

Processor register covering GCP, Firestore, Ticketmaster, Eventbrite, Google Places, Open-Meteo
with DPA status and transfer mechanism for each.

**Action required:** Accept Google Cloud DPA in GCP Console. Review Ticketmaster and Eventbrite
T&Cs for potential joint controller relationship.

### 2.3 Breach response procedure — Art. 33–34
**File:** `docs/gdpr/breach_response.md`

6-step procedure: detection → containment → risk assessment → AEPD notification (72h) →
user notification → post-incident review. Includes incident log template.

### 2.4 DPIA screening note — Art. 35
**File:** `docs/gdpr/dpia_notes.md`

Screening assessment for the AI personalisation pipeline. Conclusion: full DPIA not required at
MVP. Revisit when a third-party LLM API is integrated or user base exceeds ~10,000.

---

## Phase 3 — Post-launch Hardening ✅

### 3.1 Content Security Policy headers — Art. 32 / Art. 25
**File changed:** `backend/portal-api/app/main.py`

Added `CSPMiddleware` (Starlette `BaseHTTPMiddleware`):
- `Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none';`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

Long-term: migrate auth tokens from `localStorage` to `httpOnly; Secure; SameSite=Strict` cookies.

### 3.2 Request-level audit logging — Art. 5(2)
**File changed:** `backend/portal-api/app/main.py`

Added `AuditLogMiddleware` — logs `method`, `path`, `status`, `user_id` (extracted from JWT,
never bodies), and `duration_ms` as structured JSON to stdout → Cloud Logging.

**Action required:** Set Cloud Logging retention to 90 days (GCP Console → Cloud Logging →
Log buckets → `_Default` → Edit retention).

### 3.3 localStorage consent notice — ePrivacy
**File changed:** `frontend/portal/src/App.tsx`

`StorageNotice` component — shown on first visit, dismissed state in `localStorage` key
`storage_notice_seen`:

> "This site uses session storage for authentication only. No tracking cookies. [Privacy Notice] [OK]"

### 3.4 Breach response procedure ✅
See Phase 2.3 — `docs/gdpr/breach_response.md`.

### 3.5 DPIA notes ✅
See Phase 2.4 — `docs/gdpr/dpia_notes.md`.

---

## Pre-Launch Checklist

### Organisation details (must be completed before going live)
- [ ] Replace all `[Organisation Name]`, `[Address]`, `[privacy@yourdomain.com]` placeholders in `PrivacyPage.tsx`
- [ ] Privacy Notice reviewed by a qualified DPO or data protection lawyer
- [ ] RoPA (`docs/gdpr/ropa.md`) reviewed and signed off

### GCP Infrastructure
- [ ] Enable Firestore TTL policy on field `expires_at` in collection `plans`
- [ ] Accept Google Cloud DPA in GCP Console
- [ ] Pin CloudSQL and Cloud Run to `europe-west1` (or confirm chosen EU region)
- [ ] Set Cloud Logging retention to 90 days
- [ ] Review Ticketmaster / Eventbrite T&Cs for joint controller implications

### Testing
- [ ] **Erasure**: Create test user → add saved events, reviews, plans → call `DELETE /api/v1/users/me/data` → confirm all data deleted in CloudSQL and Firestore
- [ ] **Token hashing**: Login → inspect DB `refresh_token` column — must be 64-char hex string
- [ ] **Plan TTL**: Create plan → verify `expires_at` field exists; update plan → verify `expires_at` extended
- [ ] **Export**: `GET /api/v1/users/me/export` → verify JSON contains profile, saved_events, reviews
- [ ] **Privacy page**: Navigate to `/#/privacy` → page loads correctly
- [ ] **Register consent**: Registration form blocks submit until privacy checkbox checked
- [ ] **AI disclosure**: Open planner while logged in → disclosure banner appears; dismiss → does not reappear
- [ ] **Storage notice**: First visit → `StorageNotice` banner appears; click OK → does not reappear
- [ ] **CSP headers**: `curl -I https://your-api/api/health` → verify CSP, X-Frame-Options, X-Content-Type-Options present
- [ ] **Audit log**: Make authenticated API call → Cloud Logging shows structured JSON log with `user_id`

---

## Finding Index

| # | Severity | Article | Finding | Status |
|---|----------|---------|---------|--------|
| 1 | 🔴 High | Art. 13 | No privacy notice | ✅ Fixed |
| 2 | 🔴 High | Art. 17 | No real erasure endpoint | ✅ Fixed |
| 3 | 🔴 High | Art. 5(1)(e) | No Firestore retention / TTL | ✅ Fixed |
| 4 | 🔴 High | Art. 32 | Refresh tokens stored plain-text | ✅ Fixed |
| 5 | 🟡 Medium | Art. 28 | No DPA tracking for processors | ✅ Documented |
| 6 | 🟡 Medium | Art. 44–49 | GCP region not pinned | ⚠️ Action required |
| 7 | 🟡 Medium | Art. 30 | No Record of Processing Activities | ✅ Documented |
| 8 | 🟡 Medium | Art. 32 / Art. 25 | No CSP / security headers | ✅ Fixed |
| 9 | 🟡 Medium | Art. 13 / Art. 6 | No AI processing disclosure | ✅ Fixed |
| 10 | 🟡 Medium | Art. 15 / Art. 20 | No data export endpoint | ✅ Fixed |
| 11 | 🟡 Medium | Art. 33–34 | No breach response procedure | ✅ Documented |
| 12 | 🟢 Low | ePrivacy | No localStorage / session storage notice | ✅ Fixed |
| 13 | 🟢 Low | Art. 35 | No DPIA screening for AI pipeline | ✅ Documented |
| 14 | 🟢 Low | Art. 5(2) | No request-level audit logging | ✅ Fixed |
