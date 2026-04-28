import json
import logging
import os
import requests
from datetime import datetime, timedelta, timezone
from google.cloud import secretmanager, storage, firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

logging.basicConfig(
    level = logging.INFO, 
    format = "%(asctime)s %(levelname)s %(message)s"
)

id_proyecto = os.getenv("ID_PROYECTO")
id_secreto_apikey_ticketmaster = os.getenv("ID_SECRETO_APIKEY_TICKETMASTER")
bucket_gcs = os.getenv("BUCKET_GCS")
dias_obtener_eventos = int(os.getenv("DIAS_OBTENER_EVENTOS"))
codigo_pais = os.getenv("CODIGO_PAIS")
longitud_respuesta_api_ticketmaster = int(os.getenv("LONGITUD_RESPUESTA_API_TICKETMASTER"))
url_api_ticketmaster = os.getenv("URL_API_TICKETMASTER")
coleccion_firestore_eventos = os.getenv("COLECCION_FIRESTORE_EVENTOS")

cliente_secrets = secretmanager.SecretManagerServiceClient()
cliente_storage = storage.Client(project = id_proyecto)
cliente_firestore = firestore.Client(project = id_proyecto)

def obtener_secreto(id_proyecto: str, id_secreto: str, version: str = "latest") -> str:
    ubicacion = f"projects/{id_proyecto}/secrets/{id_secreto}/versions/{version}"
    respuesta = cliente_secrets.access_secret_version(request={"name": ubicacion})
    return respuesta.payload.data.decode("UTF-8")

def obtener_eventos_ticketmaster(api_key_ticketmaster: str) -> list[dict]:
    timestamp_actual = datetime.now(timezone.utc)
    fecha_inicio = timestamp_actual.strftime("%Y-%m-%dT%H:%M:%SZ")
    fecha_fin = (timestamp_actual + timedelta(days = dias_obtener_eventos)).strftime("%Y-%m-%dT%H:%M:%SZ")

    logging.info("[Ticketmaster] Comenzando la ingestión")

    todos_los_eventos = []
    pagina = 0

    while True:
        parametros_peticion = {
            "apikey": api_key_ticketmaster,
            "countryCode": codigo_pais,
            "startDateTime": fecha_inicio,
            "endDateTime": fecha_fin,
            "size": longitud_respuesta_api_ticketmaster,
            "page": pagina
        }

        respuesta_api_ticketmaster = requests.get(
            url = url_api_ticketmaster,
            params = parametros_peticion,
            timeout = 60
        )
        respuesta_api_ticketmaster.raise_for_status()
        datos_eventos = respuesta_api_ticketmaster.json()

        embedded = datos_eventos.get("_embedded")
        if not embedded:
            logging.info("[Ticketmaster] No quedan más páginas con eventos")
            break

        eventos_pagina = embedded.get("events", [])
        todos_los_eventos.extend(eventos_pagina)

        info_pagina = datos_eventos.get("page", {})
        total_paginas = info_pagina.get("totalPages", 1)
        logging.info(f"[Ticketmaster] Página {pagina + 1}/{total_paginas} — {len(todos_los_eventos)} eventos acumulados")

        pagina += 1
        if pagina >= total_paginas: 
            break

    logging.info(f"[Ticketmaster] Extracción completada — total eventos: {len(todos_los_eventos)}")
    return todos_los_eventos

def guardar_en_bucket(nombre_bucket: str, ruta_archivo: str, contenido: str) -> None:
    bucket = cliente_storage.bucket(nombre_bucket)
    blob = bucket.blob(ruta_archivo) 
    blob.upload_from_string(
        contenido,
        content_type = "application/json"
    )
    logging.info(f"[GCS] JSON subido a gs://{nombre_bucket}/{ruta_archivo}")

def sacar_mejor_imagen(imagenes: list[dict], ratio: str = "16_9", min_ancho: int = 0) -> str | None:
    imagenes_candidatas = [
        img for img in imagenes if img.get("ratio") == ratio and img.get("width", 0) >= min_ancho
    ]
    if not imagenes_candidatas:
        imagenes_candidatas = imagenes
    return max(imagenes_candidatas, key = lambda img: img.get("width", 0), default = {}).get("url")

def transformar_evento(evento_raw: dict) -> dict | None:
    if evento_raw.get("test") == True: 
        return None

    clasificacion = (evento_raw.get("classifications") or [{}])[0]
    venue = ((evento_raw.get("_embedded") or {}).get("venues") or [{}])[0]
    atraccion = ((evento_raw.get("_embedded") or {}).get("attractions") or [{}])[0]
    inicio = (evento_raw.get("dates") or {}).get("start") or {}
    venta = ((evento_raw.get("sales") or {}).get("public")) or {}
    ubicacion = venue.get("location") or {}

    evento_normalizado = {
        "id_origen": evento_raw.get("id"),
        "fuente": "ticketmaster",
        "nombre": evento_raw.get("name"),
        "url": evento_raw.get("url"),
        "fecha": inicio.get("localDate"),
        "hora": inicio.get("localTime"),
        "fecha_utc": (
            datetime.fromisoformat(inicio["dateTime"].replace("Z", "+00:00")).isoformat()
            if inicio.get("dateTime") else None
        ),
        "estado": (evento_raw.get("dates") or {}).get("status", {}).get("code"),
        "venta_inicio": venta.get("startDateTime"),
        "venta_fin": venta.get("endDateTime"),
        "segmento": clasificacion.get("segment", {}).get("name"),
        "genero": clasificacion.get("genre", {}).get("name"),
        "subgenero": clasificacion.get("subGenre", {}).get("name"),
        "recinto_id": venue.get("id"),
        "recinto_nombre": venue.get("name"),
        "ciudad": (venue.get("city") or {}).get("name"),
        "direccion": (venue.get("address") or {}).get("line1"),
        "codigo_postal": venue.get("postalCode"),
        "latitud": float(ubicacion["latitude"]) if ubicacion.get("latitude") else None,
        "longitud": float(ubicacion["longitude"]) if ubicacion.get("longitude") else None,
        "artista_id": atraccion.get("id"),
        "artista_nombre": atraccion.get("name"),
        "artista_imagen": sacar_mejor_imagen(atraccion.get("images") or [], ratio="3_2", min_ancho=300),
        "imagen_evento": sacar_mejor_imagen(evento_raw.get("images") or [], ratio="16_9", min_ancho=1000),
        "promotor": (evento_raw.get("promoter") or {}).get("name"),
        "descripcion": evento_raw.get("description"),
    }

    return evento_normalizado

def guardar_en_firestore(eventos: list[dict]) -> dict:
    if not eventos:
        logging.info("[Firestore] No hay eventos que escribir")
        return {
            "creados": 0,
            "estado_actualizado": 0,
            "sin_cambios": 0
        }
    
    coleccion = cliente_firestore.collection(coleccion_firestore_eventos)

    refs = [
        coleccion.document(evento["id_origen"]) for evento in eventos
    ]

    snapshots = cliente_firestore.get_all(
        refs,
        field_paths = ["estado"]
    )

    existentes = {
        snap.id: (snap.to_dict() or {}) for snap in snapshots if snap.exists
    }

    logging.info(f"[Firestore] {len(existentes)}/{len(eventos)} eventos ya existen en la colección")

    bulk_writer = cliente_firestore.bulk_writer()
    estadisticas = {"creados": 0, "estado_actualizado": 0, "sin_cambios": 0}

    for evento in eventos:
        id_documento = evento["id_origen"]
        ref = coleccion.document(id_documento)

        if id_documento not in existentes:
            evento_a_escribir = {
                **evento,
                "evento_enriquecido": False,
                "embedding_creado": False,
                "primera_ingestion": SERVER_TIMESTAMP,
                "ultima_ingestion": SERVER_TIMESTAMP
            }
            bulk_writer.set(
                ref,
                evento_a_escribir
            )
            estadisticas["creados"] += 1

        elif existentes[id_documento].get("estado") != evento["estado"]:
            bulk_writer.update(
                ref,
                {
                    "estado": evento["estado"], 
                    "venta_inicio": evento.get("venta_inicio"),
                    "venta_fin": evento.get("venta_fin"),
                    "ultima_ingestion": SERVER_TIMESTAMP
                }
            )
            estadisticas["estado_actualizado"] += 1

        else:
            bulk_writer.update(
                ref,
                {
                    "ultima_ingestion": SERVER_TIMESTAMP
                }
            )
            estadisticas["sin_cambios"] += 1

    bulk_writer.close()

    logging.info(
        f"[Firestore] Resultado — creados: {estadisticas['creados']}, "
        f"estado_actualizado: {estadisticas['estado_actualizado']}, "
        f"sin_cambios: {estadisticas['sin_cambios']}"
    )
    return estadisticas

def main() -> None:
    timestamp_ejecucion = datetime.now(timezone.utc)
    logging.info(f"[JOB: Ingestión] Comienza el Job de ingestión: {timestamp_ejecucion}")

    api_key_ticketmaster = obtener_secreto(id_proyecto, id_secreto_apikey_ticketmaster)

    eventos_raw = obtener_eventos_ticketmaster(api_key_ticketmaster)
    if not eventos_raw:
        logging.warning("[JOB: Ingestión] No se obtuvo ninvun evento de Ticketmaseter")
        return
    
    guardar_en_bucket(
        nombre_bucket = bucket_gcs,
        ruta_archivo = f"eventos/ticketmaster_{timestamp_ejecucion.strftime('%Y%m%dT%H%M%S')}.json",
        contenido = json.dumps(
            eventos_raw,
            ensure_ascii = False
        )
    )

    eventos_normalizados = []
    for evento_raw in eventos_raw:
        try: 
            evento = transformar_evento(evento_raw)
            if evento is not None:
                eventos_normalizados.append(evento)
        except Exception as e:
            logging.error(f"[JOB: Ingestión] Error transformando evento: {e}", exc_info = True)

    logging.info(f"Transformación completada — {len(eventos_normalizados)} eventos válidos (de {len(eventos_raw)} brutos)")

    estadisticas = guardar_en_firestore(eventos_normalizados)

    logging.info(f"[JOB: Ingestión] Fin de la ingestión con estadisticas: {estadisticas}")

if __name__ == "__main__":
    main()
