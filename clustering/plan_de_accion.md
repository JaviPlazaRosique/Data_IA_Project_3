# Plan de Accion para Clustering de Gustos y Recomendacion por Afinidad

## Objetivo

Construir una capacidad de clustering que agrupe usuarios segun sus gustos observados en la app, usando sobre todo el historial de swipes, para poder:

- recomendar planes populares dentro de su cluster;
- recomendar planes de clusters cercanos cuando queramos ampliar discovery sin perder afinidad;
- recalcular segmentos de forma periodica y automatizable;
- llevar el prototipo local a Google Cloud sin rehacer arquitectura.

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

### 1.1. Dataset local de trabajo

Usar como base la estructura analitica ya preparada para swipes y generar un dataset sintetico con suficiente variabilidad de usuarios.

Acciones:

- crear una muestra local con usuarios y eventos sinteticos inspirados en la forma de `fct_swipes`;
- asegurar que haya diversidad realista en `segmento`, `genero`, `subgenero`, `ciudad`, precio, antelacion al evento y frecuencia de swipe;
- introducir perfiles sinteticos reconocibles para validar que el clustering los recupera;
- definir un minimo de interacciones por usuario para poder entrar en clustering.

### 1.2. Feature engineering local

Construir una tabla de features a nivel usuario, idealmente sobre ventanas de 30 y 90 dias.

Features recomendadas:

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

Acciones:

- probar varios valores de `k`;
- comparar `silhouette`, `davies_bouldin`, tamano de clusters y estabilidad entre semillas;
- revisar manualmente perfiles medios por cluster;
- descartar clusters que sean puro ruido o que solo separen por actividad extrema.

### 1.4. Definicion de clusters cercanos

Para poder recomendar planes de clusters vecinos, calcular cercania entre centroides.

Regla inicial recomendada:

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

## Fase 2. Diseno de recomendacion apoyada en clusters

El clustering no debe recomendar eventos por si solo; debe actuar como senal de priorizacion.

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

## Fase 3. Integracion en la aplicacion

### 3.1. Captura de datos

Ampliar la calidad del dato que llega desde swipes.

Cambios recomendados:

- revisar `SwipePage.tsx` para asegurar que cada swipe envia siempre contexto consistente;
- enriquecer el evento publicado con mas snapshot analitico si hace falta: `segmento`, `genero`, `subgenero`, `ciudad`, precio, fecha del evento y posicion en ranking;
- decidir si `dwell_ms` va a ser una feature real y asegurar su calidad.

### 3.2. Capa analitica dbt

Anadir modelos nuevos sobre el pipeline actual.

Propuesta de modelos:

- `int_user_swipe_features_30d`;
- `int_user_swipe_features_90d`;
- `dim_user_cluster_features_current`;
- `fct_user_cluster_assignment`;
- `dim_cluster_profile`;
- `dim_cluster_neighbors`.

### 3.3. Capa de producto

Definir como consulta la app el cluster del usuario.

Opciones viables:

- exponer desde backend un endpoint de recomendaciones ya rankeadas;
- o exponer el cluster y resolver candidatos en backend con consulta a BigQuery;
- o materializar una tabla de recomendaciones y consumirla desde backend.

Para este proyecto, la opcion mas limpia suele ser: materializar recomendaciones batch en BigQuery y servirlas desde backend con una consulta controlada.

## Fase 4. Paso de local a Google Cloud

### 4.1. Servicios GCP recomendados

La ruta mas alineada con el repo actual es:

- Pub/Sub para la ingesta de swipes;
- BigQuery para raw, features y salidas de clustering;
- dbt en Cloud Run Job para transformaciones;
- un Cloud Run Job adicional para entrenar y asignar clusters;
- Cloud Scheduler para ejecutar el job con frecuencia;
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

Propuesta minima:

1. nuevas tablas BigQuery para features, asignaciones, perfiles y vecinos;
2. un `cloud_run_job` para `clustering-train-assign`;
3. un `scheduler` que lance el job diariamente o varias veces por semana;
4. un bucket GCS para artefactos del modelo, metricas y reportes;
5. permisos IAM para que el job lea BigQuery y escriba resultados.

Si queremos cerrar el ciclo completo, despues se puede anadir:

- tabla materializada de recomendaciones por usuario;
- endpoint backend para servir esas recomendaciones;
- monitorizacion de drift y calidad.

## Fase 6. Validacion y medicion

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

- generar dataset sintetico;
- construir features;
- entrenar y evaluar KMeans;
- definir clusters cercanos;
- documentar decision de `k` y primeras lecturas de negocio.

### Sprint 2. Integracion analitica

- reforzar payload de swipes si hace falta;
- anadir modelos dbt de features;
- definir tablas de salida;
- preparar script batch reproducible con inputs y outputs claros.

### Sprint 3. Despliegue GCP

- empaquetar el job de clustering;
- crear recursos Terraform;
- desplegar en Cloud Run Job;
- orquestar con Scheduler;
- validar escritura en BigQuery y trazabilidad end to end.

### Sprint 4. Activacion en producto

- conectar backend con las tablas de recomendaciones;
- activar ranking por cluster en un entorno controlado;
- medir impacto frente a una baseline sin clustering.

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
