# Generacion de interacciones sinteticas de demo

Esta carpeta genera swipes sinteticos sobre eventos reales de BigQuery para probar el clustering con mas volumen y perfiles de usuario reconocibles.

La idea es mantener el catalogo real en `recomendacion_planes.eventos` y anadir solo interacciones sinteticas en `recomendacion_planes.swipes_raw`, usando el contrato `swipe_event_contract_v2`.

## Que genera

- usuarios demo deterministas con `user_id` tipo UUID;
- personas sinteticas con gustos diferentes;
- swipes `right` y `left` en los ultimos 90 dias;
- `dwell_ms`, `rank_position`, `recommendation_context`, `producer` y `event_snapshot`;
- filas JSONL compatibles con la tabla raw `swipes_raw`;
- validacion de la carga en BigQuery por `synthetic_run_id`.

Cada payload incluye:

- `data_origin = synthetic_demo`;
- `synthetic_run_id`;
- `synthetic_persona`;
- `schema_version = 2.0`.

Esto permite identificar facilmente los datos de demo sin mezclarlos conceptualmente con swipes reales.

## Taxonomia analitica

El catalogo real trae valores como `Arts & Theatre`, `Miscellaneous/Family`, `World` o `Undefined`.

Las features actuales de clustering esperan valores mas analiticos como:

- segmentos: `Music`, `Sports`, `Arts_Theatre`, `Family`;
- generos: `Rock`, `Pop`, `Basketball`, `Comedy`, `Musical`, `Theatre`, `Kids`, `Circus`, `Exhibition`.

Por eso el generador normaliza el `event_snapshot` a la taxonomia usada por las features, manteniendo siempre el `event_id` real del catalogo.

## Scripts

- `step_1_export_real_events.py`: exporta eventos reales desde BigQuery a `outputs/real_events.csv`.
- `step_2_generate_demo_users.py`: genera usuarios demo en `outputs/demo_users.csv`.
- `step_3_generate_synthetic_swipes.py`: genera swipes v2 en CSV de revision y JSONL de carga.
- `step_4_load_swipes_to_bigquery.py`: inserta el JSONL en `recomendacion_planes.swipes_raw`.
- `step_5_validate_loaded_swipes.py`: valida en BigQuery filas cargadas, usuarios, contrato v2 y ratio de likes.
- `step_6_refresh_analytics_with_bq.py`: refresca `stg_swipes`, `fct_swipes` y las features usando `bq` como fallback local si dbt no tiene ADC.
- `step_7_enrich_feature_export_with_demo_metadata.py`: anade persona y ciudad al export local de features para interpretar el smoke test.
- `run_generation_pipeline.py`: orquestador opcional.

## Uso recomendado

Generar archivos locales sin cargar nada:

```bash
python3 clustering/3_generacion_interacciones_demo/run_generation_pipeline.py
```

Generar y cargar en BigQuery:

```bash
python3 clustering/3_generacion_interacciones_demo/run_generation_pipeline.py --load-to-bigquery
```

Usar un identificador de ejecucion propio:

```bash
python3 clustering/3_generacion_interacciones_demo/run_generation_pipeline.py \
  --run-id synthetic_demo_20260502_v2 \
  --load-to-bigquery
```

Si ya existe ese `run_id`, el paso de carga se bloquea para evitar duplicados accidentales. Solo usa `--force-load` si quieres appendear de nuevo al raw.

## Despues de cargar

Refresca la capa analitica en este orden con dbt:

```bash
dbt build --select stg_swipes fct_swipes int_user_swipe_features_30d int_user_swipe_features_90d dim_user_cluster_features_current
```

Si dbt no tiene Application Default Credentials pero `bq` funciona, usa el fallback local:

```bash
python3 clustering/3_generacion_interacciones_demo/step_6_refresh_analytics_with_bq.py
```

Despues exporta `dim_user_cluster_features_current` y reentrena con:

```bash
python3 clustering/2_integracion_datos_gcp/step_4_entrenar_desde_feature_export.py \
  --input-csv clustering/2_integracion_datos_gcp/real_exports/dim_user_cluster_features_current_YYYYMMDD.csv \
  --output-dir clustering/2_integracion_datos_gcp/training_outputs/smoke_real_YYYYMMDD
```

Para interpretar mejor una demo sintetica, puedes enriquecer el export local con `synthetic_persona` y entrenar solo con usuarios demo:

```bash
python3 clustering/3_generacion_interacciones_demo/step_7_enrich_feature_export_with_demo_metadata.py --synthetic-only
```

## Criterio de exito

- BigQuery contiene filas con `schema_version = 2.0`;
- todas las filas sinteticas tienen `event_snapshot` y `dwell_ms`;
- hay suficiente volumen por usuario para clustering;
- la tabla `dim_user_cluster_features_current` contiene muchos mas usuarios que antes;
- los clusters dejan de estar dominados por usuarios aislados.
