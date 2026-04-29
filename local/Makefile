COMPOSE := docker compose -f docker-compose.yml

.PHONY: help up up-full down reset logs logs-backend logs-firebase \
        seed-events migrate dev frontend-config psql build ps \
        pubsub-topics pubsub-sub pubsub-pull pubsub-listen \
        sink-logs sink-tail sink-clear dbt-build dbt-test \
        bq-query bq-swipes bq-tables bq-seed-eventos

help:
	@echo "The Electric Curator — local dev targets"
	@echo ""
	@echo "Run from the local/ directory (cd local) or with 'make -C local <target>'."
	@echo ""
	@echo "  make up              start default stack (no nginx frontend)"
	@echo "  make up-full         also start nginx-built frontend on :5173"
	@echo "  make down            stop services (keeps data volumes)"
	@echo "  make reset           stop + wipe Postgres and Firestore volumes"
	@echo "  make logs            tail all service logs"
	@echo "  make logs-backend    tail backend logs only"
	@echo "  make logs-firebase   tail Firestore emulator logs"
	@echo "  make seed-events     re-run the Firestore events fixture seed"
	@echo "  make migrate         run Alembic migrations against the local db"
	@echo "  make dev             run Vite dev server (frontend/portal)"
	@echo "  make frontend-config regenerate frontend/portal/public/public-config.json"
	@echo "  make psql            open psql inside the db container"
	@echo "  make build           rebuild all images"
	@echo "  make ps              show container status"
	@echo "  make pubsub-topics   list topics in the local emulator"
	@echo "  make pubsub-pull     pull + ack queued swipe messages once"
	@echo "  make pubsub-listen   poll continuously every 2s"
	@echo "  make sink-logs       tail logs of the local Pub/Sub→BQ sink"
	@echo "  make sink-tail       follow the sink JSONL file (envelope rows)"
	@echo "  make sink-clear      truncate the sink JSONL file"
	@echo "  make dbt-build       run dbt build against GCP dev dataset (needs ADC)"
	@echo "  make dbt-test        run dbt test against GCP dev dataset"
	@echo "  make bq-tables       list tables in the local BQ emulator"
	@echo "  make bq-swipes       SELECT * FROM raw.swipes_raw on the emulator"
	@echo "  make bq-query SQL=\"...\"  run arbitrary SQL on the emulator"
	@echo "  make bq-seed-eventos seed minimal events catalog into the emulator"

up:
	$(COMPOSE) up -d --build

up-full:
	$(COMPOSE) --profile full up -d --build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

logs-backend:
	$(COMPOSE) logs -f backend

logs-firebase:
	$(COMPOSE) logs -f firebase

seed-events:
	$(COMPOSE) run --rm --build seed-events

migrate:
	$(COMPOSE) run --rm --build migrate

dev:
	cd ../frontend/portal && npm run dev

FIREBASE_API_KEY ?=
FIREBASE_AUTH_DOMAIN ?=
FIREBASE_PROJECT_ID ?=

frontend-config:
	@jq -n \
	  --arg backend "http://localhost:8080" \
	  --arg apiKey "$(FIREBASE_API_KEY)" \
	  --arg authDomain "$(FIREBASE_AUTH_DOMAIN)" \
	  --arg projectId "$(FIREBASE_PROJECT_ID)" \
	  '{backendUrl: $$backend, firebase: {apiKey: $$apiKey, authDomain: $$authDomain, projectId: $$projectId}}' \
	  > ../frontend/portal/public/public-config.json
	@echo "Wrote frontend/portal/public/public-config.json"

psql:
	$(COMPOSE) exec db psql -U curator -d electric_curator

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

# ─── Pub/Sub emulator helpers ────────────────────────────────────────────────
# Emulator listens on host :8085. Project = demo-local. Topic = swipe-events.
PUBSUB_HOST := localhost:8085
PUBSUB_PROJECT := demo-local
PUBSUB_TOPIC := swipe-events
PUBSUB_SUB := swipe-events-debug

pubsub-topics:
	@curl -s http://$(PUBSUB_HOST)/v1/projects/$(PUBSUB_PROJECT)/topics | python3 -m json.tool

pubsub-sub:
	@curl -s -X PUT http://$(PUBSUB_HOST)/v1/projects/$(PUBSUB_PROJECT)/subscriptions/$(PUBSUB_SUB) \
		-H "Content-Type: application/json" \
		-d '{"topic":"projects/$(PUBSUB_PROJECT)/topics/$(PUBSUB_TOPIC)","ackDeadlineSeconds":10}' | python3 -m json.tool || true

pubsub-pull: pubsub-sub
	@curl -s -X POST http://$(PUBSUB_HOST)/v1/projects/$(PUBSUB_PROJECT)/subscriptions/$(PUBSUB_SUB):pull \
		-H "Content-Type: application/json" \
		-d '{"maxMessages":20,"returnImmediately":true}' \
		| python3 -c 'import sys,json,base64; d=json.load(sys.stdin); msgs=d.get("receivedMessages",[]); print(f"{len(msgs)} message(s)\n"); [print(json.dumps({"id":m["message"].get("messageId"),"attrs":m["message"].get("attributes",{}),"data":json.loads(base64.b64decode(m["message"]["data"]))}, indent=2)) for m in msgs]; ack=[m["ackId"] for m in msgs]; open("/tmp/.psack","w").write(json.dumps(ack))'
	@if [ -s /tmp/.psack ]; then \
		curl -s -X POST http://$(PUBSUB_HOST)/v1/projects/$(PUBSUB_PROJECT)/subscriptions/$(PUBSUB_SUB):acknowledge \
			-H "Content-Type: application/json" \
			-d "$$(printf '{"ackIds":%s}' $$(cat /tmp/.psack))" > /dev/null; \
	fi

pubsub-listen:
	@echo "Polling $(PUBSUB_TOPIC) every 2s. Ctrl-C to stop."
	@while true; do $(MAKE) --no-print-directory pubsub-pull; sleep 2; done

# ─── Pub/Sub → BQ sink helpers ───────────────────────────────────────────────
SINK_FILE := swipes_data/swipes_raw.jsonl

sink-logs:
	$(COMPOSE) logs -f pubsub-bq-sink

sink-tail:
	@mkdir -p swipes_data && touch $(SINK_FILE)
	@tail -f $(SINK_FILE)

sink-clear:
	@: > $(SINK_FILE) && echo "cleared $(SINK_FILE)"

# ─── dbt (runs against real GCP dev dataset; emulator has no BQ) ─────────────
DBT := docker run --rm \
    -v $(PWD)/../transformations:/app \
    -v $$HOME/.config/gcloud:/root/.config/gcloud:ro \
    -e GCP_PROJECT=$${GCP_PROJECT:?set GCP_PROJECT to a real GCP project} \
    -e DBT_DATASET=$${DBT_DATASET:-dbt_dev} \
    -w /app \
    --entrypoint dbt \
    ghcr.io/dbt-labs/dbt-bigquery:1.8.3

dbt-build:
	$(DBT) build --profiles-dir . --target dev

dbt-test:
	$(DBT) test --profiles-dir . --target dev

# ─── BigQuery emulator helpers ───────────────────────────────────────────────
BQ_HOST := localhost:9550
BQ_PROJECT := demo-local

bq-tables:
	@curl -s http://$(BQ_HOST)/bigquery/v2/projects/$(BQ_PROJECT)/datasets/raw/tables | python3 -m json.tool

bq-query:
	@if [ -z "$(SQL)" ]; then echo 'usage: make bq-query SQL="select 1"'; exit 1; fi
	@SQL="$(SQL)" python3 -c 'import json,os; print(json.dumps({"query":os.environ["SQL"],"useLegacySql":False}))' \
		| curl -s -X POST http://$(BQ_HOST)/bigquery/v2/projects/$(BQ_PROJECT)/queries \
			-H "Content-Type: application/json" --data-binary @- \
		| python3 -m json.tool

bq-swipes:
	@$(MAKE) --no-print-directory bq-query SQL="SELECT message_id, publish_time, data FROM raw.swipes_raw ORDER BY publish_time DESC LIMIT 20"

bq-seed-eventos:
	@curl -s -X POST http://$(BQ_HOST)/bigquery/v2/projects/$(BQ_PROJECT)/datasets/recomendacion_planes/tables/eventos/insertAll \
		-H "Content-Type: application/json" \
		-d '{"rows":[{"json":{"id":"evt-1","nombre":"Concierto Demo","ciudad":"Madrid","genero":"Rock","subgenero":"Indie","recinto_nombre":"Sala Local"}}]}' | python3 -m json.tool
