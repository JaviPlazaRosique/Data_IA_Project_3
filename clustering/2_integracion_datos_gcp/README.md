# Integracion Del Clustering Con Datos Reales Y GCP

Este directorio contiene la siguiente fase del trabajo de clustering: el puente entre el prototipo local y una implementacion real basada en `fct_swipes`, dbt y ejecucion batch en Google Cloud.

La idea es no tocar todavia el flujo productivo existente, sino preparar entregables pequenos, claros y reutilizables para avanzar con seguridad.

## Objetivos de esta carpeta

- mapear que features del prototipo ya pueden construirse sobre datos reales;
- generar borradores de modelos dbt para 30 y 90 dias;
- definir un contrato enriquecido del swipe para mejorar la calidad del dato;
- adaptar el entrenamiento para leer exports reales de features;
- preparar los assets base del batch en GCP con buenas practicas.

## Scripts disponibles

### 1. `step_1_mapear_features_reales.py`

Analiza la salida del prototipo local y genera:

- `outputs/feature_mapping.csv`
- `outputs/feature_gap_report.md`

Sirve para ver que parte del prototipo ya es implementable con `fct_swipes` y que parte sigue bloqueada por `dwell_ms`, precio o perfil de usuario.

### 2. `step_2_generar_borradores_dbt.py`

Genera en `dbt_drafts/`:

- `int_user_swipe_features_30d.sql`
- `int_user_swipe_features_90d.sql`
- `dim_user_cluster_features_current.sql`
- `schema.yml`

Son borradores listos para revisar y mover mas tarde a `transformations/models/`.

### 3. `step_3_definir_contrato_swipe_v2.py`

Genera en `specs/`:

- `swipe_event_contract_v2.json`
- `swipe_event_contract_v2.md`
- `implementation_checklist.md`

Documenta el payload enriquecido recomendado para que clustering no dependa solo de joins posteriores.

### 4. `step_4_entrenar_desde_feature_export.py`

Entrena clustering a partir de un CSV exportado desde dbt/BigQuery con features ya agregadas por usuario.

Ejemplo con el prototipo actual:

```bash
python3 clustering/integracion_datos_reales_gcp/step_4_entrenar_desde_feature_export.py \
  --input-csv clustering/prototipo_local/output/user_features.csv
```

Genera en `training_outputs/real_feature_clustering/`:

- `user_cluster_assignments.csv`
- `cluster_profiles.csv`
- `cluster_neighbors.csv`
- `model_selection_metrics.csv`
- `training_run_summary.json`

Cuando exista el modelo real `dim_user_cluster_features_current`, este mismo script puede ejecutarse contra un export real de BigQuery.

### 5. `step_5_preparar_batch_gcp.py`

Genera en `gcp_batch/`:

- `Dockerfile`
- `requirements.txt`
- `job_main.py`
- `cloud_run_job.env.example`
- `terraform_clustering_job_snippet.tf`
- `runbook.md`

Prepara el scaffold del `Cloud Run Job` y del `Scheduler` siguiendo el estilo del repositorio actual.

## Orden recomendado de ejecucion

```bash
python3 clustering/integracion_datos_reales_gcp/step_1_mapear_features_reales.py
python3 clustering/integracion_datos_reales_gcp/step_2_generar_borradores_dbt.py
python3 clustering/integracion_datos_reales_gcp/step_3_definir_contrato_swipe_v2.py
python3 clustering/integracion_datos_reales_gcp/step_4_entrenar_desde_feature_export.py \
  --input-csv clustering/prototipo_local/output/user_features.csv
python3 clustering/integracion_datos_reales_gcp/step_5_preparar_batch_gcp.py
```

## Como usar esto para avanzar en el proyecto

1. Revisar `outputs/feature_gap_report.md` y decidir que bloqueos se corrigen primero.
2. Revisar `dbt_drafts/` y mover los modelos a `transformations/models/` cuando se validen.
3. Acordar el contrato `v2` del swipe entre frontend, backend y analitica.
4. Exportar el modelo real de features desde BigQuery y probar el entrenamiento con `step_4`.
5. Promover `gcp_batch/` a una imagen de `Cloud Run Job` cuando el flujo con datos reales ya sea estable.

## Notas de diseno

- Todos los scripts son pequenos y de responsabilidad unica.
- Los artefactos generados quedan dentro de esta misma carpeta.
- Se prioriza Python estandar siempre que es posible.
- El scaffold GCP favorece `Cloud Run Job` + `Cloud Scheduler`, service account dedicada y logs estructurados.
