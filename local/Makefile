COMPOSE := docker compose -f docker-compose.yml

.PHONY: help up up-full down reset logs logs-backend logs-firebase \
        seed-events dev frontend-config psql build ps

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
	@echo "  make dev             run Vite dev server (frontend/portal)"
	@echo "  make frontend-config regenerate frontend/portal/public/public-config.json"
	@echo "  make psql            open psql inside the db container"
	@echo "  make build           rebuild all images"
	@echo "  make ps              show container status"

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

dev:
	cd ../frontend/portal && npm run dev

frontend-config:
	@echo '{"backendUrl": "http://localhost:8080"}' > ../frontend/portal/public/public-config.json
	@echo "Wrote frontend/portal/public/public-config.json"

psql:
	$(COMPOSE) exec db psql -U curator -d electric_curator

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps
