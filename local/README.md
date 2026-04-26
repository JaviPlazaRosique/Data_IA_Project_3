# Local development

Full local stack for **The Electric Curator** — Postgres, Firestore emulator,
FastAPI backend, and (optionally) the nginx-built frontend. Runs fully offline
with seeded test data.

## Prerequisites

- Docker + Docker Compose v2
- Node 22+ (only if you want Vite hot-reload — not required for the Docker-only flow)

## Quick start

```bash
# from the repo root
cp .env.example .env
cd local
make up            # or from the repo root: make -C local up
```

> All `make` targets below assume you're inside `local/`. From the repo root
> use `make -C local <target>` instead.

On first boot the stack will:

1. Start Postgres on `localhost:5433`.
2. Run Alembic migrations once.
3. Seed two test users.
4. Start the Firestore emulator on `localhost:8081` (UI at `localhost:4000`).
5. Seed six fixture events into the `eventos` collection.
6. Start the Pub/Sub emulator on `localhost:8085` with topic `swipe-events` pre-created.
7. Start the FastAPI backend on `localhost:8080`.

When all one-shot services have exited and `backend` + `firebase` are running,
you're ready.

## Frontend — two ways

### Vite dev (hot-reload, default)

The compose stack leaves port 5173 free. Run Vite from the host:

```bash
cd frontend/portal
npm install    # first time only
npm run dev
```

Open <http://localhost:5173>. The page fetches `/public-config.json`, which
points at `http://localhost:8080` (the containerised backend).

> `frontend/portal/public/public-config.json` is gitignored. If yours is
> missing, `make frontend-config` regenerates it.

### Nginx production build (inside Docker)

```bash
make up-full    # from local/ — or: make -C local up-full from the root
```

Serves the built SPA on `http://localhost:5173`. Useful for sanity-checking
the production bundle before deploy.

## Test credentials

| Email | Password |
|-------|----------|
| `alice@example.com` | `Alice1234!` |
| `bob@example.com` | `Bob1234!` |

Both users are seeded by `local/seed.py` on first migrate.

## Key URLs

| What | URL |
|------|-----|
| Frontend (Vite dev) | <http://localhost:5173> |
| Backend API | <http://localhost:8080> |
| OpenAPI docs | <http://localhost:8080/docs> |
| Firestore Emulator UI | <http://localhost:4000> |
| Pub/Sub Emulator | `localhost:8085` (project `demo-local`, topic `swipe-events`) |
| Postgres | `localhost:5433` (user: `curator`, db: `electric_curator`) |

## Seeded Firestore events

`local/seed_events.py` writes six fixtures into `eventos` — three in Madrid,
one each in Barcelona, Valencia, and Sevilla — covering `Music`, `Arts &
Theatre`, `Film`, and `Sports` segments so every pin color shows on the map.
Safe to re-run (`make seed-events`) — documents are upserted by id.

## Common commands

```bash
make up             # start the default stack (no nginx frontend)
make up-full        # also start the nginx-built frontend on :5173
make down           # stop all services, keep data volumes
make reset          # stop + delete volumes (wipes Postgres + Firestore)
make logs           # tail logs from all services
make logs-backend   # tail backend only
make seed-events    # re-run the Firestore fixtures seed
make dev            # cd frontend/portal && npm run dev
make psql           # open psql inside the db container
```

## Troubleshooting

**Port already in use.** Another process holds 5433/8080/5173/8081/4000.
`lsof -i :5173` to find it; either stop it or edit the port mapping in
`local/docker-compose.yml`.

**Empty Discover / Map pages.** The `seed-events` container probably raced
the Firestore emulator. Re-run: `make seed-events`. Verify fixtures in the
[emulator UI](http://localhost:4000/firestore).

**CORS error from Vite.** The backend allows `http://localhost:5173` and
`http://localhost:5174`. If Vite picks a different port, either pin it
(`vite --port 5173`) or add the new origin to `CORS_ORIGINS` in
`local/docker-compose.yml` and restart the backend.

**Backend won't start — "Database configuration is missing".** `.env` wasn't
loaded. Make sure you ran `cp .env.example .env` at the repo root and are
invoking compose from there (the `Makefile` does this for you).

**Stale cached builds.** `docker compose -f local/docker-compose.yml build --no-cache`
then `make up`.

## Pub/Sub → BigQuery sink + BigQuery emulator (local replica)

Prod uses a native Pub/Sub BigQuery subscription writing every swipe envelope
to `raw.swipes_raw`. Locally, two containers reproduce that:

1. **`bigquery-emulator`** — `goccy/bigquery-emulator` exposes the BigQuery
   REST API on `localhost:9550` (host 9050 collides with Tor on most Linux installs, so the host port is remapped; container port stays 9050 — the sink talks to it as `bigquery-emulator:9050` over the docker network). Datasets `raw`, `recomendacion_planes`,
   `dbt_dev` and tables `raw.swipes_raw`, `recomendacion_planes.eventos` are
   pre-created from `local/bq_seed.yaml` on boot. State is in-memory — restart
   wipes all data.
2. **`pubsub-bq-sink`** — Python subscriber on `swipe-events-sub` that calls
   the BigQuery emulator REST API to insert each envelope row. Also writes
   the same row to `local/swipes_data/swipes_raw.jsonl` for quick eyeballing.

```bash
make up
make sink-tail                # follow the JSONL while you swipe
make bq-tables                # list tables in the raw dataset
make bq-swipes                # SELECT recent rows from raw.swipes_raw
make bq-query SQL="SELECT count(*) FROM raw.swipes_raw"
make bq-seed-eventos          # one demo row in recomendacion_planes.eventos
```

Caveats:
- The emulator implements the REST API and a SQL subset; some BigQuery
  functions (e.g. complex `JSON_VALUE` paths, window functions) may not be
  fully supported. Treat it as a smoke-test of the ingest contract, not full
  parity with prod.
- dbt-bigquery does not have a first-class custom-endpoint setting, so
  `make dbt-build` still targets a real GCP dev dataset — see below.

`local/swipes_data/` is gitignored.

## dbt transformations

The dbt project lives at `transformations/`. BigQuery has no local emulator,
so dbt is always executed against a real GCP dev dataset. Set up ADC once,
then run targets via Docker (no local Python install required):

```bash
gcloud auth application-default login
export GCP_PROJECT=project3grupo3
export DBT_DATASET=dbt_dev    # any sandbox dataset you can write to
make dbt-build                # dbt build against $GCP_PROJECT.$DBT_DATASET
make dbt-test                 # tests only
```

The dev profile reads from `raw.swipes_raw` + `recomendacion_planes.eventos`
in the live project and writes models into `$DBT_DATASET`. Use a personal
sandbox dataset to avoid colliding with prod marts.

## Inspecting swipe events (Pub/Sub emulator)

Left/right swipes in QuickMatch publish to the `swipe-events` topic on the
Pub/Sub emulator. The favorite button is a separate action that writes to the
`saved_events` table in Postgres and does **not** publish to Pub/Sub. Pull
queued swipe messages with `gcloud` pointed at the emulator:

```bash
export PUBSUB_EMULATOR_HOST=localhost:8085
export PUBSUB_PROJECT_ID=demo-local
gcloud pubsub subscriptions create swipe-events-debug --topic=swipe-events --project=demo-local
gcloud pubsub subscriptions pull swipe-events-debug --auto-ack --limit=10 --project=demo-local
```

Or hit the emulator REST API directly:

```bash
curl http://localhost:8085/v1/projects/demo-local/topics
```

Topic state is in-memory — restarting the `pubsub` container drops queued
messages and the subscription. The `swipe-events` topic itself is recreated
automatically on boot from `PUBSUB_PROJECT1` in `docker-compose.yml`.
