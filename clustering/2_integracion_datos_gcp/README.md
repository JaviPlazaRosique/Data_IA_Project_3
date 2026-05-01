# Integracion Del Clustering Con Datos Reales Y GCP

Este directorio contiene la siguiente fase del trabajo de clustering: el puente entre el prototipo local y una implementacion real basada en `fct_swipes`, dbt y ejecucion batch en Google Cloud.

La carpeta nacio para preparar entregables pequeños, claros y reutilizables antes de tocar el flujo productivo. Los modelos dbt y el contrato v2 ya han empezado a promoverse al codigo principal del proyecto.

## Objetivos de esta carpeta

- mapear que features del prototipo ya pueden construirse sobre datos reales;
- dejar promovidos los modelos dbt de features a 30 y 90 dias;
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

Genera borradores historicos en `dbt_drafts/` si se necesita regenerar la propuesta original:

- `int_user_swipe_features_30d.sql`
- `int_user_swipe_features_90d.sql`
- `dim_user_cluster_features_current.sql`
- `schema.yml`

Estado actual: los modelos ya estan promovidos a `transformations/models/`:

- `transformations/models/intermediate/int_user_swipe_features_30d.sql`
- `transformations/models/intermediate/int_user_swipe_features_90d.sql`
- `transformations/models/marts/dim_user_cluster_features_current.sql`

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
python3 clustering/2_integracion_datos_gcp/step_4_entrenar_desde_feature_export.py \
  --input-csv clustering/1_prototipo_local/output/user_features.csv
```

Genera en `training_outputs/real_feature_clustering/`:

- `user_cluster_assignments.csv`
- `cluster_profiles.csv`
- `cluster_neighbors.csv`
- `model_selection_metrics.csv`
- `training_run_summary.json`

Cuando `dim_user_cluster_features_current` este materializado en BigQuery, este mismo script puede ejecutarse contra un export real.

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
python3 clustering/2_integracion_datos_gcp/step_1_mapear_features_reales.py
python3 clustering/2_integracion_datos_gcp/step_3_definir_contrato_swipe_v2.py
python3 clustering/2_integracion_datos_gcp/step_4_entrenar_desde_feature_export.py \
  --input-csv clustering/1_prototipo_local/output/user_features.csv
python3 clustering/2_integracion_datos_gcp/step_5_preparar_batch_gcp.py
```

## Como usar esto para avanzar en el proyecto

1. Revisar `outputs/feature_gap_report.md` y decidir que bloqueos se corrigen primero.
2. Ejecutar y validar los modelos dbt promovidos en `transformations/models/`.
3. Validar en datos reales que el contrato `v2` del swipe llega completo a BigQuery.
4. Exportar el modelo real de features desde BigQuery y probar el entrenamiento con `step_4`.
5. Promover `gcp_batch/` a una imagen de `Cloud Run Job` cuando el flujo con datos reales ya sea estable.

## Notas de diseno

- Todos los scripts son pequenos y de responsabilidad unica.
- Los artefactos generados quedan dentro de esta misma carpeta.
- Se prioriza Python estandar siempre que es posible.
- El scaffold GCP favorece `Cloud Run Job` + `Cloud Scheduler`, service account dedicada y logs estructurados.
