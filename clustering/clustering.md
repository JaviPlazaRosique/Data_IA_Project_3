# Clustering Basado en Swipes

**Última revisión:** April 2026

## Objetivo

Usar la mecánica de tarjetas deslizables como señal principal para construir clusters de usuarios según sus gustos reales.

La lógica es simple:

- `swipe_right` indica interés explícito,
- `swipe_left` indica rechazo explícito,
- y el historial acumulado de swipes permite detectar patrones de preferencia por tipo de evento.

---

## Situación actual

Con la arquitectura actual **no se está guardando todavía** una señal explícita de:

- evento recomendado,
- respuesta del usuario a esa recomendación,
- contexto en el que apareció la tarjeta,
- ni rechazo explícito al evento.

Actualmente existen datos de:

- perfil de usuario,
- favoritos,
- planes del AI Planner,
- catálogo de eventos.

Eso ayuda, pero no basta para un clustering basado en swipes.  
Para esta funcionalidad hace falta desarrollar una nueva capa de captura de interacciones.

---

## Qué guardar por cada swipe

Cada swipe debe persistirse como una interacción usuario-evento.

Campos mínimos recomendados:

| Campo | Tipo | Descripción |
|------|------|-------------|
| `interaction_id` | string | ID único de la interacción |
| `event_timestamp` | timestamp | Momento del swipe |
| `user_id` | string | Usuario autenticado |
| `session_id` | string | Sesión si no hay usuario autenticado o como apoyo analítico |
| `event_id` | string | Evento mostrado |
| `interaction_type` | string | Siempre `swipe` en este caso |
| `swipe_direction` | string | `right` o `left` |
| `liked` | boolean | `true` si `right`, `false` si `left` |
| `recommendation_context` | string | Origen de la recomendación: `discover`, `map`, `planner`, etc. |
| `segmento` | string | Segmento del evento |
| `genero` | string | Género del evento |
| `subgenero` | string | Subgénero del evento |
| `ciudad` | string | Ciudad del evento |
| `precio_min` | float | Precio mínimo del evento |
| `precio_max` | float | Precio máximo del evento |
| `fecha_evento` | date | Fecha del evento |
| `recinto_id` | string | ID del recinto |
| `ingestion_timestamp` | timestamp | Momento de escritura técnica |

Recomendación importante:

- guardar un **snapshot del evento** en el momento del swipe,
- no depender solo del catálogo vivo para reconstruir después el contexto.

---

## Tabla recomendada en BigQuery

Nombre propuesto:

- `user_event_interactions`

Granularidad:

- una fila por interacción de usuario con un evento.

Partición recomendada:

- por `event_timestamp`

Clustering recomendado en BigQuery:

- `user_id`
- `interaction_type`
- `swipe_direction`
- `segmento`

---

## Variables para generar clusters

A partir de la tabla de swipes, las variables más útiles para clustering serían:

| Variable | Tipo | Descripción |
|---------|------|-------------|
| `total_swipes_30d` | numérica | Actividad reciente |
| `right_swipe_rate_30d` | numérica | Proporción de likes |
| `left_swipe_rate_30d` | numérica | Proporción de dislikes |
| `music_like_rate_30d` | numérica | Afinidad con música |
| `sports_like_rate_30d` | numérica | Afinidad con deportes |
| `arts_like_rate_30d` | numérica | Afinidad con artes |
| `family_like_rate_30d` | numérica | Afinidad con eventos familiares |
| `top_genre_like_rate` | numérica | Afinidad por género dominante |
| `distinct_segments_liked_30d` | numérica | Diversidad de gustos |
| `distinct_cities_liked_30d` | numérica | Disposición geográfica |
| `avg_liked_price_30d` | numérica | Precio medio de eventos aceptados |
| `avg_disliked_price_30d` | numérica | Precio medio de eventos rechazados |
| `same_city_like_rate_30d` | numérica | Afinidad por eventos locales |
| `days_until_event_avg_liked` | numérica | Cuánta antelación acepta |
| `days_since_last_right_swipe` | numérica | Recencia de interés positivo |

Estas variables ya permitirían separar perfiles como:

- usuarios muy selectivos,
- usuarios abiertos a explorar,
- usuarios locales,
- usuarios dispuestos a desplazarse,
- usuarios sensibles al precio,
- usuarios claramente orientados a ciertos géneros.

---

## Qué falta desarrollar

Para soportar esta estrategia faltan al menos estas piezas:

1. Frontend
   Registrar cada `swipe_left` y `swipe_right`.

2. Backend
   Exponer un endpoint tipo `POST /api/v1/interactions`.

3. Persistencia analítica
   Guardar esas interacciones en BigQuery.

4. Pipeline de features
   Agregar interacciones por usuario para generar variables de clustering.

5. Job de clustering
   Recalcular clusters de forma periódica.

---

## Recomendación práctica

La mejor forma de empezar es:

1. Implementar el registro de swipes en `BigQuery`.
2. Guardar también el contexto del evento y del recomendador.
3. Construir una tabla agregada diaria por usuario.
4. Entrenar el clustering sobre ventanas móviles de 30 o 90 días.

El valor real del clustering vendrá más de la calidad de esta captura de interacciones que del algoritmo en sí.
