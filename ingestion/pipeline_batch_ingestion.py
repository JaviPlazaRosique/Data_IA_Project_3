from datetime import datetime, timedelta, timezone
import requests
import argparse
import json
import logging

from google.cloud import secretmanager
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import WriteToText

def obtener_secreto(id_proyecto: str, id_secreto: str, version: str = "latest") -> str:
    cliente = secretmanager.SecretManagerServiceClient()
    ubicacion_secreto = f"projects/{id_proyecto}/secrets/{id_secreto}/versions/{version}"
    respuesta = cliente.access_secret_version(request={"name": ubicacion_secreto})
    return respuesta.payload.data.decode("UTF-8")

def obtener_eventos_ticketmaster(api_key: str) -> list[dict]:
    url_base_ticketmaster = "https://app.ticketmaster.com/discovery/v2/events.json"
    codigo_pais = "ES"
    dias_ventana = 12
    longitud_pagina = 200
    ahora = datetime.now(timezone.utc)
    fecha_inicio = ahora.strftime("%Y-%m-%dT%H:%M:%SZ")
    fecha_fin = (ahora + timedelta(days = dias_ventana)).strftime("%Y-%m-%dT%H:%M:%SZ")

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

        respuesta = requests.get(url_base_ticketmaster, params=params, timeout=30)
        respuesta.raise_for_status()
        datos = respuesta.json()

        embedded = datos.get("_embedded")
        if not embedded:
            break

        todos_los_eventos.extend(embedded.get("events", []))

        info_pagina = datos.get("page", {})
        total_paginas = info_pagina.get("totalPages", 1)
        pagina += 1

        if pagina >= total_paginas:
            break

    return todos_los_eventos

def run():
    parser = argparse.ArgumentParser(description = ('Argumentos necesarios para la ejecución del batch de ingestión de Dataflow'))

    parser.add_argument(
        '--id_proyecto',
        required = False, 
        help = 'ID del proyecto de GCP'
    )

    parser.add_argument(
        '--coleccion_firestore_eventos',
        required = False, 
        help = 'Colección de Firestore en la que se guardarán los eventos.'
    )

    parser.add_argument(
        '--dataset_bigquery',
        required = False, 
        hepl = 'Dataset de BigQuery en el que se guardarán los datos'
    )

    parser.add_argument(
        '--tabla_eventos_bigquery',
        required = False,
        help = 'Tabla de BigQuery en la que se guardarán todos los eventos'
    )

    parser.add_argument(
        '--bucket_gcs',
        required = False,
        help = 'Ruta del bucket de GCS donde se guardarán los eventos en formato JSON (ej: gs://mi-bucket/eventos)'
    )

    argumentos, pipeline_opts = parser.parse_known_args()

    configuracion_pipeline = PipelineOptions(
        pipeline_opts, 
        save_main_session = True, 
        streaming = False, 
        project = argumentos.id_proyecto
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ruta_destino_gcs_eventos = f"{argumentos.bucket_gcs}/ticketmaster_{timestamp}"

    with beam.Pipeline(options = configuracion_pipeline) as p:

        eventos_ticketmaster = (
            p
            | "ObtenerEventosTicketMaster" >> beam.Create(obtener_eventos_ticketmaster(obtener_secreto(argumentos.id_proyecto, "ticketmaster-api-key")))
        )

        _ = (
            eventos_ticketmaster
            | "EventosTicketMasterJSON" >> beam.Map(json.dumps)
            | "GuardarEventosTicketMasterGCS" >> WriteToText(
                ruta_destino_gcs_eventos,
                file_name_suffix=".json",
                shard_name_template="",
                num_shards=1,
            )
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)

    logging.info("Comienza la ingestion")

    run()