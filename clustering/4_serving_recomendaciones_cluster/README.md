# Serving de recomendaciones por cluster

Esta carpeta materializa las salidas del clustering en BigQuery y genera una primera tabla de candidatos recomendados por usuario.

El objetivo es separar claramente:

- entrenamiento del modelo;
- salidas interpretables del clustering;
- generacion batch de candidatos para consumo de producto.

## Tablas creadas

Todas las tablas se escriben por defecto en `project3grupo3.recomendacion_planes_marts`.

- `user_cluster_assignments`: asignacion usuario -> cluster.
- `cluster_profiles`: perfil interpretable por cluster.
- `cluster_neighbors`: clusters cercanos para discovery.
- `cluster_event_affinity`: afinidad historica cluster -> tipo de evento.
- `user_recommendation_candidates`: candidatos recomendados por usuario.

## Scripts

- `step_1_load_cluster_outputs.py`: carga CSVs del entrenamiento en BigQuery.
- `step_2_build_cluster_event_affinity.py`: calcula afinidad por segmento, genero y banda de precio usando `fct_swipes`.
- `step_3_generate_user_recommendation_candidates.py`: genera ranking top-N por usuario.
- `step_4_validate_serving_outputs.py`: valida conteos y guarda una muestra.
- `run_serving_pipeline.py`: orquestador local.

## Ejecucion

```bash
python3 clustering/4_serving_recomendaciones_cluster/run_serving_pipeline.py
```

Por defecto usa:

```text
clustering/2_integracion_datos_gcp/training_outputs/smoke_synthetic_demo_improved_20260502_all_users
```

Puedes cambiar el directorio de outputs:

```bash
python3 clustering/4_serving_recomendaciones_cluster/run_serving_pipeline.py \
  --training-output-dir clustering/2_integracion_datos_gcp/training_outputs/smoke_synthetic_demo_improved_20260502_synthetic_only \
  --model-run-id smoke_synthetic_demo_improved_20260502_synthetic_only
```

## Logica de scoring

Cada usuario recibe candidatos desde:

- su cluster propio con peso `1.0`;
- clusters vecinos con pesos decrecientes;
- eventos futuros reales del catalogo;
- afinidad historica cluster -> segmento/genero/banda de precio;
- pequeno boost por ciudad del usuario si esta disponible;
- pequeno boost por urgencia temporal.

Tambien se excluyen eventos que el usuario ya ha visto en `fct_swipes`.

## Notas GCP

- Las tablas finales se crean con `create or replace table` para que el batch sea idempotente.
- Las tablas se clusterizan por claves de acceso frecuentes (`user_id`, `cluster_id`, `recommendation_rank`).
- `user_recommendation_candidates` queda particionada por `computed_at`.
- Cada tabla incluye `model_run_id` y timestamp de ejecucion para trazabilidad.

## Siguiente paso

Conectar el backend a `user_recommendation_candidates`, por ejemplo con un endpoint:

```text
GET /users/me/recommendations
```

Ese endpoint deberia leer los candidatos del usuario actual, ordenar por `recommendation_rank` y devolver los metadatos del evento.
