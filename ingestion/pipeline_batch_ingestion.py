from datetime import datetime, timedelta, timezone
import math
import random
import time
import requests
import argparse
import json
import logging

from google.cloud import secretmanager, firestore
import google.generativeai as genai
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import WriteToText
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition, ReadFromBigQuery


def reintentos_peticiones(fn, max_intentos: int = 4, espera_base: float = 1.0):
    for intento in range(max_intentos):
        try:
            return fn()
        except Exception as e:
            es_rate_limit = (
                isinstance(e, requests.exceptions.HTTPError)
                and e.response is not None
                and e.response.status_code == 429
            ) or any(t in str(e).lower() for t in ("429", "quota", "resource exhausted"))

            if es_rate_limit and intento < max_intentos - 1:
                espera = espera_base * (2 ** intento) + random.uniform(0, 1)
                logging.warning("[Reintentos] Cuota excedida — esperando %.1fs (intento %d/%d)", espera, intento + 1, max_intentos)
                time.sleep(espera)
            else:
                raise


def obtener_secreto(id_proyecto: str, id_secreto: str, version: str = "latest") -> str:
    logging.info(f"[SecretManager] Obteniendo secreto con id = {id_secreto}")
    cliente = secretmanager.SecretManagerServiceClient()
    ubicacion_secreto = f"projects/{id_proyecto}/secrets/{id_secreto}/versions/{version}"
    respuesta = cliente.access_secret_version(request={"name": ubicacion_secreto})
    logging.info("[SecretManager] Secreto '%s' obtenido correctamente", id_secreto)
    logging.info(f"[SecretManager] Secreto con id = {id_secreto} obtenido correctamente")
    return respuesta.payload.data.decode("UTF-8")


def obtener_eventos_ticketmaster(api_key: str) -> list[dict]:
    url_base_ticketmaster = "https://app.ticketmaster.com/discovery/v2/events.json"
    codigo_pais = "ES"
    dias_ventana = 12
    longitud_pagina = 200
    ahora = datetime.now(timezone.utc)
    fecha_inicio = ahora.strftime("%Y-%m-%dT%H:%M:%SZ")
    fecha_fin = (ahora + timedelta(days=dias_ventana)).strftime("%Y-%m-%dT%H:%M:%SZ")

    logging.info("[Ticketmaster] Comenzando extracción de los datos")

    todos_los_eventos = []
    pagina = 0

    while True:
        params = {
            "apikey": api_key,
            "countryCode": codigo_pais,
            "startDateTime": fecha_inicio,
            "endDateTime": fecha_fin,
            "size": longitud_pagina,
            "page": pagina,
        }

        respuesta = reintentos_peticiones(
            lambda p=params: requests.get(url_base_ticketmaster, params=p, timeout=30)
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

        embedded = datos.get("_embedded")
        if not embedded:
            logging.info("[Ticketmaster] No quedan más páginas con eventos")
            break

        eventos_pagina = embedded.get("events", [])
        todos_los_eventos.extend(eventos_pagina)

        info_pagina = datos.get("page", {})
        total_paginas = info_pagina.get("totalPages", 1)
        logging.info(f"[Ticketmaster] Página {pagina + 1}/{total_paginas} — {len(todos_los_eventos)} eventos acumulados")

        pagina += 1
        if pagina >= total_paginas:
            break

    logging.info(f"[Ticketmaster] Extracción completada — total eventos: {len(todos_los_eventos)}")
    return todos_los_eventos


def sacar_mejor_imagen(imagenes: list[dict], ratio: str = "16_9", min_ancho: int = 0) -> str | None:
    candidatas = [img for img in imagenes if img.get("ratio") == ratio and img.get("width", 0) >= min_ancho]
    if not candidatas:
        candidatas = imagenes
    return max(candidatas, key=lambda img: img.get("width", 0), default={}).get("url")


def transformar_evento(evento_raw: dict) -> dict:
    clasificacion = (evento_raw.get("classifications") or [{}])[0]
    venue         = ((evento_raw.get("_embedded") or {}).get("venues") or [{}])[0]
    atraccion     = ((evento_raw.get("_embedded") or {}).get("attractions") or [{}])[0]
    inicio        = (evento_raw.get("dates") or {}).get("start") or {}
    venta         = ((evento_raw.get("sales") or {}).get("public")) or {}
    ubicacion     = venue.get("location") or {}

    evento = {
        "id":               evento_raw.get("id"),
        "nombre":           evento_raw.get("name"),
        "url":              evento_raw.get("url"),
        "es_test":          evento_raw.get("test", False),
        "fecha":            inicio.get("localDate"),
        "hora":             inicio.get("localTime"),
        "fecha_utc":        datetime.fromisoformat(inicio["dateTime"].replace("Z", "+00:00")) if inicio.get("dateTime") else None,
        "estado":           (evento_raw.get("dates") or {}).get("status", {}).get("code"),
        "venta_inicio":     venta.get("startDateTime"),
        "venta_fin":        venta.get("endDateTime"),
        "segmento":         clasificacion.get("segment", {}).get("name"),
        "genero":           clasificacion.get("genre", {}).get("name"),
        "subgenero":        clasificacion.get("subGenre", {}).get("name"),
        "recinto_id":       venue.get("id"),
        "recinto_nombre":   venue.get("name"),
        "ciudad":           (venue.get("city") or {}).get("name"),
        "direccion":        (venue.get("address") or {}).get("line1"),
        "codigo_postal":    venue.get("postalCode"),
        "latitud":          float(ubicacion["latitude"])  if ubicacion.get("latitude")  else None,
        "longitud":         float(ubicacion["longitude"]) if ubicacion.get("longitude") else None,
        "artista_id":       atraccion.get("id"),
        "artista_nombre":   atraccion.get("name"),
        "artista_imagen":   sacar_mejor_imagen(atraccion.get("images") or [], ratio="3_2", min_ancho=300),
        "imagen_evento":    sacar_mejor_imagen(evento_raw.get("images") or [], ratio="16_9", min_ancho=1000),
        "promotor":         (evento_raw.get("promoter") or {}).get("name"),
    }

    logging.debug(f"[Ticketmaster] Evento procesado: id = {evento["id"]}")
    return evento

schema_bq = {
    "fields": [
        {
            "name": "id",             
            "type": "STRING",    
            "mode": "REQUIRED"
        },
        {
            "name": "nombre",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "url",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "fecha",
            "type": "DATE",
            "mode": "NULLABLE"
        },
        {
            "name": "hora",
            "type": "TIME",
            "mode": "NULLABLE"
        },
        {
            "name": "fecha_utc",
            "type": "TIMESTAMP",
            "mode": "NULLABLE"
        },
        {
            "name": "estado",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "venta_inicio",
            "type": "TIMESTAMP",
            "mode": "NULLABLE"
        },
        {
            "name": "venta_fin",
            "type": "TIMESTAMP",
            "mode": "NULLABLE"
        },
        {
            "name": "segmento",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "genero",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "subgenero",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "recinto_id",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "recinto_nombre",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "ciudad",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "direccion",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "codigo_postal",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "latitud",
            "type": "FLOAT64",
            "mode": "NULLABLE"
        },
        {
            "name": "longitud",
            "type": "FLOAT64",
            "mode": "NULLABLE"
        },
        {
            "name": "artista_id",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "artista_nombre",
            "type": "STRING",
            "mode": "NULLABLE"
        },
        {
            "name": "promotor",
            "type": "STRING",
            "mode": "NULLABLE"
        },
    ]
}

def limpiar_datos_bq(evento: dict) -> dict:
    campos_bq = {f["name"] for f in schema_bq["fields"]}
    return {campo: evento.get(campo) for campo in campos_bq}


class ObtenerEventosTicketmaster(beam.DoFn):
    def __init__(self, id_proyecto: str, id_secreto: str):
        self.id_proyecto = id_proyecto
        self.id_secreto  = id_secreto

    def setup(self):
        self.api_key = obtener_secreto(self.id_proyecto, self.id_secreto)
        logging.info("[ObtenerEventosTicketmaster] Worker inicializado")

    def process(self, _):
        yield from obtener_eventos_ticketmaster(self.api_key)


ETIQUETA_ERRORES = "errores"


class TransformarEvento(beam.DoFn):
    def process(self, evento_raw: dict):
        try:
            yield transformar_evento(evento_raw)
        except Exception as e:
            logging.warning("[TransformarEvento] Error — id=%s | %s", evento_raw.get("id"), e)
            yield beam.pvalue.TaggedOutput(ETIQUETA_ERRORES, json.dumps({
                "id":        evento_raw.get("id"),
                "error":     str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw":       evento_raw,
            }, default=str))


class EscribirEnFirestore(beam.DoFn):
    def __init__(self, id_proyecto: str, coleccion: str):
        self.id_proyecto = id_proyecto
        self.coleccion   = coleccion

    def setup(self):
        self.cliente = firestore.Client(project=self.id_proyecto)
        logging.info(f"[Firestore] Cliente inicializado — colección: {self.coleccion}")

    def process(self, evento: dict):
        self.cliente.collection(self.coleccion).document(evento["id"]).set(evento, merge=True)
        logging.debug(f"[Firestore] Evento guardado — id={evento['id']} | nombre={evento.get('nombre')}")
        yield evento


precios_rest_alojamiento = {
    "PRICE_LEVEL_UNSPECIFIED": "No especificado",
    "PRICE_LEVEL_FREE": "Gratis",
    "PRICE_LEVEL_INEXPENSIVE": "€",
    "PRICE_LEVEL_MODERATE": "€€",
    "PRICE_LEVEL_EXPENSIVE": "€€€",
    "PRICE_LEVEL_VERY_EXPENSIVE": "€€€€",
}


def calcular_radio_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def buscar_google_places(api_key: str, lat: float, lng: float, tipos: list[str], radio_metros: int) -> list[dict]:
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key":   api_key,
        "X-Goog-FieldMask": "places.displayName,places.location,places.rating,places.priceLevel,places.formattedAddress,places.types",
        "Content-Type":     "application/json",
    }
    body = {
        "includedTypes": tipos,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radio_metros),
            }
        },
    }
    logging.debug(f"[Places] Buscando tipos={tipos} en radio={radio_metros}m | lat={lat:.5f} lng={lng:.5f}")
    respuesta = reintentos_peticiones(
        lambda: requests.post(url, headers=headers, json=body, timeout=30)
    )
    respuesta.raise_for_status()
    lugares = respuesta.json().get("places", [])
    logging.debug(f"[Places] {len(lugares)} resultados para tipos={tipos}")
    return lugares


def consultar_google_places(api_key: str, lat: float, lng: float) -> tuple[list[dict], list[dict]]:
    lugares_restaurantes = buscar_google_places(api_key, lat, lng, tipos=["restaurant"], radio_metros=1000)
    lugares_alojamientos = buscar_google_places(api_key, lat, lng, tipos=["hotel", "motel", "hostel", "lodging"], radio_metros=5000)

    restaurantes = []
    for lugar in lugares_restaurantes:
        loc = lugar.get("location", {})
        distancia = calcular_radio_metros(lat, lng, loc["latitude"], loc["longitude"]) if loc else None
        restaurantes.append({
            "nombre":           lugar.get("displayName", {}).get("text"),
            "valoracion":       lugar.get("rating"),
            "precio":           precios_rest_alojamiento.get(lugar.get("priceLevel")),
            "direccion":        lugar.get("formattedAddress"),
            "distancia_metros": distancia,
        })

    alojamientos = []
    for lugar in lugares_alojamientos:
        loc = lugar.get("location", {})
        distancia = calcular_radio_metros(lat, lng, loc["latitude"], loc["longitude"]) if loc else None
        tipos_lugar = lugar.get("types", [])
        tipo = next((t for t in ("hotel", "motel", "hostel") if t in tipos_lugar), "alojamiento")
        alojamientos.append({
            "nombre":           lugar.get("displayName", {}).get("text"),
            "tipo":             tipo,
            "valoracion":       lugar.get("rating"),
            "precio":           precios_rest_alojamiento.get(lugar.get("priceLevel")),
            "direccion":        lugar.get("formattedAddress"),
            "distancia_metros": distancia,
        })

    restaurantes.sort(key=lambda x: x["distancia_metros"] or 9999)
    alojamientos.sort(key=lambda x: x["distancia_metros"] or 9999)

    logging.info(f"[Places] Resultados finales — {len(restaurantes)} restaurantes | {len(alojamientos)} alojamientos")
    return restaurantes, alojamientos

class EnriquecerConRecinto(beam.DoFn):
    def __init__(self, id_proyecto: str, coleccion_recintos: str, id_secreto_places: str):
        self.id_proyecto        = id_proyecto
        self.coleccion_recintos = coleccion_recintos
        self.id_secreto_places  = id_secreto_places

    def setup(self):
        self.db      = firestore.Client(project=self.id_proyecto)
        self.api_key = obtener_secreto(self.id_proyecto, self.id_secreto_places)
        logging.info(f"[EnriquecerConRecinto] Worker inicializado — colección recintos: {self.coleccion_recintos}")

    def process(self, evento: dict):
        recinto_id = evento.get("recinto_id")
        lat        = evento.get("latitud")
        lng        = evento.get("longitud")

        if not recinto_id or lat is None or lng is None:
            logging.warning(f"[EnriquecerConRecinto] Evento sin recinto o coordenadas — id={evento.get('id')} | nombre={evento.get('nombre')}")
            yield evento
            return

        ref_recinto = self.db.collection(self.coleccion_recintos).document(recinto_id)
        doc_recinto = ref_recinto.get()

        if doc_recinto.exists:
            datos_recinto = doc_recinto.to_dict()
            logging.info(f"[EnriquecerConRecinto] Caché HIT — recinto_id={recinto_id} | nombre={datos_recinto.get('nombre')}")
        else:
            logging.info(f"[EnriquecerConRecinto] Caché MISS — recinto_id={recinto_id} | consultando Google Places...")
            restaurantes, alojamientos = consultar_google_places(self.api_key, lat, lng)
            ahora = datetime.now(timezone.utc)
            datos_recinto = {
                "id":                   recinto_id,
                "nombre":               evento.get("recinto_nombre"),
                "ciudad":               evento.get("ciudad"),
                "latitud":              lat,
                "longitud":             lng,
                "restaurantes":         restaurantes,
                "alojamientos":         alojamientos,
                "fecha_creacion":       ahora.isoformat(),
                "fecha_expiracion":     (ahora + timedelta(weeks=2)).isoformat(),
            }
            ref_recinto.set(datos_recinto)
            logging.info(f"[EnriquecerConRecinto] Recinto guardado en Firestore — recinto_id={recinto_id} | {len(restaurantes)} restaurantes | {len(alojamientos)} alojamientos")

        yield {
            **evento,
            "restaurantes_cercanos": datos_recinto.get("restaurantes", []),
            "alojamientos_cercanos": datos_recinto.get("alojamientos", []),
        }


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
    },
    "required": ["minutos_antelacion", "motivo"],
}


class EnriquecerConGemini(beam.DoFn):
    def __init__(self, id_proyecto: str, id_secreto_gemini: str):
        self.id_proyecto       = id_proyecto
        self.id_secreto_gemini = id_secreto_gemini

    def setup(self):
        api_key = obtener_secreto(self.id_proyecto, self.id_secreto_gemini)
        genai.configure(api_key=api_key)
        self.modelo = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=schema_salida_enriquecimiento_gemini,
            ),
        )
        logging.info("[Gemini] Worker inicializado — modelo: gemini-2.5-flash")

    def process(self, evento: dict):
        restaurantes = evento.get("restaurantes_cercanos") or []
        alojamientos = evento.get("alojamientos_cercanos") or []

        prompt = f"""Eres un asistente experto en eventos en España. Dado el siguiente evento, \
indica cuántos minutos antes del inicio se recomienda llegar y el motivo principal en una frase corta. \
Ten en cuenta el tipo de evento, el tamaño habitual del recinto y si hay restaurantes cercanos.

Evento: {evento.get("nombre")}
Tipo: {evento.get("segmento")} — {evento.get("genero")}
Recinto: {evento.get("recinto_nombre")} ({evento.get("ciudad")})
Restaurantes a menos de 1 km: {len(restaurantes)}
Alojamientos a menos de 5 km: {len(alojamientos)}"""

        try:
            respuesta = reintentos_peticiones(lambda: self.modelo.generate_content(prompt))
            antelacion = json.loads(respuesta.text)
            logging.info("[Gemini] Antelación generada — id=%s | %d min | motivo: %s", evento.get("id"), antelacion.get("minutos_antelacion"), antelacion.get("motivo"))
        except Exception as e:
            antelacion = None
            logging.error("[Gemini] Error al generar antelación — id=%s | error: %s", evento.get("id"), e, exc_info=True)

        yield {**evento, "antelacion_recomendada": antelacion}


def run():
    parser = argparse.ArgumentParser(description="Argumentos necesarios para la ejecución del batch de ingestión de Dataflow")

    parser.add_argument(
        "--id_proyecto",                  
        required = True, 
        help = "ID del proyecto de GCP"
    )

    parser.add_argument(
        "--coleccion_firestore_eventos",  
        required = True, 
        help = "Colección de Firestore para eventos"
    )

    parser.add_argument(
        "--coleccion_firestore_recintos", 
        required = True, 
        help = "Colección de Firestore para recintos con restaurantes y alojamientos"
    )

    parser.add_argument(
        "--dataset_bigquery",              
        required = True, 
        help = "Dataset de BigQuery"
    )

    parser.add_argument(
        "--tabla_eventos_bigquery",       
        required = True, 
        help = "Tabla de BigQuery para eventos"
    )

    parser.add_argument(
        "--bucket_gcs",                   
        required = True, 
        help = "Ruta del bucket GCS para eventos en crudo (ej: gs://mi-bucket/eventos)"
    )

    parser.add_argument(
        "--id_secreto_ticketmaster",      
        required = True, 
        help = "ID del secreto en Secret Manager para la API key de Ticketmaster"
    )

    parser.add_argument(
        "--id_secreto_google_places",
        required = True,
        help = "ID del secreto en Secret Manager para la API key de Google Places"
    )

    parser.add_argument(
        "--id_secreto_gemini",
        required = True,
        help = "ID del secreto en Secret Manager para la API key de Gemini"
    )

    argumentos, pipeline_opts = parser.parse_known_args()

    _worker_image = (
        f"europe-west1-docker.pkg.dev/{argumentos.id_proyecto}"
        f"/repo-recomendador-eventos/batch-ingesta:latest"
    )

    configuracion_pipeline = PipelineOptions(
        pipeline_opts,
        save_main_session=True,
        streaming=False,
        project=argumentos.id_proyecto,
        sdk_container_image=_worker_image,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ruta_destino_gcs_eventos = f"{argumentos.bucket_gcs}/ticketmaster_{timestamp}"
    logging.info(f"[Pipeline] Ruta destino GCS: {ruta_destino_gcs_eventos}")

    ref_tabla_bq = f"{argumentos.id_proyecto}.{argumentos.dataset_bigquery}.{argumentos.tabla_eventos_bigquery}"

    with beam.Pipeline(options=configuracion_pipeline) as p:

        eventos_ticketmaster = (
            p
            | "IniciarPipeline" >> beam.Create([None])
            | "ObtenerEventosTicketMaster" >> beam.ParDo(
                ObtenerEventosTicketmaster(
                    argumentos.id_proyecto,
                    argumentos.id_secreto_ticketmaster,
                )
            )
        )

        _ = (
            eventos_ticketmaster
            | "EventosCrudosJSON" >> beam.Map(json.dumps)
            | "GuardarEventosCrudosGCS" >> WriteToText(
                ruta_destino_gcs_eventos,
                file_name_suffix=".json",
                shard_name_template="",
                num_shards=1,
            )
        )

        resultado_transformacion = (
            eventos_ticketmaster
            | "TransformarEventos" >> beam.ParDo(TransformarEvento()).with_outputs(ETIQUETA_ERRORES, main="validos")
        )

        _ = (
            resultado_transformacion[ETIQUETA_ERRORES]
            | "GuardarErroresGCS" >> WriteToText(
                f"{argumentos.bucket_gcs}/errores/transformacion_{timestamp}",
                file_name_suffix=".json",
                shard_name_template="",
                num_shards=1,
            )
        )

        eventos_enriquecidos = (
            resultado_transformacion.validos
            | "EnriquecerConRecinto" >> beam.ParDo(
                EnriquecerConRecinto(
                    argumentos.id_proyecto,
                    argumentos.coleccion_firestore_recintos,
                    argumentos.id_secreto_google_places,
                )
            )
            | "EnriquecerConGemini" >> beam.ParDo(
                EnriquecerConGemini(argumentos.id_proyecto, argumentos.id_secreto_gemini)
            )
        )

        _ = (
            eventos_enriquecidos
            | "GuardarEventosFirestore" >> beam.ParDo(
                EscribirEnFirestore(argumentos.id_proyecto, argumentos.coleccion_firestore_eventos)
            )
        )

        ids_existentes = (
            p
            | "LeerIDsExistentes" >> ReadFromBigQuery(
                query=f"SELECT id FROM `{ref_tabla_bq}`",
                use_standard_sql=True,
            )
            | "ExtraerIDs" >> beam.Map(lambda row: row["id"])
        )

        tabla_bq = f"{argumentos.id_proyecto}:{argumentos.dataset_bigquery}.{argumentos.tabla_eventos_bigquery}"
        _ = (
            eventos_enriquecidos
            | "LimpiarParaBigQuery" >> beam.Map(limpiar_datos_bq)
            | "FiltrarEventosNuevos" >> beam.Filter(
                lambda evento, ids: evento["id"] not in ids,
                ids=beam.pvalue.AsSet(ids_existentes),
            )
            | "GuardarEventosBigQuery" >> WriteToBigQuery(
                tabla_bq,
                schema=schema_bq,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("[Pipeline] Comienza la ingestión")
    run()
