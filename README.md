# NextPlan

> Recomendador de planes y eventos con IA, desplegado en Google Cloud.

NextPlan es una plataforma para descubrir eventos en España. Los usuarios exploran planes en un mapa, hacen swipe sobre lo que les gusta y conversan con un agente IA que les crea itinerarios personalizados. La plataforma aprende de cada interacción para afinar las recomendaciones.

## Visión general

- Catálogo de eventos enriquecido con Gemini e indexado para RAG en BigQuery.
- Frontend con swipe, mapa, detalle de evento y un agente IA que planifica ([AIPlannerPage.tsx](frontend/portal/src/pages/AIPlannerPage.tsx)).
- Pipeline de aprendizaje: swipes → Pub/Sub → BigQuery → dbt → clustering K-Means → recomendaciones servidas a cada usuario.
- Loop de valoración post-evento por email para cerrar el ciclo de feedback (cumplimiento RGPD Art. 5).

## Arquitectura

```
                       ┌──────────────────┐
                       │   Ticketmaster   │
                       └────────┬─────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │      ingestion/        │
                    │  Apache Beam + Gemini  │
                    └────────────┬───────────┘
                                 │
                                 ▼
    ┌────────────────────────────────────────────────────────┐
    │            BigQuery (recomendacion_planes)             │
    │     eventos · swipes_raw · valoraciones_eventos        │
    └─┬───────────────┬──────────────────┬───────────────────┘
      │               │                  │
      ▼               ▼                  ▼
  ┌────────┐  ┌────────────────┐  ┌────────────────────┐
  │ agent/ │  │ transformations│  │  ia_motor_imagenes │
  │  RAG   │  │     (dbt)      │  │  Gemini + Pollin.  │
  └───┬────┘  └────────┬───────┘  └────────────────────┘
      │                │
      │                ▼
      │       ┌──────────────────┐
      │       │   clustering/    │
      │       │  K-Means → recs  │
      │       └────────┬─────────┘
      │                │
      ▼                ▼
   ┌────────────────────────────────┐         ┌──────────────────┐
   │     backend/portal-api         │ ◄────── │ frontend/portal  │
   │     backend/admin-api          │ ◄────── │ frontend/admin   │
   └─────────────┬──────────────────┘         └──────────────────┘
                 │
                 ▼
         Pub/Sub swipe-events ──► BigQuery swipes_raw
                 │
                 ▼
    backend/valoracion (Cloud Functions + SendGrid)
```

## Módulos

### [`ingestion/`](ingestion/)

Ingesta batch desde la API de Ticketmaster, enriquecimiento con Gemini (descripción, categoría, banda horaria) y generación de embeddings. Escribe a BigQuery `recomendacion_planes.eventos`.

- **Scripts**: [`pipeline_batch_ingestion.py`](ingestion/pipeline_batch_ingestion.py) (Apache Beam), [`backfill_embeddings.py`](ingestion/backfill_embeddings.py), [`migrar_rag.py`](ingestion/migrar_rag.py).
- **Stack**: Python, Apache Beam, Vertex AI (Gemini), Secret Manager.
- **Despliegue**: Dataflow Flex Template, lanzado por Cloud Scheduler dos veces al día.

### [`transformations/`](transformations/)

Capa dbt sobre BigQuery que convierte los swipes crudos en features para el modelo de clustering.

- **Staging**: `stg_swipes` (parsea el envelope JSON publicado en Pub/Sub).
- **Intermediate**: `int_user_swipe_features_30d`, `int_user_swipe_features_90d`, `int_user_reference_city`.
- **Marts**: `fct_swipes`, `dim_user_cluster_features_current`.
- **Despliegue**: Cloud Run Job, lanzado por Cloud Scheduler (lunes y jueves).

### [`clustering/`](clustering/)

K-Means propio (implementación en [`step_4_entrenar_desde_feature_export.py`](clustering/2_integracion_datos_gcp/step_4_entrenar_desde_feature_export.py)) que agrupa usuarios por gustos y materializa recomendaciones. Estructurado en cuatro fases:

1. [`1_prototipo_local/`](clustering/1_prototipo_local/) — Prototipo offline con datos sintéticos.
2. [`2_integracion_datos_gcp/`](clustering/2_integracion_datos_gcp/) — Pipeline real contra BigQuery.
3. [`3_generacion_interacciones_demo/`](clustering/3_generacion_interacciones_demo/) — Genera swipes sintéticos sobre eventos reales.
4. [`4_serving_recomendaciones_cluster/`](clustering/4_serving_recomendaciones_cluster/) — Materializa `user_recommendation_candidates` en BigQuery.

- **Despliegue**: Cloud Run Job, semanal (lunes 01:00 Madrid).

### [`agent/`](agent/)

Agente conversacional con **Google ADK** desplegado en **Vertex AI Agent Engine**. Pipeline secuencial en dos pasos:

1. **Extractor** ([`extractor.py`](agent/extractor.py)) — `LlmAgent` que extrae de la pregunta del usuario un JSON con `question`, `ciudad`, `category`, `referencia_temporal` (resuelve "esta noche", "este finde" a fechas ISO).
2. **Ejecutor** ([`agent.py`](agent/agent.py)) — Llama a la tool `buscar_eventos`, que ejecuta `VECTOR_SEARCH` sobre BigQuery con embeddings semánticos.

- **Modelo**: `gemini-2.5-flash` (configurable en [`config.py`](agent/config.py)).
- **Embeddings**: `gemini-embedding-001`, 3072 dimensiones.

### [`ia_motor_imagenes/`](ia_motor_imagenes/)

Genera portadas de evento. Para cada evento con `contexto_rag`, Gemini elabora una descripción visual (prompt de director de arte) y la API de **Pollinations.ai** produce la imagen final (768x1024). El resultado se sube a `gs://portadas-{project_id}/`.

### [`database/`](database/)

Esquema PostgreSQL gestionado con **Alembic** ([`alembic.ini`](database/alembic.ini), [`versions/`](database/versions/)). Tablas principales:

- `users` — id (UUID), email, hashed_password, full_name, preferred_budget, preferred_location, preferred_categories, is_admin, etc.
- `saved_events` — eventos que cada usuario ha guardado.

Doce migraciones, incluyendo la migración a Firebase Authentication.

### [`backend/portal-api/`](backend/portal-api/)

API REST FastAPI para los usuarios finales. Endpoints clave:

- `POST /api/v1/agent/chat` — proxy al agente IA, con sanitización de prompts (inyección/toxicidad).
- `GET /api/v1/users/me/recommendations` — lee de BigQuery `user_recommendation_candidates`.
- `POST /api/v1/users/me/saved-events` — escribe en Firestore.
- `POST /api/v1/users/me/swipe-events` — publica en Pub/Sub `swipe-events`.

Middleware de audit logging (RGPD Art. 32), CSP headers y rate limiting.

### [`backend/admin-api/`](backend/admin-api/)

API FastAPI para administración: gestión de eventos, usuarios, analíticas y estadísticas. Conecta con Cloud SQL, Firestore y BigQuery. Mismo middleware de audit logging que `portal-api`.

### [`backend/valoracion/`](backend/valoracion/)

Dos Cloud Functions HTTP que cierran el loop de feedback por email:

- [`envio_email/`](backend/valoracion/envio_email/) — Recibe una recomendación, genera un JWT (HS256, caducidad 30 días) con `user_id` y `event_id`, y envía un email vía **SendGrid** con dos botones: "Me gustó" y "No me gustó".
- [`recepcion_mail/`](backend/valoracion/recepcion_mail/) — Valida el JWT cuando el usuario pulsa el botón e inserta la valoración en BigQuery `valoraciones_eventos`.

Encolado por Cloud Tasks desde `portal-api` cuando se sirven recomendaciones.

### [`frontend/portal/`](frontend/portal/)

SPA React 19 + Vite + Tailwind CSS v4 con auth Firebase. Páginas en [`src/pages/`](frontend/portal/src/pages/):

| Ruta | Página | Función |
|---|---|---|
| `/map` | `MapPage` | Mapa con markers de eventos (Google Maps + clustering) |
| `/swipe` | `SwipePage` | Interfaz de swipe (like/dislike) |
| `/planner` | `AIPlannerPage` | Chat con el agente IA |
| `/event/:id` | `EventDetailsPage` | Detalle de evento |
| `/profile` | `ProfilePage` | Preferencias del usuario |
| `/onboarding` | `OnboardingPage` | Selección inicial de categorías |
| `/login`, `/register` | `LoginPage`, `RegisterPage` | Autenticación |
| `/privacy` | `PrivacyPage` | Política de privacidad |

### [`frontend/admin/`](frontend/admin/)

Dashboard React + Recharts en [`DashboardPage.tsx`](frontend/admin/src/pages/DashboardPage.tsx) con seis pestañas: `overview`, `events`, `analytics`, `saved-events`, `planner`, `architecture`.

## Stack tecnológico

| Capa | Tecnologías |
|---|---|
| IA | Vertex AI Gemini 2.5 Flash, `gemini-embedding-001`, Google ADK |
| Backend | FastAPI, SQLAlchemy async, Pydantic |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS v4, Recharts |
| Datos | BigQuery (analítica + RAG), Cloud SQL Postgres (transaccional), Firestore (estado de usuario y eventos) |
| Eventos | Pub/Sub, Cloud Tasks |
| Cómputo | Cloud Run, Cloud Run Jobs, Cloud Functions, Dataflow Flex Template |
| Orquestación | Cloud Scheduler |
| Auth | Firebase Authentication, JWT (`python-jose`) |
| Storage | Cloud Storage |
| Infra | Terraform |
| CI/CD | GitHub Actions + Workload Identity Federation |

## Despliegue

- **Infra**: toda la infraestructura GCP está en [`terraform/`](terraform/), con 20 módulos en [`terraform/modules/`](terraform/modules/) (Cloud Run, BigQuery, Pub/Sub, Firestore, Cloud SQL, Vertex AI Agent Engine, IAM, WIF, Secret Manager, etc.). Región por defecto `europe-west1`.
- **CI/CD**: 11 workflows en [`.github/workflows/`](.github/workflows/), uno por componente. Autenticación GitHub → GCP vía Workload Identity Federation (sin claves estáticas).
- **IAM**: las concesiones IAM se gestionan en Terraform, no con `gcloud`.

## Cumplimiento RGPD

Documentación en [`docs/gdpr/`](docs/gdpr/): registro de actividades de tratamiento (`ropa.md`), encargados de tratamiento (`processors.md`), evaluación de impacto (`dpia_notes.md`) y respuesta a brechas (`breach_response.md`).

A nivel de código, ambos backends tienen middleware de audit logging (Art. 32) y el loop de valoración por email implementa la trazabilidad del consentimiento del usuario (Art. 5, accountability).

## Estructura del repo

```
.
├── agent/                # Agente RAG (Vertex AI Agent Engine + Gemini)
├── backend/
│   ├── admin-api/        # API de administración (FastAPI)
│   ├── portal-api/       # API de usuarios (FastAPI)
│   └── valoracion/       # Cloud Functions de feedback por email
├── clustering/           # K-Means de gustos + serving de recomendaciones
├── database/             # Esquema Postgres (Alembic)
├── docs/gdpr/            # Documentación RGPD
├── frontend/
│   ├── admin/            # Dashboard de admin (React)
│   └── portal/           # App de usuario (React)
├── ia_motor_imagenes/    # Generador de portadas (Gemini + Pollinations)
├── ingestion/            # Pipeline batch (Beam/Dataflow)
├── local/                # Stack local con Docker Compose
├── terraform/            # IaC: 20 módulos GCP
├── transformations/      # Modelos dbt
└── .github/workflows/    # 11 pipelines CI/CD
```
