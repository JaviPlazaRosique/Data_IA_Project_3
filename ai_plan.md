# Plan detallado para implementar la solución de IA del planner

## Objetivo

Queremos que el usuario pueda escribir una petición natural como:

- `quiero un plan romántico para el viernes por la noche`
- `busco algo barato en Madrid este sábado`
- `quiero un plan tranquilo con cena y concierto`

y que la aplicación responda con una recomendación útil basada en eventos reales almacenados en el catálogo, no con texto inventado por el modelo.

La solución correcta no es preguntar directamente a Gemini "qué recomiendas", sino construir un flujo de:

1. interpretación de intención,
2. recuperación de candidatos reales,
3. ranking,
4. generación final sobre esos candidatos,
5. persistencia del plan y de la conversación.

## Principio de diseño

La IA debe decidir sobre datos recuperados del sistema, no sobre memoria interna del modelo.

Eso implica:

- Firestore y el catálogo son la fuente de verdad.
- Gemini en Vertex AI se usa para entender la intención del usuario y redactar una respuesta final de calidad.
- El backend decide qué eventos son elegibles.
- La respuesta final se genera solo a partir de eventos previamente recuperados.

## Estado actual del repositorio

Hoy el proyecto ya tiene una base muy buena para este desarrollo:

- Un backend en Cloud Run.
- Firestore con colecciones como `eventos` y `plans`.
- Un pipeline de ingestión batch en Dataflow.
- Enriquecimiento con Gemini en la ingesta.
- Una UI de planner en `frontend/portal/src/pages/AIPlannerPage.tsx`.
- Persistencia básica de planes en `backend/portal-api/app/api/v1/endpoints/plans.py`.

También hay varias limitaciones actuales que conviene corregir para que la solución sea sólida:

- El planner guarda mensajes pero no genera respuestas inteligentes todavía.
- El esquema de eventos actual no contiene suficientes metadatos semánticos para recomendar bien.
- El endpoint de eventos filtra en memoria después de cargar muchos documentos, lo cual no escala.
- La cuenta de servicio del backend no tiene todavía el rol de Vertex AI necesario para invocar Gemini desde Cloud Run.

## Arquitectura objetivo en Google Cloud

### Componentes

- `Dataflow`
  - ingesta batch de eventos
  - enriquecimiento semántico del catálogo

- `Firestore`
  - catálogo operativo de eventos
  - persistencia de conversaciones y planes

- `Cloud Run`
  - API del planner
  - orquestación del flujo de IA
  - recuperación, ranking y persistencia

- `Vertex AI Gemini`
  - extracción estructurada de intención
  - generación final de la respuesta

- `Secret Manager`
  - configuración sensible y secretos

- `BigQuery Vector Search` opcional en fase 2
  - recuperación semántica avanzada cuando el catálogo crezca o la búsqueda por tags se quede corta

### Decisión técnica recomendada

Para este proyecto, la mejor primera versión es:

- `Firestore + Gemini + ranking heurístico`

y no:

- un RAG complejo desde el día 1,
- ni un sistema basado solo en embeddings,
- ni una búsqueda full-text improvisada.

Motivo:

- el catálogo es estructurado,
- ya existe ingesta con Gemini,
- ya existe Firestore,
- y el valor principal está en transformar intención en filtros y ranking sobre eventos reales.

## Flujo de datos óptimo

### Flujo 1: enriquecimiento del catálogo

1. El pipeline batch recoge eventos desde las fuentes actuales.
2. Se normalizan campos básicos:
   - fecha
   - hora
   - ciudad
   - recinto
   - segmento
   - género
   - coordenadas
3. Se obtienen datos complementarios del entorno:
   - restaurantes cercanos
   - alojamientos cercanos
4. Gemini genera metadatos semánticos del evento.
5. El evento enriquecido se guarda en Firestore.
6. Opcionalmente se guarda también una versión analítica en BigQuery.

### Flujo 2: petición del usuario en el planner

1. El usuario escribe una petición en la UI.
2. El frontend envía el mensaje al backend del planner.
3. El backend recupera contexto mínimo:
   - perfil del usuario si existe
   - preferencias históricas si existen
   - últimos mensajes del plan activo
4. Gemini transforma la petición natural en una intención estructurada.
5. El backend convierte esa intención en filtros de recuperación.
6. Firestore devuelve una lista de eventos candidatos.
7. El backend calcula un ranking.
8. Se seleccionan los mejores candidatos.
9. Gemini redacta una respuesta final usando solo esos candidatos.
10. El backend guarda:
    - mensaje del usuario
    - respuesta del asistente
    - candidatos recomendados
    - itinerario propuesto
11. El frontend renderiza la respuesta y las cards de eventos.

### Flujo 3: mejora continua

1. Se registran métricas de uso:
   - cuántas veces se consulta el planner
   - qué eventos se recomiendan
   - qué eventos se abren o guardan
2. Se analizan fallos:
   - consultas sin resultados
   - respuestas poco específicas
   - planes no guardados o abandonados
3. Se ajustan:
   - prompts
   - reglas de ranking
   - metadatos generados en la ingesta

## Diseño correcto de la solución

### Regla principal

El modelo nunca debe recibir todo el catálogo.

Debe recibir solo:

- la petición del usuario,
- una intención estructurada,
- y un conjunto pequeño de eventos ya filtrados por el backend.

### Por qué este enfoque es el correcto

Porque evita:

- alucinaciones,
- recomendaciones de eventos inexistentes,
- respuestas difíciles de explicar,
- problemas de coste por prompts demasiado grandes,
- y degradación del rendimiento cuando crezca el catálogo.

## Fase 1: enriquecer el catálogo para hacerlo "recomendable"

### Objetivo

Añadir a cada evento los metadatos que necesita la IA para decidir bien.

### Archivo principal

- `ingestion/pipeline_batch_ingestion.py`

### Campos recomendados a generar

- `resumen_corto`
- `vibe`
  - ejemplos: `romantico`, `energetico`, `tranquilo`, `familiar`, `premium`, `alternativo`
- `occasion_tags`
  - ejemplos: `pareja`, `friends`, `familia`, `solo`, `afterwork`
- `price_band`
  - ejemplos: `low`, `medium`, `high`
- `indoor_outdoor`
- `time_of_day_fit`
  - ejemplos: `morning`, `afternoon`, `night`
- `romantic_score`
- `family_score`
- `group_score`
- `tourist_score`
- `duration_minutes_estimate`
- `plan_pairings`
  - ejemplos: `cena_antes`, `copas_despues`, `paseo`

### Cómo implementarlo

1. Ampliar el `response_schema` del enriquecimiento Gemini.
2. Ajustar el prompt del pipeline para que devuelva estos campos en JSON.
3. Validar el esquema antes de escribir en Firestore.
4. Guardar los nuevos campos en cada documento de `eventos`.
5. Exponer esos campos en el backend con el schema correspondiente.

### Resultado esperado

Cada evento deja de ser solo un registro descriptivo y pasa a ser una unidad utilizable por el recomendador.

## Fase 2: adaptar el esquema del backend

### Objetivo

Hacer que la API entienda y devuelva los nuevos metadatos del catálogo.

### Archivos a tocar

- `backend/portal-api/app/schemas/event.py`
- `backend/portal-api/app/api/v1/endpoints/events.py`

### Cambios concretos

1. Extender `EventRead` con los nuevos campos semánticos.
2. Dejar de depender de un filtrado puramente en memoria para el planner.
3. Crear una capa de acceso a eventos específica para recuperación inteligente.

### Importante

El endpoint actual de eventos es válido para un MVP, pero para el planner no conviene hacer:

- cargar muchos eventos,
- filtrar después en Python,
- y luego pedir ayuda al modelo.

Lo correcto es construir consultas más selectivas desde el principio.

## Fase 3: preparar la infraestructura en Google Cloud

### Objetivo

Permitir que el backend en Cloud Run invoque Vertex AI correctamente.

### Archivo a tocar

- `terraform/main.tf`

### Cambios necesarios

1. Añadir `roles/aiplatform.user` a la cuenta de servicio `portal-api-sa`.
2. Pasar al servicio de Cloud Run estas variables de entorno:
   - `GOOGLE_CLOUD_PROJECT`
   - `VERTEX_AI_REGION`
   - `GEMINI_MODEL`
3. Mantener el uso de credenciales implícitas mediante la service account de Cloud Run.

### Configuración sugerida

- `VERTEX_AI_REGION = europe-west1`
- `GEMINI_MODEL = gemini-2.5-flash`

### Motivo

La ingesta ya usa Vertex AI, pero el backend del planner también necesita ese acceso.

## Fase 4: crear el servicio de interpretación de intención

### Objetivo

Traducir el mensaje libre del usuario a un JSON estructurado.

### Archivo nuevo recomendado

- `backend/portal-api/app/services/planner_ai.py`

### Entrada

Texto del usuario:

- `quiero un plan romántico para el viernes por la noche`

### Salida estructurada esperada

```json
{
  "city": "Madrid",
  "date_from": "2026-04-24T18:00:00+02:00",
  "date_to": "2026-04-24T23:59:00+02:00",
  "vibes": ["romantico"],
  "occasion_tags": ["pareja"],
  "price_band": null,
  "segments": [],
  "needs_dinner_pairing": true,
  "group_size": 2,
  "indoor_outdoor": null
}
```

### Reglas de implementación

1. Usar Gemini con salida JSON estructurada.
2. Resolver fechas relativas en backend con la zona horaria del producto.
3. Validar el JSON con Pydantic.
4. Definir defaults cuando falten datos.

### Muy importante

La interpretación de intención no debe generar texto de respuesta al usuario. Solo debe devolver estructura utilizable por el backend.

## Fase 5: crear la capa de recuperación de candidatos

### Objetivo

Obtener eventos reales que encajen con la intención detectada.

### Archivo nuevo recomendado

- `backend/portal-api/app/services/event_retrieval.py`

### Lógica recomendada

1. Consultar Firestore por restricciones fuertes:
   - ciudad
   - rango temporal
   - disponibilidad
   - segmento si aplica
2. Recuperar un conjunto controlado de candidatos.
3. Aplicar filtros semánticos en backend:
   - `occasion_tags`
   - `vibe`
   - `price_band`
   - `indoor_outdoor`
4. Calcular una puntuación final por candidato.

### Ejemplo de scoring inicial

- coincidencia de fecha: `+30`
- coincidencia de ciudad: `+20`
- coincidencia de `occasion_tags`: `+20`
- coincidencia de `vibe`: `+15`
- disponibilidad de restaurantes cercanos si el plan pide cena: `+10`
- coincidencia de precio: `+5`

### Qué almacenar en el score

Conviene devolver no solo la puntuación total, sino también los motivos:

- `matched_vibe`
- `matched_time_window`
- `has_restaurants_nearby`
- `good_for_couples`

Eso servirá luego para:

- explicar la recomendación,
- depurar decisiones,
- y medir calidad.

## Fase 6: generar la respuesta final del asistente

### Objetivo

Redactar una respuesta natural y útil, pero basada únicamente en candidatos reales.

### Archivo recomendado

- `backend/portal-api/app/services/planner_ai.py`

### Entrada del modelo en esta fase

- mensaje del usuario,
- intención estructurada,
- top N eventos candidatos,
- reglas de estilo de respuesta.

### Reglas del prompt

El prompt debe exigir:

- no inventar eventos,
- no mencionar nada fuera de los candidatos recibidos,
- reconocer cuando hay poca oferta,
- proponer una o dos alternativas claras,
- resumir por qué encajan con la petición.

### Formato de salida recomendado

La respuesta del modelo no debería ser solo texto libre. Conviene que devuelva también estructura:

```json
{
  "message": "Para un viernes romántico por la noche te recomendaría empezar con ...",
  "recommended_event_ids": ["evt_1", "evt_8", "evt_4"],
  "itinerary": {
    "stops": [
      {
        "type": "event",
        "event_id": "evt_1"
      }
    ],
    "budget": 80
  }
}
```

### Motivo

Así el frontend puede:

- mostrar cards de eventos,
- construir el itinerario,
- y persistir una estructura útil, no solo un párrafo.

## Fase 7: exponer un endpoint específico para el planner

### Objetivo

Dejar de usar el recurso `plans` solo como almacenamiento y convertirlo también en el punto de conversación inteligente.

### Archivos a tocar

- `backend/portal-api/app/api/v1/endpoints/plans.py`
- `backend/portal-api/app/schemas/plan.py`

### Endpoint recomendado

- `POST /plans/{plan_id}/chat`

o, si no existe plan todavía:

- `POST /plans/chat`

### Flujo interno del endpoint

1. Validar usuario autenticado.
2. Cargar plan previo si existe.
3. Añadir el nuevo mensaje del usuario al contexto reciente.
4. Invocar el servicio de interpretación.
5. Recuperar candidatos.
6. Hacer ranking.
7. Generar respuesta final.
8. Persistir mensajes e itinerario.
9. Devolver al frontend:
   - mensaje del asistente
   - eventos recomendados
   - itinerary
   - plan_id

### Recomendación de diseño

No mezclar demasiada lógica dentro del endpoint. La mayor parte debe vivir en servicios reutilizables.

## Fase 8: adaptar el frontend del planner

### Objetivo

Conectar la UI actual con el nuevo flujo del backend.

### Archivo principal

- `frontend/portal/src/pages/AIPlannerPage.tsx`

### Cambios necesarios

1. Sustituir el flujo actual de simple persistencia por una llamada al endpoint inteligente.
2. Añadir estado de carga para la respuesta del asistente.
3. Renderizar:
   - texto del asistente,
   - cards de eventos recomendados,
   - itinerary generado.
4. Guardar `plan_id` devuelto por el backend.
5. Rehidratar conversaciones previas al volver a la página.

### Importante

La UI no debe decidir recomendaciones. Solo debe:

- recoger la petición,
- llamar a la API,
- y pintar lo que devuelve el backend.

## Fase 9: persistencia del plan y trazabilidad

### Objetivo

Guardar no solo mensajes, sino también la decisión tomada por el sistema.

### Cambios recomendados en el modelo de plan

Además de `messages` e `itinerary`, conviene guardar:

- `last_user_intent`
- `recommended_event_ids`
- `retrieval_debug`
- `planner_version`

### Ejemplo

```json
{
  "last_user_intent": {
    "vibes": ["romantico"],
    "occasion_tags": ["pareja"]
  },
  "recommended_event_ids": ["evt_1", "evt_8"],
  "planner_version": "v1"
}
```

### Motivo

Esto ayuda a:

- depurar respuestas malas,
- comparar versiones,
- rehacer recomendaciones sin perder contexto,
- y auditar qué hizo la IA.

## Fase 10: observabilidad, calidad y coste

### Objetivo

Asegurar que la solución es mantenible y no solo funcional.

### Qué registrar

- tiempo total por petición
- tiempo de llamada a Gemini
- número de candidatos recuperados
- número de candidatos mostrados
- tasa de peticiones sin resultados
- eventos más recomendados
- errores de parseo del JSON del modelo

### Qué limitar

- número máximo de candidatos enviados al modelo
- longitud del historial de chat usado como contexto
- reintentos a Vertex AI

### Qué medir después

- clics en eventos recomendados
- guardados en favoritos tras recomendación
- conversión a plan guardado
- consultas que terminan sin interacción posterior

## Fase 11: evolución futura

### Cuándo añadir embeddings

Solo cuando ocurra una de estas situaciones:

- el catálogo sea mucho más grande,
- las queries sean muy ambiguas,
- o los tags y filtros ya no capturen bien la intención.

### Solución recomendada para esa fase

1. Generar embeddings del evento durante la ingesta.
2. Guardarlos en BigQuery.
3. Usar BigQuery Vector Search para recuperar candidatos semánticos.
4. Combinar esos candidatos con filtros estructurados.
5. Mantener el mismo paso final de generación con Gemini.

### Ventaja

No rompe la arquitectura. Solo mejora la fase de recuperación.

## Ejemplo completo del flujo con una petición real

### Entrada del usuario

`quiero un plan romántico para el viernes por la noche`

### Paso 1: intención estructurada

El backend transforma la petición en:

- ocasión: pareja
- vibe: romántico
- ventana temporal: viernes 18:00 a 23:59
- ciudad: ciudad por defecto del usuario o la indicada
- posible necesidad de cena o entorno agradable

### Paso 2: recuperación

Se consultan eventos de esa ventana temporal y ciudad.

### Paso 3: ranking

Se priorizan eventos con:

- mejor encaje para pareja
- horario apropiado
- entorno con restaurantes cercanos
- estilo más íntimo o premium

### Paso 4: generación final

Gemini recibe solo los mejores eventos y redacta algo como:

- propuesta principal
- una alternativa
- breve explicación del porqué

### Paso 5: persistencia

Se guarda:

- el mensaje del usuario
- la respuesta del asistente
- los IDs recomendados
- el itinerario sugerido

## Qué no hacer

- No enviar toda la colección de eventos al modelo.
- No confiar la selección de eventos completamente a Gemini.
- No hacer recomendaciones solo desde frontend.
- No dejar fechas relativas sin resolver.
- No usar texto libre como único resultado interno.
- No depender de un único párrafo sin estructura.

## Orden de implementación recomendado

1. Ampliar el enriquecimiento del catálogo en la ingesta.
2. Extender el schema de eventos en backend.
3. Dar permisos de Vertex AI al backend en Terraform.
4. Crear el servicio de interpretación estructurada.
5. Crear el servicio de recuperación y ranking.
6. Crear el endpoint inteligente del planner.
7. Adaptar el frontend del planner.
8. Añadir trazabilidad y métricas.
9. Evaluar calidad real con usuarios y consultas reales.
10. Solo después valorar embeddings y búsqueda vectorial.

## Archivos del repo que previsiblemente habrá que tocar

- `ingestion/pipeline_batch_ingestion.py`
- `backend/portal-api/app/config.py`
- `backend/portal-api/app/schemas/event.py`
- `backend/portal-api/app/schemas/plan.py`
- `backend/portal-api/app/api/v1/endpoints/events.py`
- `backend/portal-api/app/api/v1/endpoints/plans.py`
- `backend/portal-api/app/services/planner_ai.py`
- `backend/portal-api/app/services/event_retrieval.py`
- `backend/portal-api/requirements.txt`
- `frontend/portal/src/api.ts`
- `frontend/portal/src/pages/AIPlannerPage.tsx`
- `terraform/main.tf`

## Resultado final esperado

Cuando esta solución esté completa, el planner funcionará así:

- el usuario escribe en lenguaje natural,
- el backend entiende la intención,
- recupera eventos reales del catálogo,
- selecciona los mejores,
- genera una respuesta convincente y explicable,
- y guarda todo como un plan reutilizable.

Ese es el flujo correcto para una solución de IA sólida en esta aplicación y sobre Google Cloud: usar Gemini como capa de inteligencia, pero dejar la decisión sobre eventos reales en manos del backend y del catálogo enriquecido.
