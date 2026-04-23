"""
Local dev seed — inserts fixture events into the Firestore emulator.

Targets the `eventos` collection that the backend reads (see
backend/portal-api/app/api/v1/endpoints/events.py:8). Events carry the same
field names that the real ingestion pipeline produces
(see ingestion/pipeline_batch_ingestion.py), so the portal renders the same
shapes as in production.

Idempotent — documents are keyed by event id and written with merge=True.
"""

import os
import socket
import time

import firebase_admin
from firebase_admin import credentials, firestore

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "demo-local")
COLLECTION = os.environ.get("FIRESTORE_EVENTS_COLLECTION", "eventos")


EVENTS: list[dict] = [
    {
        "id": "evt-madrid-neon-pulse",
        "nombre": "Neon Pulse — Synthwave Night",
        "url": "https://www.ticketmaster.es/search?q=La+Riviera",
        "fecha": "2026-05-14",
        "hora": "22:00",
        "fecha_utc": "2026-05-14T20:00:00Z",
        "estado": "onsale",
        "segmento": "Music",
        "genero": "Electronic",
        "subgenero": "Synthwave",
        "recinto_id": "rec-la-riviera",
        "recinto_nombre": "La Riviera",
        "ciudad": "Madrid",
        "direccion": "Paseo Bajo de la Virgen del Puerto, s/n, 28005 Madrid",
        "latitud": 40.4108,
        "longitud": -3.7221,
        "artista_id": "art-neon-pulse",
        "artista_nombre": "Neon Pulse Collective",
        "artista_imagen": "https://picsum.photos/seed/neon-pulse/400/400",
        "imagen_evento": "https://picsum.photos/seed/neon-pulse-event/800/450",
        "promotor": "Live Nation ES",
    },
    {
        "id": "evt-madrid-matadero-digital-soul",
        "nombre": "Digital Soul — Immersive Exhibition",
        "url": "https://www.mataderomadrid.org/",
        "fecha": "2026-05-18",
        "hora": "19:30",
        "fecha_utc": "2026-05-18T17:30:00Z",
        "estado": "onsale",
        "segmento": "Arts & Theatre",
        "genero": "Multimedia",
        "subgenero": "Digital Art",
        "recinto_id": "rec-matadero",
        "recinto_nombre": "Matadero Madrid",
        "ciudad": "Madrid",
        "direccion": "Plaza de Legazpi, 8, 28045 Madrid",
        "latitud": 40.3905,
        "longitud": -3.6975,
        "artista_id": "art-digital-soul",
        "artista_nombre": "Collective AV",
        "artista_imagen": "https://picsum.photos/seed/digital-soul/400/400",
        "imagen_evento": "https://picsum.photos/seed/digital-soul-event/800/450",
        "promotor": "Matadero",
    },
    {
        "id": "evt-bcn-sonar-warmup",
        "nombre": "Sónar Warm-up — Underground Techno",
        "url": "https://www.salarazzmatazz.com/",
        "fecha": "2026-06-12",
        "hora": "23:30",
        "fecha_utc": "2026-06-12T21:30:00Z",
        "estado": "onsale",
        "segmento": "Music",
        "genero": "Electronic",
        "subgenero": "Techno",
        "recinto_id": "rec-razzmatazz",
        "recinto_nombre": "Razzmatazz",
        "ciudad": "Barcelona",
        "direccion": "Carrer dels Almogàvers, 122, 08018 Barcelona",
        "latitud": 41.3980,
        "longitud": 2.1909,
        "artista_id": "art-sonar-warmup",
        "artista_nombre": "Hex Resident",
        "artista_imagen": "https://picsum.photos/seed/sonar-warmup/400/400",
        "imagen_evento": "https://picsum.photos/seed/sonar-warmup-event/800/450",
        "promotor": "Advanced Music",
    },
    {
        "id": "evt-valencia-cinema-under-stars",
        "nombre": "Cinema Under the Stars — Blade Runner 2049",
        "url": "https://www.filmin.es/pelicula/blade-runner-2049",
        "fecha": "2026-07-04",
        "hora": "22:00",
        "fecha_utc": "2026-07-04T20:00:00Z",
        "estado": "onsale",
        "segmento": "Film",
        "genero": "Sci-Fi",
        "subgenero": "Cyberpunk",
        "recinto_id": "rec-jardines-palau",
        "recinto_nombre": "Jardines del Palau",
        "ciudad": "Valencia",
        "direccion": "Passeig de l'Albereda, 30, 46023 Valencia",
        "latitud": 39.4578,
        "longitud": -0.3540,
        "artista_id": None,
        "artista_nombre": "Ridley Scott (dir.)",
        "artista_imagen": "https://picsum.photos/seed/blade-runner/400/400",
        "imagen_evento": "https://picsum.photos/seed/cinema-stars-event/800/450",
        "promotor": "Cinema al Fresco",
    },
    {
        "id": "evt-madrid-wanda-derbi",
        "nombre": "Derbi Madrileño — Atleti vs Real Madrid",
        "url": "https://www.atleticodemadrid.com/entradas",
        "fecha": "2026-05-24",
        "hora": "21:00",
        "fecha_utc": "2026-05-24T19:00:00Z",
        "estado": "onsale",
        "segmento": "Sports",
        "genero": "Soccer",
        "subgenero": "La Liga",
        "recinto_id": "rec-metropolitano",
        "recinto_nombre": "Riyadh Air Metropolitano",
        "ciudad": "Madrid",
        "direccion": "Av. de Luis Aragonés, 4, 28022 Madrid",
        "latitud": 40.4362,
        "longitud": -3.5996,
        "artista_id": None,
        "artista_nombre": None,
        "artista_imagen": None,
        "imagen_evento": "https://picsum.photos/seed/derbi-event/800/450",
        "promotor": "La Liga",
    },
    {
        "id": "evt-madrid-neon-pulse-night2",
        "nombre": "Neon Pulse — Synthwave Night",
        "url": "https://www.ticketmaster.es/search?q=La+Riviera",
        "fecha": "2026-05-15",
        "hora": "22:00",
        "fecha_utc": "2026-05-15T20:00:00Z",
        "estado": "onsale",
        "segmento": "Music",
        "genero": "Electronic",
        "subgenero": "Synthwave",
        "recinto_id": "rec-la-riviera",
        "recinto_nombre": "La Riviera",
        "ciudad": "Madrid",
        "direccion": "Paseo Bajo de la Virgen del Puerto, s/n, 28005 Madrid",
        "latitud": 40.4108,
        "longitud": -3.7221,
        "artista_id": "art-neon-pulse",
        "artista_nombre": "Neon Pulse Collective",
        "artista_imagen": "https://picsum.photos/seed/neon-pulse/400/400",
        "imagen_evento": "https://picsum.photos/seed/neon-pulse-event/800/450",
        "promotor": "Live Nation ES",
    },
    {
        "id": "evt-madrid-neon-pulse-night2-late",
        "nombre": "Neon Pulse — Synthwave Night",
        "url": "https://www.ticketmaster.es/search?q=La+Riviera",
        "fecha": "2026-05-15",
        "hora": "01:30",
        "fecha_utc": "2026-05-15T23:30:00Z",
        "estado": "onsale",
        "segmento": "Music",
        "genero": "Electronic",
        "subgenero": "Synthwave",
        "recinto_id": "rec-la-riviera",
        "recinto_nombre": "La Riviera",
        "ciudad": "Madrid",
        "direccion": "Paseo Bajo de la Virgen del Puerto, s/n, 28005 Madrid",
        "latitud": 40.4108,
        "longitud": -3.7221,
        "artista_id": "art-neon-pulse",
        "artista_nombre": "Neon Pulse Collective",
        "artista_imagen": "https://picsum.photos/seed/neon-pulse/400/400",
        "imagen_evento": "https://picsum.photos/seed/neon-pulse-event/800/450",
        "promotor": "Live Nation ES",
    },
    {
        "id": "evt-madrid-neon-pulse-night3",
        "nombre": "Neon Pulse — Synthwave Night",
        "url": "https://www.ticketmaster.es/search?q=La+Riviera",
        "fecha": "2026-05-16",
        "hora": "22:00",
        "fecha_utc": "2026-05-16T20:00:00Z",
        "estado": "onsale",
        "segmento": "Music",
        "genero": "Electronic",
        "subgenero": "Synthwave",
        "recinto_id": "rec-la-riviera",
        "recinto_nombre": "La Riviera",
        "ciudad": "Madrid",
        "direccion": "Paseo Bajo de la Virgen del Puerto, s/n, 28005 Madrid",
        "latitud": 40.4108,
        "longitud": -3.7221,
        "artista_id": "art-neon-pulse",
        "artista_nombre": "Neon Pulse Collective",
        "artista_imagen": "https://picsum.photos/seed/neon-pulse/400/400",
        "imagen_evento": "https://picsum.photos/seed/neon-pulse-event/800/450",
        "promotor": "Live Nation ES",
    },
    {
        "id": "evt-bcn-sonar-warmup-night2",
        "nombre": "Sónar Warm-up — Underground Techno",
        "url": "https://www.salarazzmatazz.com/",
        "fecha": "2026-06-13",
        "hora": "23:30",
        "fecha_utc": "2026-06-13T21:30:00Z",
        "estado": "onsale",
        "segmento": "Music",
        "genero": "Electronic",
        "subgenero": "Techno",
        "recinto_id": "rec-razzmatazz",
        "recinto_nombre": "Razzmatazz",
        "ciudad": "Barcelona",
        "direccion": "Carrer dels Almogàvers, 122, 08018 Barcelona",
        "latitud": 41.3980,
        "longitud": 2.1909,
        "artista_id": "art-sonar-warmup",
        "artista_nombre": "Hex Resident",
        "artista_imagen": "https://picsum.photos/seed/sonar-warmup/400/400",
        "imagen_evento": "https://picsum.photos/seed/sonar-warmup-event/800/450",
        "promotor": "Advanced Music",
    },
    {
        "id": "evt-sevilla-flamenco-clandestino",
        "nombre": "Flamenco Clandestino — Tablao Íntimo",
        "url": "https://www.tablaolosgallos.com/",
        "fecha": "2026-05-30",
        "hora": "23:00",
        "fecha_utc": "2026-05-30T21:00:00Z",
        "estado": "onsale",
        "segmento": "Arts & Theatre",
        "genero": "Flamenco",
        "subgenero": "Traditional",
        "recinto_id": "rec-casa-carmen",
        "recinto_nombre": "Casa de Carmen",
        "ciudad": "Sevilla",
        "direccion": "Calle Marqués de Paradas, 30, 41001 Sevilla",
        "latitud": 37.3891,
        "longitud": -5.9845,
        "artista_id": "art-carmen",
        "artista_nombre": "Carmen del Río",
        "artista_imagen": "https://picsum.photos/seed/carmen/400/400",
        "imagen_evento": "https://picsum.photos/seed/flamenco-event/800/450",
        "promotor": "Tablao Íntimo",
    },
]


class _EmulatorCredential(credentials.Base):
    """Stub credential — the Firestore emulator ignores auth."""

    def get_credential(self):
        from google.oauth2.credentials import Credentials as _GoogleCredentials
        return _GoogleCredentials(token="local-emulator-token")


def _wait_for_emulator(host_port: str, timeout: float = 60.0) -> None:
    host, port = host_port.rsplit(":", 1)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, int(port)), timeout=2):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError(f"Firestore emulator not reachable at {host_port} after {timeout}s")


def main() -> None:
    host_port = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if not host_port:
        raise RuntimeError(
            "FIRESTORE_EMULATOR_HOST is not set — this script only targets the emulator.",
        )
    _wait_for_emulator(host_port)

    firebase_admin.initialize_app(_EmulatorCredential(), {"projectId": PROJECT_ID})
    db = firestore.client()

    for event in EVENTS:
        db.collection(COLLECTION).document(event["id"]).set(event, merge=True)
        print(f"  ✓ {event['id']} — {event['nombre']}")

    print(f"Seeded {len(EVENTS)} events into '{COLLECTION}'.")


if __name__ == "__main__":
    main()
