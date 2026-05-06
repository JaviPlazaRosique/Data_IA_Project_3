# Plan de Accion para Clustering de Gustos y Recomendacion por Afinidad

## Objetivo

Construir una capacidad de clustering que agrupe usuarios segun sus gustos observados en la app, usando sobre todo el historial de swipes, para poder:

- recomendar planes populares dentro de su cluster;
- recomendar planes de clusters cercanos cuando queramos ampliar discovery sin perder afinidad;
- recalcular segmentos de forma periodica y automatizable;
- llevar el prototipo local a Google Cloud sin rehacer arquitectura.

## Estado actual

Actualmente ya existen dos bloques de trabajo principales dentro de `clustering`:

- `clustering/1_prototipo_local`: prototipo local funcional que cubre la fase 1 del plan.
- `clustering/2_integracion_datos_gcp`: fase preparatoria para llevar el clustering a datos reales, dbt y GCP.
- `clustering/3_generacion_interacciones_demo`: generacion de swipes sinteticos sobre eventos reales para demo y pruebas de clustering.
- `clustering/4_serving_recomendaciones_cluster`: materializacion de outputs del clustering y generacion de candidatos recomendados.

Lo que ya esta implementado:

- generacion de usuarios, eventos e interacciones sinteticas inspiradas en `fct_swipes`;
- construccion de features por usuario en ventanas de 30 y 90 dias;
- entrenamiento de un baseline con estandarizacion y `KMeans`;
- seleccion de `k` mediante metricas offline;
- generacion de clusters cercanos;
- produccion de artefactos y tablas de salida del prototipo;
- informe final del experimento local.
- mapeo de features del prototipo contra `fct_swipes`;
- analisis de gaps de datos reales;
- modelos dbt reales para features a 30 y 90 dias;
- definicion e implementacion del contrato enriquecido `swipe_event_contract_v2`;
- adaptacion de `stg_swipes` y `fct_swipes` para `dwell_ms` y `event_snapshot`;
- adaptacion del entrenamiento para leer exports reales de features;
- batch semanal de clustering en GCP declarado con `Cloud Run Job` y `Cloud Scheduler`.
- generacion y carga en BigQuery de interacciones sinteticas de demo con contrato `v2`.
- materializacion de tablas de serving para clustering y primera tabla de candidatos recomendados por usuario.

Estructura actual de `1_prototipo_local`:

- `step_1_generate_synthetic_data.py`
- `step_2_build_user_features.py`
- `step_3_train_baseline_model.py`
- `step_4_build_cluster_outputs.py`
- `step_5_write_report.py`
- `run_prototype.py`

Artefactos ya disponibles en `1_prototipo_local`:

- `data/synthetic_users.csv`
- `data/synthetic_events_catalog.csv`
- `data/synthetic_fct_swipes.csv`
- `output/user_features.csv`
- `output/user_cluster_assignments.csv`
- `output/cluster_profiles.csv`
- `output/cluster_neighbors.csv`
- `output/cluster_event_affinity.csv`
- `output/model_selection_metrics.csv`
- `output/prototype_report.md`
- `artifacts/user_features_metadata.json`
- `artifacts/model_artifacts.json`

Estructura actual de `2_integracion_datos_gcp`:

- `step_1_mapear_features_reales.py`
- `step_2_generar_borradores_dbt.py`
- `step_3_definir_contrato_swipe_v2.py`
- `step_4_entrenar_desde_feature_export.py`
- `step_5_preparar_batch_gcp.py`
- `README.md`

Estructura actual de `3_generacion_interacciones_demo`:

- `step_1_export_real_events.py`
- `step_2_generate_demo_users.py`
- `step_3_generate_synthetic_swipes.py`
- `step_4_load_swipes_to_bigquery.py`
- `step_5_validate_loaded_swipes.py`
- `step_6_refresh_analytics_with_bq.py`
- `step_7_enrich_feature_export_with_demo_metadata.py`
- `run_generation_pipeline.py`
- `README.md`

Estructura actual de `4_serving_recomendaciones_cluster`:

- `step_1_load_cluster_outputs.py`
- `step_2_build_cluster_event_affinity.py`
- `step_3_generate_user_recommendation_candidates.py`
- `step_4_validate_serving_outputs.py`
- `run_serving_pipeline.py`
- `serving_config.py`
- `README.md`

Artefactos ya disponibles en `2_integracion_datos_gcp`:

- `outputs/feature_mapping.csv`
- `outputs/feature_gap_report.md`
- `specs/swipe_event_contract_v2.json`
- `specs/swipe_event_contract_v2.md`
- `specs/implementation_checklist.md`
- `training_outputs/real_feature_clustering/*`
- `gcp_batch/Dockerfile`
- `gcp_batch/job_main.py`
- `gcp_batch/terraform_clustering_job_snippet.tf`
- `gcp_batch/runbook.md`

Artefactos ya disponibles en `3_generacion_interacciones_demo`:

- `outputs/real_events.csv`
- `outputs/demo_users.csv`
- `outputs/synthetic_swipes_preview.csv`
- `outputs/synthetic_swipes_raw_rows.jsonl`
- `outputs/generation_summary.json`
- `outputs/validation_summary.json`

Artefactos ya disponibles en `4_serving_recomendaciones_cluster`:

- `outputs/serving_validation_summary.json`

## Punto de partida actual del proyecto

El repositorio ya tiene gran parte del flujo base necesario:

- el frontend ya dispone de una experiencia de swipes en `frontend/portal/src/pages/SwipePage.tsx`;
- el backend ya expone el endpoint `POST /users/me/swipe-events` en `backend/portal-api/app/api/v1/endpoints/swipe_events.py`;
- los swipes ya se publican en Pub/Sub desde `backend/portal-api/app/services/pubsub.py`;
- Terraform ya crea el topic `swipe-events` y la tabla raw `swipes_raw` en BigQuery;
- dbt ya transforma esos eventos en `stg_swipes` y en el mart `fct_swipes`;
- el proyecto ya usa Cloud Run Jobs y Cloud Scheduler para ejecutar procesos batch.

Esto permite plantear una solucion incremental: primero prototipo local con datos sinteticos y despues industrializacion en GCP con muy pocos cambios estructurales.

## Gaps a cubrir antes de entrenar un clustering util

Aunque la base es buena, todavia hay huecos que conviene cerrar para que el clustering sea realmente accionable:

1. El payload actual del swipe es pequeno: incluye `event_id`, `direction`, `swiped_at`, `dwell_ms`, `session_id` y `recommendation_context`, pero no guarda un snapshot rico del evento en el momento de la interaccion.
2. `fct_swipes` ya enriquece con `segmento`, `genero`, `subgenero`, `ciudad` y `recinto_id`, pero `precio_min` y `precio_max` aparecen aun como `null`.
3. Falta una capa dedicada de features por usuario para clustering.
4. Falta una capa de salida con asignaciones de cluster, clusters cercanos y reglas de recomendacion.
5. Falta definir el mecanismo de serving: como usara la app el cluster del usuario para priorizar eventos.

## Principios de diseno

- Empezar simple: baseline con `KMeans` y features interpretable.
- Separar entrenamiento, asignacion y recomendacion.
- Usar ventanas temporales moviles, no historico infinito.
- Mantener una trazabilidad clara entre swipe bruto, feature agregada, cluster asignado y recomendacion servida.
- Preparar el disenio para cold start y para usuarios con muy poca actividad.

## Fase 1. Prototipo local con datos de prueba

Estado: completada en version inicial.

Resultado: existe ya un pipeline local por pasos, reproducible y sin dependencias externas, preparado para validar el enfoque antes de conectarlo a datos reales. Su implementacion vive en `clustering/1_prototipo_local`.

### 1.1. Dataset local de trabajo

Usar como base la estructura analitica ya preparada para swipes y generar un dataset sintetico con suficiente variabilidad de usuarios.

Estado actual:

- crear una muestra local con usuarios y eventos sinteticos inspirados en la forma de `fct_swipes`;
- asegurar que haya diversidad realista en `segmento`, `genero`, `subgenero`, `ciudad`, precio, antelacion al evento y frecuencia de swipe;
- introducir perfiles sinteticos reconocibles para validar que el clustering los recupera;
- definir un minimo de interacciones por usuario para poder entrar en clustering.

### 1.2. Feature engineering local

Construir una tabla de features a nivel usuario, idealmente sobre ventanas de 30 y 90 dias.

Estado actual:

- volumen: `total_swipes`, `total_right_swipes`, `right_swipe_rate`;
- afinidad por contenido: tasas de like por `segmento`, `genero` y `subgenero`;
- dispersion: numero de segmentos/generos distintos aceptados;
- geografia: afinidad por `ciudad`, ratio de eventos en ciudad propia frente a otras;
- timing: antelacion media de los eventos que acepta;
- precio: precio medio y mediano de eventos aceptados y rechazados;
- engagement: `dwell_ms` medio, recencia del ultimo like, sesiones activas;
- contexto: comportamiento distinto en `recommendation_context` si luego anadimos mas fuentes.

### 1.3. Entrenamiento del baseline

Entrenar primero un baseline con `StandardScaler + KMeans`.

Estado actual:

- probar varios valores de `k`;
- comparar `silhouette`, `davies_bouldin`, tamano de clusters y estabilidad entre semillas;
- revisar manualmente perfiles medios por cluster;
- descartar clusters que sean puro ruido o que solo separen por actividad extrema.

### 1.4. Definicion de clusters cercanos

Para poder recomendar planes de clusters vecinos, calcular cercania entre centroides.

Estado actual:

- distancia coseno o euclidea entre centroides escalados;
- guardar para cada cluster sus `top_n` clusters mas cercanos;
- usar esa cercania como expansion controlada del universo de recomendacion.

### 1.5. Salidas esperadas del prototipo

El prototipo local debe producir como minimo:

- tabla de features por usuario;
- tabla de asignacion usuario -> cluster;
- tabla de perfil por cluster;
- tabla de cluster -> clusters cercanos;
- tabla de afinidad cluster -> tipos de evento;
- informe corto con conclusion de si el clustering es interpretable y util.

Estado de outputs:

- completado: `user_features.csv`
- completado: `user_cluster_assignments.csv`
- completado: `cluster_profiles.csv`
- completado: `cluster_neighbors.csv`
- completado: `cluster_event_affinity.csv`
- completado: `prototype_report.md`

### 1.6. Cierre de fase 1

La fase 1 queda suficientemente cubierta para pasar al siguiente bloque de trabajo porque ya tenemos:

- un flujo ejecutable de punta a punta;
- un baseline interpretable;
- salidas comparables con las tablas objetivo de produccion;
- separacion clara entre generacion, features, entrenamiento, outputs e informe.

Lo que no resuelve aun la fase 1:

- no trabaja todavia con datos reales del proyecto;
- no publica resultados en BigQuery;
- no se integra aun con dbt ni con el backend;
- no sirve recomendaciones reales a usuarios.

## Fase 1.5. Preparacion para datos reales y GCP

Estado: completada en version preparatoria.

Resultado: existe ya una segunda carpeta de trabajo en `clustering/2_integracion_datos_gcp` que aterriza los siguientes pasos tecnicos, y parte de esos entregables ya se ha promovido al flujo principal.

### 1.5.1. Mapeo de features reales

Estado: completado.

Entregables:

- `outputs/feature_mapping.csv`
- `outputs/feature_gap_report.md`

Lectura principal:

- la mayoria de las features del prototipo ya pueden construirse sobre `fct_swipes`;
- los bloqueos mas importantes estan en `dwell_ms`, precio del evento y contexto geografico del usuario.

### 1.5.2. Modelos dbt de features

Estado: promovido a modelos reales del proyecto.

Entregables:

- `transformations/models/intermediate/int_user_swipe_features_30d.sql`
- `transformations/models/intermediate/int_user_swipe_features_90d.sql`
- `transformations/models/intermediate/schema.yml`
- `transformations/models/marts/dim_user_cluster_features_current.sql`

Objetivo:

- materializar una tabla de features por usuario lista para exportar y entrenar clustering.

### 1.5.3. Contrato enriquecido del swipe

Estado: especificado e implementado en frontend, backend y dbt staging/mart.

Entregables:

- `specs/swipe_event_contract_v2.json`
- `specs/swipe_event_contract_v2.md`
- `specs/implementation_checklist.md`
- `frontend/portal/src/api.ts`
- `frontend/portal/src/components/QuickMatch.tsx`
- `backend/portal-api/app/schemas/saved_event.py`
- `transformations/models/staging/stg_swipes.sql`
- `transformations/models/marts/fct_swipes.sql`

Objetivo:

- guardar un snapshot analitico del evento en el momento del swipe para reducir dependencia de joins posteriores.

### 1.5.4. Entrenamiento desde exports reales

Estado: completado en version adaptable.

Entregables:

- `step_4_entrenar_desde_feature_export.py`
- `training_outputs/real_feature_clustering/*`

Objetivo:

- reutilizar el entrenamiento del clustering cuando las features reales ya esten materializadas y exportadas desde dbt o BigQuery.

### 1.5.5. Scaffold batch GCP

Estado: completado en version scaffold.

Entregables:

- `gcp_batch/Dockerfile`
- `gcp_batch/requirements.txt`
- `gcp_batch/job_main.py`
- `gcp_batch/cloud_run_job.env.example`
- `gcp_batch/terraform_clustering_job_snippet.tf`
- `gcp_batch/runbook.md`

Objetivo:

- preparar el despliegue batch siguiendo el stack actual del repositorio: BigQuery, Cloud Run Job, Scheduler y Terraform.

## Fase 1.6. Interacciones sinteticas sobre eventos reales

Estado: completada para demo inicial.

Resultado: se ha creado `clustering/3_generacion_interacciones_demo` para poblar la tabla de interacciones con usuarios y swipes sinteticos, manteniendo el catalogo de eventos real como fuente.

### 1.6.1. Generacion de datos

Estado: completado.

Entregables:

- export local de 694 eventos reales desde `recomendacion_planes.eventos`;
- 184 usuarios demo deterministas;
- 13.069 swipes sinteticos en formato compatible con `swipes_raw`;
- payloads marcados con `data_origin = synthetic_demo`;
- identificador de ejecucion `synthetic_run_id = synthetic_demo_20260502`.

### 1.6.2. Contrato y trazabilidad

Estado: validado en BigQuery.

Resultado de validacion:

- filas cargadas: 13.069;
- usuarios sinteticos: 184;
- eventos reales cubiertos: 694;
- filas con `schema_version = 2.0`: 13.069;
- filas con `event_snapshot`: 13.069;
- filas con `dwell_ms`: 13.069;
- `right_swipe_rate` global: 0,481.

### 1.6.3. Decisiones tomadas

- no se modifica la tabla de eventos;
- no se escriben directamente tablas derivadas como `fct_swipes` o features;
- las interacciones se insertan en `swipes_raw`, igual que si vinieran de Pub/Sub;
- el `event_snapshot` normaliza la taxonomia a los valores usados por las features de clustering;
- los datos sinteticos quedan identificados por `synthetic_run_id` y `data_origin`.

### 1.6.4. Siguiente paso tras la carga

Estado: completado mediante fallback local con `bq`, porque `dbt build` requiere Application Default Credentials en este entorno.

La capa analitica ya se refresco para que los swipes nuevos entren en:

- `stg_swipes`;
- `fct_swipes`;
- `int_user_swipe_features_30d`;
- `int_user_swipe_features_90d`;
- `dim_user_cluster_features_current`.

Resultado tras refrescar:

- `fct_swipes`: 17.412 filas;
- swipes `v2` en `fct_swipes`: 13.069;
- usuarios en features: 196;
- swipes medios a 90 dias por usuario: 88,84.

Tambien se ejecuto un smoke test de entrenamiento con el export actualizado:

- input: `clustering/2_integracion_datos_gcp/real_exports/dim_user_cluster_features_current_synthetic_demo_20260502_enriched.csv`;
- output: `clustering/2_integracion_datos_gcp/training_outputs/smoke_synthetic_demo_20260502_enriched`;
- filas entrenadas: 196;
- `k` seleccionado: 4;
- `silhouette`: 0,156;
- lectura: el pipeline tecnico ya esta cerrado, pero los clusters aun mezclan varias personas sinteticas y conviene mejorar features/segmentacion antes de usarlo como ranking principal.

### 1.6.5. Mejora de features y reentrenamiento

Estado: completado en smoke test.

Cambios aplicados:

- se anadieron `liked_share_*` para representar la distribucion de gustos aceptados por segmento, genero y banda de precio;
- se anadieron `swipe_share_*` para representar exposicion por segmento, genero y banda de precio;
- se anadieron `preference_lift_*` para medir afinidad relativa frente al ratio medio de like del usuario;
- el entrenamiento descarta features constantes;
- el entrenamiento pondera menos volumen puro y pondera mas afinidad/preferencia.

Entregables:

- `transformations/models/intermediate/int_user_swipe_features_30d.sql`;
- `transformations/models/intermediate/int_user_swipe_features_90d.sql`;
- `transformations/models/marts/dim_user_cluster_features_current.sql`;
- `clustering/2_integracion_datos_gcp/real_exports/dim_user_cluster_features_current_synthetic_demo_improved_20260502.csv`;
- `clustering/2_integracion_datos_gcp/real_exports/dim_user_cluster_features_current_synthetic_demo_improved_20260502_enriched.csv`;
- `clustering/2_integracion_datos_gcp/real_exports/dim_user_cluster_features_current_synthetic_demo_improved_20260502_synthetic_only.csv`;
- `clustering/2_integracion_datos_gcp/training_outputs/smoke_synthetic_demo_improved_20260502_all_users`;
- `clustering/2_integracion_datos_gcp/training_outputs/smoke_synthetic_demo_improved_20260502_synthetic_only`.

Resultado con todos los usuarios:

- filas entrenadas: 196;
- features numericas usadas: 164;
- features constantes descartadas: 40;
- `k` seleccionado: 4;
- `silhouette`: 0,243;
- `davies_bouldin`: 1,486;
- clusters balanceados: tamanos 37, 54, 67 y 38.

Resultado con usuarios demo:

- filas entrenadas: 184;
- features numericas usadas: 164;
- features constantes descartadas: 40;
- `k` seleccionado: 4;
- `silhouette`: 0,259;
- `davies_bouldin`: 1,448;
- clusters principales: familia/exposiciones, cultura/teatro, musica pop-rock/flamenco y discovery/deportes.

Lectura:

- la mejora es clara frente al smoke anterior, donde habia clusters muy pequenos y menos interpretables;
- las personas `family_weekend_exhibition` y `culture_theatre_explorer` se recuperan con alta pureza;
- musica local y flamenco quedan agrupados, algo razonable por la taxonomia actual;
- deporte se mezcla con discovery porque hay poco catalogo deportivo real disponible.

## Fase 2. Diseno de recomendacion apoyada en clusters

El clustering no debe recomendar eventos por si solo; debe actuar como senal de priorizacion.

Estado: pendiente. Ya esta definido a nivel conceptual, pero todavia no esta implementado sobre datos reales ni conectado a la app.

### 2.1. Estrategia de recomendacion

Propuesta de ranking:

1. generar candidatos desde el catalogo de eventos futuros;
2. calcular afinidad del evento con el cluster del usuario;
3. anadir afinidad con clusters cercanos con menor peso;
4. mezclar con senales individuales del usuario si existen;
5. aplicar reglas de negocio: ciudad, fechas proximas, disponibilidad, repeticion, diversidad.

### 2.2. Casos de uso

- usuarios activos: priorizar cluster propio;
- usuarios abiertos a descubrir: mezclar cluster propio y cluster vecino;
- usuarios con poca actividad: apoyarse mas en onboarding, categorias guardadas o popularidad global;
- usuarios sin historial: fallback a onboarding, ciudad y eventos tendencia.

### 2.3. Tablas objetivo para serving

Conviene terminar con tablas consumibles por producto:

- `user_cluster_assignments`;
- `cluster_profiles`;
- `cluster_neighbors`;
- `cluster_event_affinity`;
- `user_recommendation_candidates` o una vista equivalente.

Estado: completado en version inicial batch.

Tablas creadas en `project3grupo3.recomendacion_planes_marts`:

- `user_cluster_assignments`;
- `cluster_profiles`;
- `cluster_neighbors`;
- `cluster_event_affinity`;
- `user_recommendation_candidates`.

Implementacion:

- `clustering/4_serving_recomendaciones_cluster/step_1_load_cluster_outputs.py`;
- `clustering/4_serving_recomendaciones_cluster/step_2_build_cluster_event_affinity.py`;
- `clustering/4_serving_recomendaciones_cluster/step_3_generate_user_recommendation_candidates.py`;
- `clustering/4_serving_recomendaciones_cluster/step_4_validate_serving_outputs.py`;
- `clustering/4_serving_recomendaciones_cluster/run_serving_pipeline.py`.

Resultado de validacion:

- usuarios asignados: 196;
- perfiles de cluster: 4;
- relaciones cluster vecino: 12;
- filas de afinidad cluster-evento: 65;
- candidatos recomendados: 5.880;
- usuarios con recomendaciones: 196;
- maximo de candidatos por usuario: 30.

La logica actual:

- usa el cluster propio con peso principal;
- incorpora clusters vecinos como discovery;
- excluye eventos ya vistos por el usuario;
- prioriza afinidad historica por segmento, genero y banda de precio;
- anade pequenos boosts por ciudad del usuario y urgencia temporal.

## Fase 3. Integracion en la aplicacion

Estado: siguiente bloque recomendado de trabajo.

### 3.1. Captura de datos

Ampliar la calidad del dato que llega desde swipes.

Cambios recomendados:

- revisar `SwipePage.tsx` para asegurar que cada swipe envia siempre contexto consistente;
- enriquecer el evento publicado con mas snapshot analitico si hace falta: `segmento`, `genero`, `subgenero`, `ciudad`, precio, fecha del evento y posicion en ranking;
- decidir si `dwell_ms` va a ser una feature real y asegurar su calidad.

Siguiente paso concreto:

- validar en BigQuery que los eventos publicados ya incluyen `schema_version`, `dwell_ms`, `rank_position`, `producer` y `event_snapshot`.
- completado: sincronizar `preferred_location` y `preferred_budget` del perfil de usuario a BigQuery en `recomendacion_planes.user_preferences`.

### 3.2. Capa analitica dbt

Anadir modelos nuevos sobre el pipeline actual.

Propuesta de modelos:

- `int_user_swipe_features_30d`;
- `int_user_swipe_features_90d`;
- `int_user_reference_city`;
- `dim_user_cluster_features_current`;
- `fct_user_cluster_assignment`;
- `dim_cluster_profile`;
- `dim_cluster_neighbors`.

Siguiente paso concreto:

- completado: incorporar `reference_city` al pipeline analitico y priorizar `preferred_location` cuando existe;
- ejecutar `dbt parse/build` en un entorno con dbt instalado y BigQuery configurado;
- exportar `dim_user_cluster_features_current` y entrenar el clustering con datos reales.

### 3.3. Capa de producto

Definir como consulta la app el cluster del usuario.

Opciones viables:

- exponer desde backend un endpoint de recomendaciones ya rankeadas;
- o exponer el cluster y resolver candidatos en backend con consulta a BigQuery;
- o materializar una tabla de recomendaciones y consumirla desde backend.

Para este proyecto, la opcion mas limpia suele ser: materializar recomendaciones batch en BigQuery y servirlas desde backend con una consulta controlada.

Siguiente paso concreto:

- completado: se materializo una tabla de candidatos recomendados por usuario en BigQuery.
- completado: se creo el endpoint backend `GET /api/v1/users/me/recommendations`.
- completado: se creo una vista frontend `/recommendations` para consumir y mostrar recomendaciones clusterizadas.

Entregables:

- `backend/portal-api/app/api/v1/endpoints/recommendations.py`;
- `backend/portal-api/app/services/recommendations.py`;
- `backend/portal-api/app/schemas/recommendation.py`;
- `frontend/portal/src/pages/RecommendationsPage.tsx`;
- contrato TypeScript `ClusterRecommendationRead` en `frontend/portal/src/api.ts`.

Siguiente paso concreto:

- probar con un usuario real desplegado que tenga filas en `user_cluster_assignments`;
- completado: anadir fallback de cold start en `GET /api/v1/users/me/recommendations` para usuarios sin cluster o sin candidatos.

## Fase 4. Paso de local a Google Cloud

Estado: implementado en codigo e infraestructura declarativa, pendiente de aplicar y probar en GCP.

### 4.1. Servicios GCP recomendados

La ruta alineada con el repo actual es:

- Pub/Sub para la ingesta de swipes;
- BigQuery para raw, features y salidas de clustering;
- dbt en Cloud Run Job para transformaciones;
- un Cloud Run Job adicional para entrenar, asignar clusters y regenerar recomendaciones;
- Cloud Scheduler para ejecutar el job semanalmente;
- GCS para guardar artefactos si se quiere persistir el modelo y metricas;
- Terraform para declarar toda la infraestructura nueva.

### 4.2. Estrategia de despliegue recomendada

#### Opcion MVP recomendada

Mantener el entrenamiento en Python con `scikit-learn` y ejecutarlo como Cloud Run Job.

Ventajas:

- replica casi exacta del prototipo local;
- menor tiempo de entrega;
- mas control sobre features y logica de cercania entre clusters.

#### Opcion futura

Evaluar BigQuery ML o Vertex AI cuando el pipeline ya este estabilizado.

Cuadra mejor si:

- el volumen crece mucho;
- queremos versionado avanzado de modelos;
- o necesitamos una plataforma de experimentacion mas formal.

## Fase 5. Infraestructura a crear en Terraform

Estado: implementado en `terraform/main.tf`, pendiente de `terraform apply` y prueba manual.

Implementado:

1. permisos IAM para que `portal-api` lea recomendaciones en BigQuery;
2. permisos IAM para que `portal-api` sincronice preferencias de usuario en BigQuery;
3. un `cloud_run_job` para `clustering-train-assign`;
4. un `scheduler` semanal los lunes a la 01:00 Europe/Madrid;
5. permisos IAM para que el job lea features y escriba outputs en BigQuery;
6. carga automatica de `user_cluster_assignments`, `cluster_profiles`, `cluster_neighbors`, `cluster_event_affinity` y `user_recommendation_candidates`.
7. tabla `recomendacion_planes.user_preferences` para disponibilizar `preferred_location` al pipeline dbt.

Pendiente opcional:

- bucket GCS para versionar artefactos del modelo, metricas y reportes;
- monitorizacion de drift y calidad.

## Fase 6. Validacion y medicion

Estado: pendiente. La validacion offline inicial ya existe sobre datos sinteticos, pero falta validacion con datos reales y medicion en producto.

### 6.1. Validacion offline

Antes de usar el clustering en producto hay que comprobar:

- que los clusters sean estables;
- que tengan interpretacion de negocio;
- que las recomendaciones derivadas tengan afinidad superior a una baseline popular/global;
- que no se sesguen solo por nivel de actividad.

### 6.2. Validacion en producto

Metricas recomendadas:

- CTR o `right_swipe_rate` sobre recomendaciones clusterizadas;
- guardados o aperturas de detalle;
- diversidad consumida por usuario;
- conversion a plan o evento guardado;
- cobertura: porcentaje de usuarios con cluster asignable.

## Fase 7. Orden de ejecucion recomendado

### Sprint 1. Prototipo local

- completado: generar dataset sintetico;
- completado: construir features;
- completado: entrenar y evaluar KMeans;
- completado: definir clusters cercanos;
- completado: documentar decision de `k` y primeras lecturas de negocio.

### Sprint 2. Integracion analitica

- completado: mapear features del prototipo contra `fct_swipes`;
- completado: generar borradores dbt para 30d, 90d y `dim_user_cluster_features_current`;
- completado: definir contrato enriquecido del swipe;
- completado: adaptar el entrenamiento para leer exports reales de features;
- completado: promover esos borradores a modelos reales del proyecto;
- completado: actualizar `stg_swipes` y `fct_swipes` para soportar `dwell_ms`, precio y snapshot enriquecido;
- completado: implementar `swipe_event_contract_v2` en frontend y backend;
- completado: generar y cargar swipes sinteticos de demo contra eventos reales en `swipes_raw`;
- completado: definir `reference_city` en el pipeline de features y serving, con prioridad para `preferred_location`;
- completado: sincronizar preferencias de usuario a BigQuery mediante `user_preferences`.

### Sprint 3. Despliegue GCP

- completado: preparar scaffold del job en GCP;
- completado: empaquetar el job definitivo sobre tablas BigQuery;
- completado: crear recursos Terraform reales para Cloud Run Job y Scheduler;
- completado: orquestar retraining semanal con Scheduler;
- pendiente: aplicar Terraform y desplegar en GCP;
- pendiente: validar escritura en BigQuery y trazabilidad end to end.

### Sprint 4. Activacion en producto

- conectar backend con las tablas de recomendaciones;
- completado: implementar fallback de cold start desde catalogo de eventos futuros cuando no existan candidatos clusterizados;
- activar ranking por cluster en un entorno controlado;
- medir impacto frente a una baseline sin clustering.

## Proximos pasos recomendados

Orden recomendado a partir de hoy:

1. Probar end to end la vista `/recommendations` con un usuario real/desplegado que tenga candidatos.
2. Probar end to end la vista `/recommendations` con un usuario nuevo o sin candidatos para validar `cluster_source = cold_start`.
3. Validar offline la calidad de `user_recommendation_candidates` por cluster y por persona demo.
4. Publicar swipes reales desde la app y validar en `stg_swipes` que llega el contrato `v2`.
5. Resolver la estrategia de precio para clustering:
   usar `precio_min/precio_max` si se incorporan;
   o usar temporalmente `banda_precio` como proxy.
6. Aplicar Terraform y ejecutar manualmente `clustering-train-assign` antes de depender del scheduler semanal.
7. Validar en BigQuery la cobertura real de `reference_city_source` entre `preferred_location`, `liked_swipes_90d` y `swipes_90d`.

## Siguiente entregable recomendado

El siguiente entregable con mejor relacion valor/esfuerzo es:

- validar que un usuario existente recibe eventos ordenados desde `user_recommendation_candidates`;
- validar que un usuario sin candidatos recibe eventos con `cluster_source = cold_start`;
- preparar el despliegue frontend/backend para probarlo en la app real.

## Bloqueos actuales mas importantes

- `precio_min` y `precio_max` dependen de que el frontend/catalogo los tenga disponibles; mientras tanto `banda_precio` queda codificada como proxy numerico (`bajo=15`, `medio=45`, `alto=90`);
- falta validar el contrato enriquecido con datos reales en BigQuery.

## Decisiones tecnicas recomendadas desde el inicio

- usar ventanas moviles de 30 dias para asignacion operativa y 90 dias para estabilidad;
- excluir del entrenamiento a usuarios con interacciones insuficientes;
- recalcular clusters al menos una vez al dia en batch;
- separar el calculo del cluster de la logica final de ranking;
- guardar siempre explicabilidad basica por cluster: top gustos, ciudades, precios y comportamientos.

## Resultado esperado

Si seguimos este plan, la aplicacion terminara con un sistema en el que:

- cada usuario tiene un cluster interpretable;
- cada cluster tiene vecinos utiles para discovery;
- las recomendaciones pueden apoyarse en comportamiento colectivo sin perder contexto individual;
- el prototipo local y la version en GCP comparten la misma logica y la misma estructura de datos.
