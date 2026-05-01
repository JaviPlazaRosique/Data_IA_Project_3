from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SPECS_DIR = BASE_DIR / "specs"


def contract_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Swipe Event Contract v2",
        "type": "object",
        "required": [
            "schema_version",
            "event_id",
            "direction",
            "swiped_at",
            "session_id",
            "recommendation_context",
            "event_snapshot",
        ],
        "properties": {
            "schema_version": {"type": "string", "const": "2.0"},
            "event_id": {"type": "string"},
            "direction": {"type": "string", "enum": ["left", "right"]},
            "swiped_at": {"type": "string", "format": "date-time"},
            "dwell_ms": {"type": ["integer", "null"], "minimum": 0},
            "session_id": {"type": "string"},
            "recommendation_context": {"type": "string", "enum": ["swipe", "chat"]},
            "rank_position": {"type": ["integer", "null"], "minimum": 0},
            "recommendation_id": {"type": ["string", "null"]},
            "producer": {
                "type": "object",
                "required": ["surface"],
                "properties": {
                    "surface": {"type": "string", "enum": ["swipe", "chat"]},
                    "client_version": {"type": ["string", "null"]},
                },
            },
            "event_snapshot": {
                "type": "object",
                "required": ["event_id"],
                "properties": {
                    "event_id": {"type": "string"},
                    "segmento": {"type": ["string", "null"]},
                    "genero": {"type": ["string", "null"]},
                    "subgenero": {"type": ["string", "null"]},
                    "ciudad": {"type": ["string", "null"]},
                    "recinto_id": {"type": ["string", "null"]},
                    "fecha_evento": {"type": ["string", "null"], "format": "date"},
                    "precio_min": {"type": ["number", "null"]},
                    "precio_max": {"type": ["number", "null"]},
                    "banda_precio": {"type": ["string", "null"]},
                },
            },
        },
    }


def contract_markdown() -> str:
    return """# Contrato enriquecido del swipe (`v2`)

## Objetivo

Evitar que el clustering dependa exclusivamente de joins posteriores y guardar el contexto del evento en el momento exacto de la interaccion.

## Cambios principales frente al payload actual

- se anade `schema_version`;
- se mantiene el payload base actual (`event_id`, `direction`, `swiped_at`, `dwell_ms`, `session_id`, `recommendation_context`);
- se anade `rank_position` para capturar contexto de ranking;
- se anade `recommendation_id` para trazabilidad de la recomendacion;
- se anade `producer` para identificar superficie y version del cliente;
- se anade `event_snapshot` con metadatos del evento.

## Campos recomendados del snapshot

- `segmento`
- `genero`
- `subgenero`
- `ciudad`
- `recinto_id`
- `fecha_evento`
- `precio_min`
- `precio_max`
- `banda_precio`

## Racional analitico

- `dwell_ms`: engagement real del usuario.
- `rank_position`: sesgo por posicion en el deck.
- `event_snapshot`: protege de cambios posteriores en el catalogo.
- `banda_precio`: alternativa temporal mientras no haya precio numerico estable.

## Implementacion recomendada

1. Frontend:
   ampliar `SwipeEventCreate` en `frontend/portal/src/api.ts`.
2. Frontend:
   enviar `event_snapshot` desde `frontend/portal/src/components/QuickMatch.tsx`.
3. Backend:
   ampliar `SwipeEventCreate` en `backend/portal-api/app/schemas/saved_event.py`.
4. Staging dbt:
   parsear `event_snapshot.*` en `transformations/models/staging/stg_swipes.sql`.
5. Mart dbt:
   hacer que `fct_swipes` prefiera el snapshot del payload cuando exista, y use join al catalogo como fallback.
"""


def implementation_checklist() -> str:
    return """# Checklist de implementación del contrato de swipe v2

## Frontend

- actualizar el tipo `SwipeEventCreate` en `frontend/portal/src/api.ts`;
- enviar `schema_version`, `rank_position`, `producer` y `event_snapshot`;
- asegurar que `QuickMatch` tenga acceso al evento visible completo al publicar el swipe.

## Backend

- ampliar el schema Pydantic de `SwipeEventCreate`;
- validar tipos y opcionales;
- mantener compatibilidad hacia atras con `v1` durante la transición si hace falta.

## dbt / BigQuery

- parsear en `stg_swipes`:
  - `event_snapshot.segmento`
  - `event_snapshot.genero`
  - `event_snapshot.subgenero`
  - `event_snapshot.ciudad`
  - `event_snapshot.recinto_id`
  - `event_snapshot.fecha_evento`
  - `event_snapshot.precio_min`
  - `event_snapshot.precio_max`
  - `event_snapshot.banda_precio`
- incluir `dwell_ms` en `stg_swipes` y `fct_swipes`.
- actualizar tests y descripciones de schema.
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    schema_path = SPECS_DIR / "swipe_event_contract_v2.json"
    schema_path.write_text(json.dumps(contract_schema(), indent=2, sort_keys=True), encoding="utf-8")
    write_file(SPECS_DIR / "swipe_event_contract_v2.md", contract_markdown())
    write_file(SPECS_DIR / "implementation_checklist.md", implementation_checklist())
    print("Step 3 completed: enriched swipe contract defined.")
    print(f"Schema path: {schema_path}")
    print(f"Markdown spec: {SPECS_DIR / 'swipe_event_contract_v2.md'}")


if __name__ == "__main__":
    main()
