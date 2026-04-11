# Plan: Frontend-to-Backend Data Persistence

> **Status (2026-04-11):** All 8 phases implemented. Pending: run `alembic upgrade head` to apply migrations to the live DB, and set `FIREBASE_CREDENTIALS_JSON` / `GOOGLE_CLOUD_PROJECT` in the backend `.env`.

## Context
The app has a working auth/users layer (CloudSQL + FastAPI) and a functional frontend with several pages that collect data but don't persist it. Three types of data need to be saved:
1. **AI Planner chat sessions & itineraries** → Firestore (user requirement)
2. **Saved/bookmarked events** → CloudSQL (new table)
3. **Event reviews/ratings** → CloudSQL (new table)

Profile preferences (`preferred_budget`, `preferred_location`) already work via `PUT /api/v1/users/me`.

---

## What Gets Saved Where

| Data | Storage | Pages |
|---|---|---|
| Chat messages, itinerary, vibe/budget sliders | Firestore `plans` collection | `AIPlannerPage.tsx` |
| Bookmarked events | CloudSQL `saved_events` table | `ProfilePage.tsx` |
| Star ratings + review text | CloudSQL `event_reviews` table | `EventDetailsPage.tsx`, `ProfilePage.tsx` |

---

## Implementation Steps (sequential)

### Phase 1 — Backend Infrastructure ✅

**1.1** `requirements.txt` — append `firebase-admin==6.5.0`

**1.2** `app/config.py` — add two optional settings:
```python
GOOGLE_CLOUD_PROJECT: str = ""
FIREBASE_CREDENTIALS_JSON: str = ""  # path to service account JSON; empty = ADC
```

**1.3** Create `app/db/firestore.py`:
- `get_firestore()` — lazily initialises Firebase app (using cert file or ADC), returns `firestore_async.client()`
- Guard with `if not firebase_admin._apps` to avoid double-init

**1.4** `app/main.py` lifespan — call `get_firestore()` at startup so the Firebase app initialises once

---

### Phase 2 — CloudSQL Migrations + ORM Models ✅

**2.1** `database/versions/002_create_saved_events_table.py`
```
saved_events: id (UUID PK), user_id (FK→users CASCADE), event_id (VARCHAR 255),
  event_title, event_venue, event_date, event_time, event_image_url,
  created_at TIMESTAMPTZ
UNIQUE(user_id, event_id)
```
Denormalised snapshot fields so bookmarks survive if the event catalogue changes.

**2.2** `database/versions/003_create_event_reviews_table.py`
```
event_reviews: id (UUID PK), user_id (FK→users CASCADE), event_id (VARCHAR 255),
  rating SMALLINT CHECK(1–5), review_text TEXT,
  created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
UNIQUE(user_id, event_id)  ← one review per user per event
```

**2.3** `app/models/saved_event.py` — `SavedEvent` ORM (mirrors migration above)

**2.4** `app/models/event_review.py` — `EventReview` ORM (mirrors migration above)

**2.5** `database/env.py` — import both new models so Alembic autogenerate sees them

**2.6** Run `alembic upgrade head` from `database/`

---

### Phase 3 — Pydantic Schemas ✅

**3.1** `app/schemas/plan.py`
- `PlanMessage(role, content, timestamp)`
- `PlanItinerary(stops, budget, vibe_chaos 0-100, vibe_hidden 0-100)`
- `PlanCreate`, `PlanUpdate` (messages = full replacement list), `PlanRead`

**3.2** `app/schemas/saved_event.py` — `SavedEventCreate`, `SavedEventRead`

**3.3** `app/schemas/event_review.py` — `EventReviewCreate`, `EventReviewUpdate`, `EventReviewRead`

---

### Phase 4 — API Endpoints ✅

**4.1** `app/api/v1/endpoints/plans.py` (Firestore-backed)
- `GET /plans` — list user's plans (filter by user_id, order by updated_at desc)
- `POST /plans` → 201
- `GET /plans/{plan_id}` — ownership check
- `PUT /plans/{plan_id}` — partial update (title / messages / itinerary)
- `DELETE /plans/{plan_id}` → 204

Firestore document path: `plans/{auto_id}` with `user_id` field for ownership.

**4.2** `app/api/v1/endpoints/saved_events.py` (SQLAlchemy)
- `GET /users/me/saved-events`
- `POST /users/me/saved-events` → 201 (IntegrityError → 409)
- `DELETE /users/me/saved-events/{event_id}` → 204

**4.3** `app/api/v1/endpoints/reviews.py` (SQLAlchemy)
- `POST /events/{event_id}/reviews` → 201 (IntegrityError → 409)
- `GET /events/{event_id}/reviews` (public)
- `GET /users/me/reviews`
- `PUT /users/me/reviews/{review_id}`

---

### Phase 5 — Router Wiring ✅

**5.1** `app/api/v1/router.py` — include `plans.router`, `saved_events.router`, `reviews.router`
(reviews has no shared prefix — it mounts `/events/...` and `/users/me/reviews` directly)

---

### Phase 6 — Frontend: `src/api.ts` ✅

Add TS types: `PlanMessage`, `PlanItinerary`, `PlanRead`, `PlanCreate`, `PlanUpdate`, `SavedEventRead`, `SavedEventCreate`, `EventReviewRead`, `EventReviewCreate`, `EventReviewUpdate`

Add functions:
- `apiListPlans`, `apiCreatePlan`, `apiGetPlan`, `apiUpdatePlan`, `apiDeletePlan`
- `apiListSavedEvents`, `apiSaveEvent`, `apiUnsaveEvent`
- `apiCreateReview`, `apiListEventReviews`, `apiListMyReviews`, `apiUpdateReview`

---

### Phase 7 — Frontend Page Wiring ✅

**7.1** `AIPlannerPage.tsx`
- `useEffect` on mount → `apiListPlans()`, load most recent session into `messages` + set `activePlanId`
- First user message → `apiCreatePlan(...)` → store returned `plan_id`
- Each message send → `apiUpdatePlan(activePlanId, { messages: [...] })` (fire-and-forget)
- Vibe/budget slider changes → `apiUpdatePlan(activePlanId, { itinerary: { budget, vibe_chaos, vibe_hidden } })`
- Initial `messages` state: `[]` (not mock data)

**7.2** `ProfilePage.tsx`
- Remove `savedEvents` + `historyEvents` mock data imports
- `useEffect` on mount → `Promise.all([apiListSavedEvents(), apiListMyReviews()])`
- Saved events: render from API; "unsave" button → `apiUnsaveEvent(event.event_id)`
- History/reviews: items with `review_text` = reviewed, without = pending
- Review submit → `apiCreateReview(eventId, { rating, review_text })`
- Review edit → `apiUpdateReview(review.id, { rating, review_text })`
- **Note:** JSX uses `event.imageUrl` but API returns `event_image_url` — use a local mapper to adapt field names

**7.3** `EventDetailsPage.tsx`
- `useEffect` on mount → `apiListEventReviews(eventId)`, find `myReview` by `user_id`
- Pre-fill `rating` and `reviewText` if `myReview` exists
- Submit button: if `myReview` exists → `apiUpdateReview`, else → `apiCreateReview`
- **Note:** `eventId` currently hardcoded; derive from `useParams()` when routing is wired

---

### Phase 8 — Schema Doc Sync ✅

Append the two new `CREATE TABLE` blocks to `database/schema.sql` to keep it consistent with migrations.

---

## Critical Files

| File | Change type |
|---|---|
| `backend/portal-api/requirements.txt` | Add `firebase-admin` |
| `backend/portal-api/app/config.py` | New Firestore config fields |
| `backend/portal-api/app/db/firestore.py` | **New** |
| `backend/portal-api/app/main.py` | Init Firestore in lifespan |
| `database/versions/002_create_saved_events_table.py` | **New** |
| `database/versions/003_create_event_reviews_table.py` | **New** |
| `backend/portal-api/app/models/saved_event.py` | **New** |
| `backend/portal-api/app/models/event_review.py` | **New** |
| `database/env.py` | Import new models |
| `backend/portal-api/app/schemas/plan.py` | **New** |
| `backend/portal-api/app/schemas/saved_event.py` | **New** |
| `backend/portal-api/app/schemas/event_review.py` | **New** |
| `backend/portal-api/app/api/v1/endpoints/plans.py` | **New** |
| `backend/portal-api/app/api/v1/endpoints/saved_events.py` | **New** |
| `backend/portal-api/app/api/v1/endpoints/reviews.py` | **New** |
| `backend/portal-api/app/api/v1/router.py` | Add 3 new routers |
| `frontend/portal/src/api.ts` | New types + functions |
| `frontend/portal/src/pages/AIPlannerPage.tsx` | Wire plan API |
| `frontend/portal/src/pages/ProfilePage.tsx` | Wire saved events + reviews |
| `frontend/portal/src/pages/EventDetailsPage.tsx` | Wire review API |
| `database/schema.sql` | Append new table DDL |

---

## Verification

1. **Backend**: Start the API locally, hit `GET /api/docs` — confirm `/plans`, `/users/me/saved-events`, `/events/{event_id}/reviews`, `/users/me/reviews` appear
2. **Migrations**: Run `alembic upgrade head` and confirm `saved_events` and `event_reviews` tables are created
3. **Plans (Firestore)**: Login in the frontend, open the AI Planner, send a message — verify a document is created in the Firestore `plans` collection; refresh the page — verify messages are restored
4. **Saved events**: On the Profile page, verify saved events load from the API (empty list, not mock data); add a save from another page and confirm it appears
5. **Reviews**: On Event Details page, submit a review — verify it persists on page refresh; verify the review appears under "History" in Profile
