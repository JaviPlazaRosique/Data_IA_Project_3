# AI Plan

Este documento recoge una propuesta concreta de implementaciones de inteligencia artificial para este repositorio, priorizadas por impacto y por facilidad de reutilizar la infraestructura que ya existe en GCP, Firestore, Cloud Run y el pipeline de ingestión.

## Top 5 funciones de IA para este repo

### 1. AI Planner real con Gemini

- **Impacto:** Muy alto
- **Dificultad:** Media

**Qué haría**

- Responder al usuario en el chat del planner.
- Sugerir eventos concretos del catálogo.
- Generar un `itinerary` estructurado.
- Guardar conversación y plan en Firestore.

**Por qué encaja**

- Ya existe la UI del planner.
- Ya existen `plans` en Firestore.
- Ya se usa Gemini en la ingesta.
- Ya existe backend en Cloud Run con autenticación.

**Archivos a tocar**

- [backend/portal-api/app/api/v1/endpoints/plans.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/plans.py)
- `backend/portal-api/app/services/planner_ai.py` nuevo
- [backend/portal-api/app/schemas/plan.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/schemas/plan.py)
- [backend/portal-api/app/config.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/config.py)
- [backend/portal-api/requirements.txt](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/requirements.txt)
- [frontend/portal/src/pages/AIPlannerPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/AIPlannerPage.tsx)
- [frontend/portal/src/api.ts](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/api.ts)
- [terraform/main.tf](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/terraform/main.tf)

**Infra necesaria**

- Añadir `roles/aiplatform.user` al backend.
- Pasar `GOOGLE_CLOUD_PROJECT`, `VERTEX_AI_REGION` y `GEMINI_MODEL`.

### 2. Recomendador personalizado para Discover

- **Impacto:** Muy alto
- **Dificultad:** Media

**Qué haría**

- Ordenar eventos por afinidad del usuario.
- Usar favoritos, reviews, ubicación y presupuesto.
- Mostrar una sección de recomendaciones personalizadas reales.

**Por qué encaja**

- Ya se guardan `saved_events`, `event_reviews` y preferencias de usuario.
- Ya existe `DiscoverPage`.
- El backend ya devuelve eventos y perfil.

**Archivos a tocar**

- [backend/portal-api/app/api/v1/endpoints/events.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/events.py)
- `backend/portal-api/app/services/recommendations.py` nuevo
- [backend/portal-api/app/models/user.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/models/user.py)
- [backend/portal-api/app/api/v1/endpoints/saved_events.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/saved_events.py)
- [backend/portal-api/app/api/v1/endpoints/reviews.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/reviews.py)
- [frontend/portal/src/pages/DiscoverPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/DiscoverPage.tsx)
- [frontend/portal/src/api.ts](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/api.ts)

**Implementación recomendada**

- Empezar con ranking heurístico.
- Después, añadir reranking o explicación con Gemini.

### 3. Búsqueda semántica en lenguaje natural

- **Impacto:** Alto
- **Dificultad:** Media-Alta

**Qué haría**

- Permitir búsquedas como `algo barato este sábado en Madrid con música en directo`.
- Traducir la intención del usuario a filtros estructurados y ranking.
- Mejorar el descubrimiento más allá de filtros rígidos.

**Por qué encaja**

- Mejora mucho la usabilidad del catálogo.
- Puede implementarse primero sin vector DB, usando Gemini para extraer intención.

**Archivos a tocar**

- [backend/portal-api/app/api/v1/endpoints/events.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/events.py)
- `backend/portal-api/app/services/event_search_ai.py` nuevo
- `backend/portal-api/app/schemas/search.py` nuevo
- [frontend/portal/src/pages/DiscoverPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/DiscoverPage.tsx)
- [frontend/portal/src/pages/MapPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/MapPage.tsx)
- [frontend/portal/src/api.ts](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/api.ts)

**MVP recomendado**

- Gemini recibe la query.
- Devuelve JSON con `ciudad`, `segmentos`, `fecha`, `budget` y `vibe`.
- El backend consulta Firestore con esos filtros y devuelve resultados ordenados.

### 4. Enriquecimiento semántico del catálogo en la ingesta

- **Impacto:** Alto
- **Dificultad:** Media

**Qué haría**

- Añadir campos como `vibe`, `audience`, `price_band`, `indoor_outdoor`, `romantic`, `family_friendly` o `tourist_friendly`.
- Generar un resumen atractivo del evento.
- Mejorar planner, búsqueda y recomendaciones a la vez.

**Por qué encaja**

- Ya existe un pipeline batch con Gemini.
- Enriquecer el catálogo una sola vez abarata el resto de funciones inteligentes.

**Archivos a tocar**

- [ingestion/pipeline_batch_ingestion.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/ingestion/pipeline_batch_ingestion.py)
- [backend/portal-api/app/schemas/event.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/schemas/event.py)
- [backend/portal-api/app/api/v1/endpoints/events.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/events.py)
- [frontend/portal/src/api.ts](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/api.ts)
- [frontend/portal/src/pages/EventDetailsPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/EventDetailsPage.tsx)
- [frontend/portal/src/pages/DiscoverPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/DiscoverPage.tsx)

**Ventaja clave**

- Esta función alimenta varias otras a la vez.

### 5. Explicaciones personalizadas de recomendación

- **Impacto:** Medio-Alto
- **Dificultad:** Baja-Media

**Qué haría**

- Mostrar explicaciones del tipo:
- `Te lo recomendamos porque guardaste eventos similares`.
- `Encaja con tu presupuesto y tu zona preferida`.
- Aumentar confianza y engagement.

**Por qué encaja**

- Reutiliza perfil, favoritos, reseñas y metadatos enriquecidos.
- Es una mejora visible sin requerir una infraestructura nueva.

**Archivos a tocar**

- `backend/portal-api/app/services/recommendation_explanations.py` nuevo
- [backend/portal-api/app/api/v1/endpoints/events.py](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/backend/portal-api/app/api/v1/endpoints/events.py)
- [frontend/portal/src/pages/DiscoverPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/DiscoverPage.tsx)
- [frontend/portal/src/pages/EventDetailsPage.tsx](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/pages/EventDetailsPage.tsx)
- [frontend/portal/src/api.ts](/Users/brunoestevecastellano/Documents/EDEM/Data_IA_Project_3/frontend/portal/src/api.ts)

**Cuándo implementarla**

- Ideal como segunda fase después del recomendador básico.

## Prioridad recomendada

1. AI Planner real con Gemini
2. Enriquecimiento semántico del catálogo
3. Recomendador personalizado
4. Búsqueda semántica
5. Explicaciones personalizadas de recomendación

## Motivo de este orden

- El planner aporta una funcionalidad visible y diferencial.
- El enriquecimiento del catálogo mejora todas las demás funciones.
- El recomendador y la búsqueda ganan mucho valor si los eventos ya vienen enriquecidos.
- Las explicaciones rematan la experiencia y aumentan la confianza del usuario.
