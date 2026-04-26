# transformations

dbt project. Lee `raw.swipes_raw` (cargado por suscripción BigQuery de Pub/Sub) y construye `recomendacion_planes_marts.fct_swipes` enriquecido con `recomendacion_planes.eventos`. Staging vive en `recomendacion_planes_staging`.

## Layout
- `models/staging/stg_swipes.sql` — parsea JSON del envelope.
- `models/marts/fct_swipes.sql` — incremental, dedupe por `message_id`, join con catálogo `eventos`.

## Local
```
pip install -r requirements.txt
export GCP_PROJECT=project3grupo3
gcloud auth application-default login
dbt build --project-dir . --profiles-dir . --target dev
```

## Prod
Despliegue (Cloud Run Job + Scheduler) pendiente de wiring en terraform.
