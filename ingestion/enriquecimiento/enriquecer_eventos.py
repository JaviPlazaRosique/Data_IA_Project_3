import json
import logging
import os
import requests
import re
from datetime import datetime, timedelta, timezone
from google.cloud import firestore, secretmanager
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(
    level = logging.INFO, 
    format = "%(asctime)s %(levelname)s %(message)s"
)

id_proyecto = os.getenv("ID_PROYECTO")
region = os.getenv("REGION")
id_secreto_apikey_places = os.getenv("ID_SECRETO_APIKEY_PLACES")
coleccion_firestore_eventos = os.getenv("COLECCION_FIRESTORE_EVENTOS")
coleccion_firestore_recintos = os.getenv("COLECCION_FIRESTORE_RECINTOS")
coleccion_firestore_cache_gemini = os.getenv("COLECCION_FIRESTORE_CACHE_GEMINI")
top_recintos_enriquecimiento = int(os.getenv("TOP_RECINTOS_ENRIQUECIMIENTO"))
radio_restaurantes_metros = int(os.getenv("RADIO_RESTAURANTES_METROS"))
radio_alojamientos_metros = int(os.getenv("RADIO_ALOJAMIENTOS_METROS"))
dias_borrado_recintos = int(os.getenv("DIAS_BORRADO_RECINTOS"))
dias_max_prevision_tiempo = int(os.getenv("DIAS_MAX_PREVISION_TIEMPO"))
modelo_gemini = os.getenv("MODELO_GEMINI")
url_google_places = os.getenv("URL_GOOGLE_PLACES")
url_open_meteo = os.getenv("URL_OPEN_METEO")

cliente_secrets = secretmanager.SecretManagerServiceClient()
cliente_firestore = firestore.Client(project = id_proyecto)

FIELD_MASK_PLACES = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.location,"
    "places.rating,"
    "places.userRatingCount,"
    "places.priceLevel,"
    "places.types"
)

schema_salida_enriquecimiento_gemini = {
    "type": "object",
    "properties": {
        "minutos_antelacion": {
            "type": "integer",
            "description": "Minutos de antelación recomendados antes del inicio del evento"
        },
        "motivo": {
            "type": "string",
            "description": "Razón principal de la recomendación en una frase corta"
        },
        "vibra": {
            "type": "string",
            "enum": ["romantico", "energetico", "tranquilo", "familiar", "premium", "alternativo"],
            "description": "Vibra principal del evento"
        },
        "etiquetas_ocasion": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["pareja", "amigos", "familia", "solo", "afterwork"],
            },
            "description": "Etiquetas de ocasión recomendadas"
        },
        "banda_precio": {
            "type": "string",
            "enum": ["bajo", "medio", "alto"],
            "description": "Banda de precio inferida"
        },
        "interior_exterior": {
            "type": "string",
            "enum": ["interior", "exterior", "mixto", "desconocido"],
            "description": "Tipo de espacio del evento"
        },
        "franja_horaria": {
            "type": "string",
            "enum": ["mañana", "tarde", "noche"],
            "description": "Franja horaria más adecuada"
        },
        "puntuacion_romantica": {
            "type": "integer",
            "description": "Puntuación para planes románticos entre 0 y 100"
        },
        "puntuacion_familiar": {
            "type": "integer",
            "description": "Puntuación para planes familiares entre 0 y 100"
        },
        "puntuacion_grupo": {
            "type": "integer",
            "description": "Puntuación para grupos entre 0 y 100"
        },
        "puntuacion_turista": {
            "type": "integer",
            "description": "Puntuación para turistas entre 0 y 100"
        },
        "duracion_minutos_estimada": {
            "type": "integer",
            "description": "Duración estimada del evento en minutos"
        },
        "maridajes_plan": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Etiquetas cortas de maridaje del plan en snake_case"
        },
        "categoria": {
            "type": "string",
            "enum": ["Música", "Arte y Teatro", "Deportes", "Familia y otros"],
            "description": "Categoría principal del evento"
        },
        "subcategoria": {
            "type": "string",
            "enum": [
                "Dance/Electrónica",
                "Flamenco/Rumba",
                "Hard Rock/Metal",
                "Hip-Hop/R&B",
                "Indie/Alternativo",
                "Jazz/Blues",
                "Latin",
                "Música Clásica",
                "Pop/Rock",
                "Festival",
                "Ballet/Danza",
                "Circo",
                "Comedia",
                "Magia",
                "Musical",
                "Ópera",
                "Baloncesto",
                "Ciclismo",
                "Fútbol",
                "Motor",
                "Tenis",
                "Actividades en familia",
                "Espectáculos de Magia",
                "Parques temáticos",
                "Teatro infantil",
                "Visitas Guiadas/Exposiciones"
            ],
            "description": "Subcategoría del evento compatible con la categoría"
        },
    },
    "required": [
        "minutos_antelacion",
        "motivo",
        "vibra",
        "etiquetas_ocasion",
        "banda_precio",
        "interior_exterior",
        "franja_horaria",
        "puntuacion_romantica",
        "puntuacion_familiar",
        "puntuacion_grupo",
        "puntuacion_turista",
        "duracion_minutos_estimada",
        "maridajes_plan",
        "categoria",
        "subcategoria",
    ],
}

SUBCATEGORIAS_POR_CATEGORIA = {
    "Música": [
        "Dance/Electrónica", 
        "Flamenco/Rumba", 
        "Hard Rock/Metal", 
        "Hip-Hop/R&B",
        "Indie/Alternativo", 
        "Jazz/Blues", 
        "Latin", 
        "Música Clásica", 
        "Pop/Rock", 
        "Festival",
    ],
    "Arte y Teatro": [
        "Ballet/Danza", 
        "Circo", 
        "Comedia", 
        "Magia", 
        "Musical", 
        "Ópera"
    ],
    "Deportes": [
        "Baloncesto", 
        "Ciclismo", 
        "Fútbol", 
        "Motor", 
        "Tenis"
    ],
    "Familia y otros": [
        "Actividades en familia", 
        "Circo", 
        "Espectáculos de Magia", 
        "Parques temáticos",
        "Teatro infantil", 
        "Visitas Guiadas/Exposiciones",
    ],
}

WMO_DESCRIPCIONES = {
    0:  "Despejado",
    1:  "Principalmente despejado",
    2:  "Parcialmente nublado",
    3:  "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    56: "Llovizna helada ligera",
    57: "Llovizna helada densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    66: "Lluvia helada ligera",
    67: "Lluvia helada intensa",
    71: "Nevada ligera",
    73: "Nevada moderada",
    75: "Nevada intensa",
    77: "Granos de nieve",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve intensos",
    95: "Tormenta",
    96: "Tormenta con granizo ligero",
    99: "Tormenta con granizo intenso",
}

def construir_prompt_enriquecimiento_gemini(evento: dict) -> str:
    subcategorias_formateadas = "\n".join(
        f"- {categoria}: {', '.join(subcategorias)}"
        for categoria, subcategorias in SUBCATEGORIAS_POR_CATEGORIA.items()
    )

    return f"""Eres un clasificador semántico de eventos en España.
Debes devolver solo JSON válido que cumpla exactamente el schema indicado.
No inventes información fuera de lo que permitan inferir los datos.
Si falta contexto, elige la opción más prudente y coherente.

Usa únicamente estos 7 campos del evento para inferir la respuesta:
- nombre: {evento.get("nombre")}
- descripcion: {evento.get("descripcion")}
- segmento: {evento.get("segmento")}
- genero: {evento.get("genero")}
- subgenero: {evento.get("subgenero")}
- recinto_nombre: {evento.get("recinto_nombre")}
- hora: {evento.get("hora")}

Reglas de salida:
- minutos_antelacion: entero razonable entre 15 y 120.
- motivo: una frase corta en español.
- vibra: elige exactamente una opción entre romantico, energetico, tranquilo, familiar, premium, alternativo.
- etiquetas_ocasion: devuelve de 1 a 3 etiquetas entre pareja, amigos, familia, solo, afterwork.
- banda_precio: infiere la banda de precio (bajo, medio, alto) a partir del tipo de evento, género y recinto.
- interior_exterior: elige interior, exterior, mixto o desconocido.
- franja_horaria: mañana para eventos de mañana, tarde para tarde, noche para noche.
- puntuacion_romantica, puntuacion_familiar, puntuacion_grupo y puntuacion_turista: enteros entre 0 y 100.
- duracion_minutos_estimada: duración típica estimada en minutos.
- maridajes_plan: devuelve de 1 a 3 etiquetas cortas en snake_case; prioriza valores como cena_antes, copas_despues, paseo cuando encajen.
- categoria: elige exactamente una entre Música, Arte y Teatro, Deportes, Familia y otros.
- subcategoria: elige exactamente una subcategoría compatible con la categoria seleccionada.

Mapa obligatorio de categorías y subcategorías:
{subcategorias_formateadas}
"""

def obtener_secreto(id_proyecto: str, id_secreto: str, version: str = "latest") -> str:
    ubicacion = f"projects/{id_proyecto}/secrets/{id_secreto}/versions/{version}"
    respuesta = cliente_secrets.access_secret_version(request={"name": ubicacion})
    return respuesta.payload.data.decode("UTF-8")

def sanitizar_id_firestore(texto: str, max_len: int = 200) -> str:
    sanitizado = re.sub(r"[/\s]+", "_", texto.strip())
    sanitizado = re.sub(r"[^\w\-_.áéíóúÁÉÍÓÚñÑüÜ]", "", sanitizado)
    if sanitizado.startswith("__"):
        sanitizado = "x" + sanitizado
    return sanitizado[:max_len] or "sin_nombre"

def obtener_eventos_pendientes() -> list[dict]:
    query = (
        cliente_firestore
        .collection(coleccion_firestore_eventos)
        .where(filter=firestore.FieldFilter("evento_enriquecido", "==", False))
    )
    eventos = []
    for doc in query.stream():
        datos = doc.to_dict()
        datos["doc_id"] = doc.id
        eventos.append(datos)

    logging.info(f"[Firestore] Eventos pendientes de enriquecer: {len(eventos)}")
    return eventos

@retry(
    stop = stop_after_attempt(5),
    wait = wait_exponential(multiplier = 1, min = 2, max = 30),
    retry = retry_if_exception_type(requests.exceptions.RequestException),
    reraise = True
)
def peticion_google_places(api_key_google_places: str, latitud: float, longitud: float, tipos_incluidos: list[str], radio_metros: int, top: int) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key_google_places,
        "X-Goog-FieldMask": FIELD_MASK_PLACES,
    }
    body = {
        "includedTypes": tipos_incluidos,
        "maxResultCount": top,
        "rankPreference": "DISTANCE",
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitud, "longitude": longitud},
                "radius": radio_metros,
            }
        },
    }
    respuesta = requests.post(url_google_places, headers=headers, json=body, timeout=30)
    respuesta.raise_for_status()
    return respuesta.json().get("places", [])

def obtener_recintos(evento: dict, api_key_google_places: str) -> dict:
    if evento.get("latitud") is None or evento.get("longitud") is None:
        logging.warning(f"Evento {evento['id_origen']} sin coordenadas, no se enriquece con recintos")
        return {
            "restaurantes": [], 
            "alojamientos": [], 
            "sin_coordenadas": True
        }
    
    recinto_id = evento.get("recinto_id")
    if not recinto_id:
        logging.warning(f"Evento {evento['id_origen']}, sin enriquecimiento de recintos por no tener recinto_id")
        return{
            "restaurantes": [], 
            "alojamientos": [], 
            "sin_coordenadas": True
        }
    
    ref_recinto = cliente_firestore.collection(coleccion_firestore_recintos).document(recinto_id)

    snapshot = ref_recinto.get()
    if snapshot.exists:
        datos = snapshot.to_dict() or {}
        logging.debug(f"[Places] Creación de recintos (restaurantes y alojamientos) para: {recinto_id}")
        return {
            "restaurantes": datos.get("restaurantes", []),
            "alojamientos": datos.get("alojamientos", []),
        }
    
    logging.info(f"[Places] {recinto_id} aún sin recintos, consulatando a Google Places")

    restaurantes = peticion_google_places(
        api_key_google_places = api_key_google_places,
        latitud = evento["latitud"],
        longitud = evento["longitud"],
        tipos_incluidos = ["restaurant"],
        radio_metros = radio_restaurantes_metros,
        top = top_recintos_enriquecimiento
    )

    alojamientos = peticion_google_places(
        api_key_google_places = api_key_google_places,
        latitud = evento["latitud"],
        longitud = evento["longitud"],
        tipos_incluidos = ["lodging"],
        radio_metros = radio_alojamientos_metros,
        top = top_recintos_enriquecimiento
    )

    fecha_expiracion = datetime.now(timezone.utc) + timedelta(days = dias_borrado_recintos)

    ref_recinto.set({
        "recinto_id": recinto_id,
        "nombre": evento.get("recinto_nombre"),
        "ciudad": evento.get("ciudad"),
        "direccion": evento.get("direccion"),
        "codigo_postal": evento.get("codigo_postal"),
        "latitud": evento["latitud"],
        "longitud": evento["longitud"],
        "restaurantes": restaurantes,
        "alojamientos": alojamientos,
        "fecha_creacion": SERVER_TIMESTAMP,
        "fecha_expiracion": fecha_expiracion
    })

    logging.info(f"[Places] Documento con id {recinto_id} creado correctamente")

    return {
        "restaurantes": restaurantes,
        "alojamientos": alojamientos,
    }

class EnriquecedorGemini:
    CAMPOS_ENRIQUECIDOS = {
        "antelacion_recomendada", 
        "vibra", 
        "etiquetas_ocasion",
        "banda_precio",
        "interior_exterior", 
        "franja_horaria", 
        "puntuacion_romantica",
        "puntuacion_familiar", 
        "puntuacion_grupo", 
        "puntuacion_turista",
        "duracion_minutos_estimada", 
        "maridajes_plan", 
        "categoria", 
        "subcategoria",
    }

    def __init__(self, id_proyecto: str, region: str, coleccion_firestore_cache_gemini: str):
        vertexai.init(project = id_proyecto, location=region)
        self.modelo = GenerativeModel(
            model_name = modelo_gemini,
            generation_config = GenerationConfig(
                response_mime_type = "application/json",
                response_schema = schema_salida_enriquecimiento_gemini,
                temperature = 0.2,
            ),
        )
        self.coleccion_firestore_cache_gemini = coleccion_firestore_cache_gemini
        logging.info(
            f"[Gemini] Inicializado con el modelo {modelo_gemini}")

    def id_documento_cache_gemini(self, doc_id: str) -> str:
        return doc_id

    def leer_cache_gemini(self, doc_id: str) -> dict | None:
        ref = cliente_firestore.collection(self.coleccion_firestore_cache_gemini).document(self.id_documento_cache_gemini(doc_id))
        snap = ref.get()
        if not snap.exists:
            return None
        datos = snap.to_dict() or {}
        if not self.CAMPOS_ENRIQUECIDOS.issubset(datos.keys()):
            return None
        return datos

    def guardar_cache_gemini(self, doc_id: str, datos_enriquecimiento: dict) -> None:
        ref = cliente_firestore.collection(self.coleccion_firestore_cache_gemini).document(self.id_documento_cache_gemini(doc_id))
        ref.set({
            **datos_enriquecimiento,
            "modelo": modelo_gemini,
            "fecha_creacion": SERVER_TIMESTAMP,
        })

    @retry(
        stop = stop_after_attempt(5),
        wait = wait_exponential(multiplier = 1, min = 2, max = 30),
        reraise = True
    )
    def llamada_gemini(self, prompt: str) -> dict:
        respuesta = self.modelo.generate_content(prompt)
        return json.loads(respuesta.text)

    def enriquecer(self, evento: dict) -> dict:
        doc_id = evento["doc_id"]

        cache = self.leer_cache_gemini(doc_id)
        if cache is not None:
            logging.info(f"[Gemini] Existe el cache con id {doc_id}")
            return {campo: cache[campo] for campo in self.CAMPOS_ENRIQUECIDOS if campo in cache}

        prompt = construir_prompt_enriquecimiento_gemini(evento)
        respuesta_cruda = self.llamada_gemini(prompt)

        datos_enriquecimiento = {
            "antelacion_recomendada": {
                "minutos_antelacion": respuesta_cruda.get("minutos_antelacion"),
                "motivo": respuesta_cruda.get("motivo"),
            },
            "vibra": respuesta_cruda.get("vibra"),
            "etiquetas_ocasion": respuesta_cruda.get("etiquetas_ocasion", []),
            "banda_precio": respuesta_cruda.get("banda_precio"),
            "interior_exterior": respuesta_cruda.get("interior_exterior"),
            "franja_horaria": respuesta_cruda.get("franja_horaria"),
            "puntuacion_romantica": respuesta_cruda.get("puntuacion_romantica"),
            "puntuacion_familiar": respuesta_cruda.get("puntuacion_familiar"),
            "puntuacion_grupo": respuesta_cruda.get("puntuacion_grupo"),
            "puntuacion_turista": respuesta_cruda.get("puntuacion_turista"),
            "duracion_minutos_estimada": respuesta_cruda.get("duracion_minutos_estimada"),
            "maridajes_plan": respuesta_cruda.get("maridajes_plan", []),
            "categoria": respuesta_cruda.get("categoria"),
            "subcategoria": respuesta_cruda.get("subcategoria"),
        }

        self.guardar_cache_gemini(doc_id, datos_enriquecimiento)
        logging.info(f"[Gemini] Documento generado con id {doc_id}")
        return datos_enriquecimiento
    
@retry(
    stop = stop_after_attempt(5),
    wait = wait_exponential(multiplier = 1, min = 2, max = 30), 
    retry = retry_if_exception_type(requests.exceptions.RequestException),
    reraise = True
)
def peticion_open_meteo(latitud: float, longitud: float, fecha: str) -> dict:
    params = {
        "latitude":   round(latitud, 4),
        "longitude":  round(longitud, 4),
        "daily":      "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max",
        "timezone":   "Europe/Madrid",
        "start_date": fecha,
        "end_date":   fecha,
    }
    respuesta = requests.get(url_open_meteo, params=params, timeout=30)
    respuesta.raise_for_status()
    return respuesta.json()

def obtener_tiempo_evento(evento: dict) -> dict | None:
    latitud = evento.get("latitud")
    longitud = evento.get("longitud")
    fecha = evento.get("fecha")

    if latitud is None or longitud is None or not fecha:
        logging.warning(f"[Tiempo] Evento {evento['doc_id']} sin coords o fecha, sin tiempo")
        return None

    try:
        fecha_evento = datetime.strptime(fecha, "%Y-%m-%d").date()
        dias_hasta_evento = (fecha_evento - datetime.now(timezone.utc).date()).days
        if dias_hasta_evento < 0 or dias_hasta_evento > dias_max_prevision_tiempo:
            logging.info(
                f"[Tiempo] Evento {evento['doc_id']} fuera de ventana de previsión "
                f"({dias_hasta_evento} días), sin tiempo"
            )
            return None
    except ValueError:
        logging.warning(f"[Tiempo] Fecha inválida en {evento['doc_id']}: {fecha}")
        return None

    payload = peticion_open_meteo(latitud, longitud, fecha)
    daily = payload.get("daily", {}) or {}
    if not daily.get("time"):
        logging.warning(f"[Tiempo] Open-Meteo sin datos para evento {evento['doc_id']}")
        return None

    codigo_wmo = daily.get("weather_code", [None])[0]
    tiempo = {
        "temp_max":         daily.get("temperature_2m_max",    [None])[0],
        "temp_min":         daily.get("temperature_2m_min",    [None])[0],
        "precipitacion_mm": daily.get("precipitation_sum",     [None])[0],
        "codigo_wmo":       codigo_wmo,
        "descripcion":      WMO_DESCRIPCIONES.get(codigo_wmo),
        "viento_max_kmh":   daily.get("wind_speed_10m_max",    [None])[0],
    }

    logging.info(
        f"[Tiempo] Consultado — {evento['doc_id']} | {fecha} | "
        f"{tiempo['descripcion']} | {tiempo['temp_min']}–{tiempo['temp_max']}°C"
    )
    return tiempo

def actualizar_evento_enriquecido(
    doc_id: str,
    recintos: dict | None,
    tiempo: dict | None,
    gemini: dict | None,
    recinto_id: str | None,
) -> None:
    ref = cliente_firestore.collection(coleccion_firestore_eventos).document(doc_id)
    actualizacion = {
        "evento_enriquecido": True,
        "fecha_enriquecido": SERVER_TIMESTAMP,
    }
    if recintos is not None:
        actualizacion["lugares_cercanos"] = recintos
        if recinto_id:
            actualizacion["recinto_id"] = recinto_id
    if tiempo is not None:
        actualizacion["tiempo"] = tiempo
    if gemini is not None:
        actualizacion.update(gemini)

    ref.update(actualizacion)
    logging.info(f"[Firestore] Evento {doc_id} actualizado como enriquecido")

def main():
    logging.info("[JOB: Enriquecimiento] Inicio del job de enriquecimiento")

    api_key_google_places = obtener_secreto(id_proyecto, id_secreto_apikey_places)
    enriquecedor_gemini = EnriquecedorGemini(
        id_proyecto = id_proyecto,
        region = region,
        coleccion_firestore_cache_gemini = coleccion_firestore_cache_gemini,
    )

    eventos = obtener_eventos_pendientes()
    if not eventos:
        logging.info("[JOB: Enriquecimiento] No hay eventos pendientes de enriquecimiento")
        return

    logging.info(f"[JOB: Enriquecimiento] Procesando {len(eventos)} eventos")
    ok = 0
    ko = 0

    for evento in eventos:
        doc_id = evento["doc_id"]
        try:
            recintos_raw = obtener_recintos(evento, api_key_google_places)
            recintos = None if recintos_raw.get("sin_coordenadas") else recintos_raw
            tiempo = obtener_tiempo_evento(evento)
            gemini = enriquecedor_gemini.enriquecer(evento)
            actualizar_evento_enriquecido(
                doc_id = doc_id,
                recintos = recintos,
                tiempo = tiempo,
                gemini = gemini,
                recinto_id = evento.get("recinto_id"),
            )
            ok += 1
        except Exception as e:
            logging.error(f"[JOB: Enriquecimiento] Error enriqueciendo evento {doc_id}: {e}")
            ko += 1

    logging.info(f"[JOB: Enriquecimiento] Fin del job — OK: {ok} | KO: {ko}")

if __name__ == "__main__":
    main()