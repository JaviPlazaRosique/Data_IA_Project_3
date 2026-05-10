"""Generate synthetic catalog events compatible with Firestore and BigQuery.

By default this script only writes a JSONL file that can be inspected before
loading. Use --upload-firestore and/or --upload-bigquery to publish the rows.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE_DIR / "swipes_data" / "synthetic_events_generated.jsonl"
DEFAULT_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "project3grupo3")
DEFAULT_DATASET = "recomendacion_planes"
DEFAULT_TABLE = "eventos"
DEFAULT_COLLECTION = "eventos"
MADRID_TZ = ZoneInfo("Europe/Madrid")
SAFE_ID_RE = re.compile(r"[^a-z0-9]+")
UUID_NAMESPACE = uuid.UUID("8fd58834-c069-4f1d-b3f8-52d3d273f8d8")

FIRESTORE_EVENT_FIELDS = {
    "id",
    "uuid_evento",
    "nombre",
    "url",
    "es_test",
    "fecha",
    "hora",
    "fecha_utc",
    "estado",
    "venta_inicio",
    "venta_fin",
    "segmento",
    "genero",
    "subgenero",
    "recinto_id",
    "recinto_nombre",
    "ciudad",
    "direccion",
    "codigo_postal",
    "latitud",
    "longitud",
    "artista_id",
    "artista_nombre",
    "artista_imagen",
    "imagen_evento",
    "promotor",
    "descripcion",
    "restaurantes_cercanos",
    "alojamientos_cercanos",
    "antelacion_recomendada",
    "contexto_rag",
    "categoria",
    "subcategoria",
    "franja_horaria",
    "tiempo",
}


@dataclass(frozen=True)
class City:
    name: str
    slug: str
    postal_code: str
    lat: float
    lng: float
    venues: tuple[tuple[str, str, str], ...]
    restaurants: tuple[tuple[str, str], ...]
    hotels: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class EventTemplate:
    slug: str
    title: str
    segment: str
    genre: str
    subgenre: str
    category: str
    vibe: str
    indoor_outdoor: str
    price_band: str
    duration_range: tuple[int, int]
    scores: tuple[int, int, int, int]
    promoter: str
    artist_suffix: str
    lead_minutes: int
    lead_reason: str
    time_slots: tuple[str, ...]


CITIES: tuple[City, ...] = (
    City(
        "Madrid",
        "madrid",
        "28004",
        40.4168,
        -3.7038,
        (
            ("rec-synth-madrid-malasana", "Sala Prisma Malasana", "Calle Pez, 23, 28004 Madrid"),
            ("rec-synth-madrid-rio", "Auditorio Rio Demo", "Paseo de la Chopera, 12, 28045 Madrid"),
            ("rec-synth-madrid-granvia", "Teatro Aurora Gran Via", "Gran Via, 58, 28013 Madrid"),
        ),
        (
            ("Bistro Prisma", "Calle Pez, 19"),
            ("La Terraza del Rio", "Paseo de la Chopera, 18"),
        ),
        (
            ("Hostal Centro Norte", "Corredera Baja, 8"),
            ("Gran Via Rooms", "Calle Silva, 14"),
        ),
    ),
    City(
        "Barcelona",
        "barcelona",
        "08005",
        41.3874,
        2.1686,
        (
            ("rec-synth-barcelona-poblenou", "Hangar Delta Poblenou", "Carrer de Pallars, 180, 08005 Barcelona"),
            ("rec-synth-barcelona-gracia", "Teatre Llum Gracia", "Carrer Verdi, 32, 08012 Barcelona"),
            ("rec-synth-barcelona-montjuic", "Mirador Stage Montjuic", "Av. Miramar, 30, 08038 Barcelona"),
        ),
        (
            ("Montjuic Picnic Bar", "Av. Miramar, 12"),
            ("Verdi Tapas", "Carrer Verdi, 20"),
        ),
        (
            ("Poble Sec Stay", "Carrer de Blai, 9"),
            ("Gracia Urban Hotel", "Travessera de Gracia, 44"),
        ),
    ),
    City(
        "Valencia",
        "valencia",
        "46023",
        39.4699,
        -0.3763,
        (
            ("rec-synth-valencia-marina", "Marina Sound Yard", "Carrer del Moll de la Duana, 46024 Valencia"),
            ("rec-synth-valencia-turia", "Jardin Turia Arena", "Passeig de la Petxina, 46008 Valencia"),
            ("rec-synth-valencia-ruzafa", "Ruzafa Black Box", "Carrer de Cuba, 32, 46006 Valencia"),
        ),
        (
            ("Ruzafa Bites", "Carrer Sueca, 18"),
            ("Marina Rice Bar", "Carrer del Port, 21"),
        ),
        (
            ("Turia Boutique Stay", "Gran Via, 72"),
            ("Marina Rooms", "Carrer de la Reina, 4"),
        ),
    ),
    City(
        "Sevilla",
        "sevilla",
        "41001",
        37.3891,
        -5.9845,
        (
            ("rec-synth-sevilla-alameda", "Alameda Stage Lab", "Alameda de Hercules, 44, 41002 Sevilla"),
            ("rec-synth-sevilla-triana", "Patio Triana Demo", "Calle Betis, 18, 41010 Sevilla"),
            ("rec-synth-sevilla-centro", "Teatro Sur Central", "Calle Sierpes, 20, 41004 Sevilla"),
        ),
        (
            ("Alameda Cocina", "Alameda de Hercules, 36"),
            ("Triana Tapas", "Calle Pureza, 22"),
        ),
        (
            ("Sevilla Patio Hotel", "Calle Feria, 15"),
            ("Triana River Stay", "Calle Betis, 25"),
        ),
    ),
    City(
        "Bilbao",
        "bilbao",
        "48009",
        43.2630,
        -2.9350,
        (
            ("rec-synth-bilbao-abando", "Abando Live Hall", "Alameda Recalde, 28, 48009 Bilbao"),
            ("rec-synth-bilbao-ria", "Ria Norte Arena", "Muelle Ramon de la Sota, 1, 48013 Bilbao"),
            ("rec-synth-bilbao-casco", "Casco Viejo Studio", "Somera Kalea, 14, 48005 Bilbao"),
        ),
        (
            ("Ria Pintxos", "Ledesma Kalea, 8"),
            ("Abando Bistro", "Colon de Larreategui, 12"),
        ),
        (
            ("Bilbao Ria Rooms", "Uribitarte, 7"),
            ("Casco Stay", "Bidebarrieta, 3"),
        ),
    ),
    City(
        "Malaga",
        "malaga",
        "29015",
        36.7213,
        -4.4214,
        (
            ("rec-synth-malaga-soho", "Soho Open Stage", "Calle Alemania, 14, 29001 Malaga"),
            ("rec-synth-malaga-muelle", "Muelle Uno Demo", "Paseo del Muelle Uno, 29016 Malaga"),
            ("rec-synth-malaga-centro", "Teatro Brisa Centro", "Calle Alcazabilla, 6, 29015 Malaga"),
        ),
        (
            ("Soho Brunch", "Calle Casas de Campos, 7"),
            ("Muelle Seafood", "Paseo del Muelle Uno, 4"),
        ),
        (
            ("Centro Light Hotel", "Calle Granada, 11"),
            ("Soho Rooms", "Calle Alemania, 20"),
        ),
    ),
)


TEMPLATES: tuple[EventTemplate, ...] = (
    EventTemplate(
        "delta-frequencies",
        "Delta Frequencies",
        "Music",
        "Electronic",
        "Techno",
        "club_night",
        "energia_alta",
        "interior",
        "alto",
        (180, 300),
        (1, 9, 3, 7),
        "Synthetic Live",
        "Collective",
        60,
        "Acceso escalonado y controles de entrada.",
        ("20:30", "22:00", "23:30"),
    ),
    EventTemplate(
        "bridge-rock-fest",
        "Bridge Rock Fest",
        "Music",
        "Rock",
        "Alternative Rock",
        "concert",
        "alternativa",
        "exterior",
        "medio",
        (110, 170),
        (4, 9, 4, 7),
        "Night Grid",
        "Band",
        50,
        "Concierto con apertura de puertas y posible cola.",
        ("19:30", "21:00", "22:00"),
    ),
    EventTemplate(
        "mediterranean-pop-night",
        "Mediterranean Pop Night",
        "Music",
        "Pop",
        "Indie Pop",
        "concert",
        "luminosa",
        "exterior",
        "medio",
        (90, 150),
        (5, 8, 7, 8),
        "Local Demo",
        "Ensemble",
        45,
        "Plan popular con entrada general.",
        ("18:00", "20:30", "21:30"),
    ),
    EventTemplate(
        "night-market-jazz",
        "Night Market Jazz",
        "Music",
        "Jazz",
        "Fusion",
        "live_music",
        "relajada",
        "interior",
        "medio",
        (85, 130),
        (5, 7, 9, 8),
        "Stage Synthetic",
        "Quartet",
        35,
        "Aforo medio y acceso sencillo.",
        ("19:00", "20:30", "22:00"),
    ),
    EventTemplate(
        "invisible-city",
        "Invisible City",
        "Arts & Theatre",
        "Theatre",
        "Immersive",
        "performance",
        "experimental",
        "interior",
        "alto",
        (85, 125),
        (3, 7, 6, 8),
        "Stage Synthetic",
        "Company",
        45,
        "Experiencia con briefing previo.",
        ("18:00", "19:30", "21:00"),
    ),
    EventTemplate(
        "malasana-stand-up",
        "Malasana Stand-up",
        "Arts & Theatre",
        "Comedy",
        "Stand-up",
        "comedy",
        "divertida",
        "interior",
        "bajo",
        (70, 100),
        (2, 8, 5, 6),
        "Laugh Demo",
        "Comedians",
        25,
        "Entrada numerada y acceso sencillo.",
        ("19:30", "21:00", "22:30"),
    ),
    EventTemplate(
        "gran-via-musical-lab",
        "Gran Via Musical Lab",
        "Arts & Theatre",
        "Musical",
        "Contemporary",
        "musical",
        "emocional",
        "interior",
        "alto",
        (120, 170),
        (6, 8, 8, 9),
        "Stage Madrid Demo",
        "Cast",
        40,
        "Teatro con acceso por patio de butacas.",
        ("17:30", "20:00", "21:30"),
    ),
    EventTemplate(
        "urban-cinema-rooftop",
        "Urban Cinema Rooftop",
        "Film",
        "Sci-Fi",
        "Open Air Cinema",
        "cinema",
        "nostalgica",
        "exterior",
        "bajo",
        (110, 150),
        (6, 7, 8, 8),
        "Cinema al Fresco Demo",
        "Screening",
        30,
        "Butaca libre y acceso rapido.",
        ("20:30", "21:30", "22:00"),
    ),
    EventTemplate(
        "family-science-garden",
        "Family Science Garden",
        "Family",
        "Kids",
        "Science Workshop",
        "family_workshop",
        "didactica",
        "exterior",
        "bajo",
        (60, 95),
        (10, 7, 4, 8),
        "Family Lab",
        "Educators",
        20,
        "Actividad familiar con llegada flexible.",
        ("10:30", "11:30", "17:00"),
    ),
    EventTemplate(
        "circus-lights",
        "Circus Lights",
        "Family",
        "Circus",
        "Contemporary Circus",
        "family_show",
        "magica",
        "interior",
        "medio",
        (80, 120),
        (9, 8, 6, 8),
        "Family Stage",
        "Troupe",
        35,
        "Recomendable llegar antes por control de accesos.",
        ("12:00", "18:00", "19:30"),
    ),
    EventTemplate(
        "basket-evening",
        "Basket Evening",
        "Sports",
        "Basketball",
        "Friendly",
        "sports_match",
        "competitiva",
        "interior",
        "medio",
        (110, 150),
        (6, 9, 3, 7),
        "Synthetic Sports",
        "Club",
        50,
        "Acceso a grada y validacion de entrada.",
        ("18:00", "19:30", "21:00"),
    ),
    EventTemplate(
        "sunset-football",
        "Sunset Football",
        "Sports",
        "Football",
        "Summer Cup",
        "sports_match",
        "energia_alta",
        "exterior",
        "alto",
        (105, 140),
        (5, 10, 3, 8),
        "Synthetic Sports",
        "Club",
        75,
        "Evento de alta afluencia con accesos por zonas.",
        ("19:00", "20:30", "21:30"),
    ),
)


PRICE_RANGES = {
    "bajo": (8.0, 25.0),
    "medio": (24.0, 55.0),
    "alto": (50.0, 120.0),
}

TITLE_SUFFIXES = (
    "Local Edition",
    "Late Session",
    "Open Air",
    "Special Edition",
    "Summer Chapter",
    "Immersive Edition",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic events for Firestore and BigQuery catalog tables."
    )
    parser.add_argument("--count", type=int, default=100, help="Number of events to generate.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSONL output path.")
    parser.add_argument("--seed", type=int, default=20260509)
    parser.add_argument(
        "--start-date",
        type=lambda value: datetime.strptime(value, "%Y-%m-%d").date(),
        default=date.today() + timedelta(days=14),
    )
    parser.add_argument("--days", type=int, default=90, help="Date range from --start-date.")
    parser.add_argument("--id-prefix", default="evt-synth")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--table", default=DEFAULT_TABLE)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--upload-firestore", action="store_true")
    parser.add_argument("--upload-bigquery", action="store_true")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="For BigQuery, delete rows with the generated IDs before inserting.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    return SAFE_ID_RE.sub("-", value.lower()).strip("-")


def parse_clock(value: str) -> time:
    hours, minutes = value.split(":", 1)
    return time(int(hours), int(minutes))


def iso_utc(day: date, clock: str) -> str:
    local_dt = datetime.combine(day, parse_clock(clock), tzinfo=MADRID_TZ)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def franja_horaria(clock: str) -> str:
    hour = parse_clock(clock).hour
    if hour < 13:
        return "mañana"
    if hour < 20:
        return "tarde"
    return "noche"


def jitter(value: float, rng: random.Random, spread: float = 0.025) -> float:
    return round(value + rng.uniform(-spread, spread), 6)


def nearby_place(items: tuple[tuple[str, str], ...], rng: random.Random, place_type: str | None = None) -> dict[str, Any]:
    name, address = rng.choice(items)
    place = {
        "nombre": name,
        "direccion": address,
        "valoracion": round(rng.uniform(4.0, 4.8), 1),
        "precio": rng.choice(("€", "€€", "€€€")),
        "distancia_metros": rng.randint(120, 950),
    }
    if place_type:
        place["tipo"] = place_type
    return place


def price_range(price_band: str, rng: random.Random) -> tuple[float, float]:
    low, high = PRICE_RANGES[price_band]
    price_min = round(rng.uniform(low, (low + high) / 2), 2)
    price_max = round(rng.uniform(max(price_min + 4.0, (low + high) / 2), high), 2)
    return price_min, price_max


def venta_window(event_day: date, clock: str, rng: random.Random) -> tuple[str, str]:
    sale_start_day = event_day - timedelta(days=rng.randint(20, 75))
    sale_start = datetime.combine(sale_start_day, time(8, 0), tzinfo=timezone.utc)
    sale_end = datetime.fromisoformat(iso_utc(event_day, clock).replace("Z", "+00:00"))
    return (
        sale_start.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        sale_end.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )


def infer_rag_taxonomy(template: EventTemplate) -> tuple[str, str]:
    if template.segment == "Music":
        subcategory_by_genre = {
            "Electronic": "Dance/Electrónica",
            "Rock": "Indie/Alternativo",
            "Pop": "Pop/Rock",
            "Jazz": "Jazz/Blues",
        }
        return "Música", subcategory_by_genre.get(template.genre, "Festival")
    if template.segment == "Sports":
        subcategory_by_genre = {
            "Basketball": "Baloncesto",
            "Football": "Fútbol",
        }
        return "Deportes", subcategory_by_genre.get(template.genre, "Motor")
    if template.segment == "Arts & Theatre":
        subcategory_by_genre = {
            "Comedy": "Comedia",
            "Musical": "Musical",
            "Theatre": "Ballet/Danza",
        }
        return "Arte y Teatro", subcategory_by_genre.get(template.genre, "Comedia")
    if template.segment == "Family":
        subcategory_by_genre = {
            "Kids": "Actividades en familia",
            "Circus": "Circo",
        }
        return "Familia y otros", subcategory_by_genre.get(template.genre, "Actividades en familia")
    return "Familia y otros", "Visitas Guiadas/Exposiciones"


def synthetic_weather(day: date, city: City, rng: random.Random) -> dict[str, Any]:
    month = day.month
    seasonal_base = 15 + 9 * math.sin((month - 3) / 12 * 2 * math.pi)
    city_adjustment = {
        "Bilbao": -2.0,
        "Malaga": 3.0,
        "Sevilla": 4.0,
        "Valencia": 2.0,
        "Barcelona": 1.0,
        "Madrid": 0.0,
    }.get(city.name, 0.0)
    temp_max = round(seasonal_base + city_adjustment + rng.uniform(2.0, 8.0), 1)
    temp_min = round(temp_max - rng.uniform(5.0, 10.0), 1)
    rainy = rng.random() < (0.18 if city.name in {"Bilbao", "Barcelona"} else 0.10)
    code = rng.choice((61, 63, 80)) if rainy else rng.choice((0, 1, 2, 3))
    descriptions = {
        0: "Despejado",
        1: "Principalmente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        80: "Chubascos ligeros",
    }
    return {
        "temp_max": temp_max,
        "temp_min": temp_min,
        "precipitacion_mm": round(rng.uniform(0.2, 8.0), 1) if rainy else 0.0,
        "codigo_wmo": code,
        "descripcion": descriptions[code],
        "viento_max_kmh": round(rng.uniform(8.0, 28.0), 1),
    }


def generate_events(count: int, start_date: date, days: int, seed: int, id_prefix: str) -> list[dict[str, Any]]:
    if count < 1:
        raise ValueError("--count must be >= 1")
    if days < 1:
        raise ValueError("--days must be >= 1")

    rng = random.Random(seed)
    events: list[dict[str, Any]] = []

    for index in range(1, count + 1):
        template = TEMPLATES[(index - 1) % len(TEMPLATES)]
        city = CITIES[(index + rng.randrange(len(CITIES))) % len(CITIES)]
        venue_id, venue_name, venue_address = city.venues[(index - 1) % len(city.venues)]
        day = start_date + timedelta(days=(index - 1) % days)
        clock = template.time_slots[(index + rng.randrange(len(template.time_slots))) % len(template.time_slots)]
        suffix = TITLE_SUFFIXES[(index + rng.randrange(len(TITLE_SUFFIXES))) % len(TITLE_SUFFIXES)]
        occurrence = f"{day:%Y%m%d}-{clock.replace(':', '')}"
        event_id = f"{id_prefix}-{city.slug}-{template.slug}-{index:04d}-{occurrence}"
        artist_slug = slugify(template.title)
        venta_inicio, venta_fin = venta_window(day, clock, rng)
        categoria, subcategoria = infer_rag_taxonomy(template)

        event = {
            "id": event_id,
            "uuid_evento": str(uuid.uuid5(UUID_NAMESPACE, event_id)),
            "nombre": f"{template.title} - {suffix}",
            "url": f"https://example.com/events/{template.slug}-{city.slug}",
            "es_test": False,
            "fecha": day.isoformat(),
            "hora": f"{clock}:00",
            "fecha_utc": iso_utc(day, clock),
            "estado": "onsale",
            "venta_inicio": venta_inicio,
            "venta_fin": venta_fin,
            "segmento": template.segment,
            "genero": template.genre,
            "subgenero": template.subgenre,
            "recinto_id": venue_id,
            "recinto_nombre": venue_name,
            "ciudad": city.name,
            "direccion": venue_address,
            "codigo_postal": city.postal_code,
            "latitud": jitter(city.lat, rng),
            "longitud": jitter(city.lng, rng),
            "artista_id": f"art-synth-{artist_slug}",
            "artista_nombre": f"{template.title} {template.artist_suffix}",
            "artista_imagen": f"https://picsum.photos/seed/art-{artist_slug}-{city.slug}/400/400",
            "imagen_evento": f"https://picsum.photos/seed/{event_id}/1200/675",
            "promotor": template.promoter,
            "descripcion": (
                f"Evento sintetico de {template.genre} en {city.name} creado para "
                "enriquecer Firestore y BigQuery con datos de prueba realistas."
            ),
            "categoria": categoria,
            "subcategoria": subcategoria,
            "franja_horaria": franja_horaria(clock),
            "restaurantes_cercanos": [nearby_place(city.restaurants, rng)],
            "alojamientos_cercanos": [nearby_place(city.hotels, rng, place_type="hotel")],
            "antelacion_recomendada": {
                "minutos_antelacion": template.lead_minutes,
                "motivo": template.lead_reason,
            },
            "tiempo": synthetic_weather(day, city, rng),
            "contexto_rag": "",
            "embedding": [],
        }
        events.append(event)

    return events


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def chunks(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[start : start + size] for start in range(0, len(rows), size)]


def parse_timestamp(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if not re.match(r"^\d{4}-\d{2}-\d{2}T", value):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value


def firestore_document(row: dict[str, Any]) -> dict[str, Any]:
    document = {field: row[field] for field in FIRESTORE_EVENT_FIELDS if field in row}
    if "fecha_utc" in document:
        document["fecha_utc"] = parse_timestamp(document["fecha_utc"])
    return document


def upload_firestore(rows: list[dict[str, Any]], project_id: str, collection: str) -> None:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing Firebase dependency. Install backend/portal-api/requirements.txt "
            "or run this from an environment with firebase-admin available."
        ) from exc

    class EmulatorCredential(credentials.Base):
        def get_credential(self) -> Any:
            from google.oauth2.credentials import Credentials

            return Credentials(token="local-emulator-token")

    if not firebase_admin._apps:
        if os.environ.get("FIRESTORE_EMULATOR_HOST"):
            firebase_admin.initialize_app(EmulatorCredential(), {"projectId": project_id})
        else:
            firebase_admin.initialize_app(credentials.ApplicationDefault(), {"projectId": project_id})

    db = firestore.client()
    written = 0
    for batch_rows in chunks(rows, 450):
        batch = db.batch()
        for row in batch_rows:
            doc_ref = db.collection(collection).document(row["id"])
            batch.set(doc_ref, firestore_document(row), merge=True)
        batch.commit()
        written += len(batch_rows)

    print(f"Upserted {written} events into Firestore collection '{collection}'.")


def schema_field_names(fields: list[Any]) -> set[str]:
    return {field.name for field in fields}


def filter_for_schema(row: dict[str, Any], fields: list[Any]) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    for field in fields:
        if field.name not in row:
            continue
        value = row[field.name]
        if value is None or (isinstance(value, float) and math.isnan(value)):
            filtered[field.name] = None
        elif field.field_type == "RECORD" and field.fields and isinstance(value, dict):
            filtered[field.name] = filter_for_schema(value, list(field.fields))
        else:
            filtered[field.name] = value
    return filtered


def existing_bigquery_ids(client: Any, table_id: str, ids: list[str]) -> set[str]:
    if not ids:
        return set()
    from google.cloud import bigquery

    found: set[str] = set()
    for id_chunk in [ids[start : start + 1000] for start in range(0, len(ids), 1000)]:
        query = f"select id from `{table_id}` where id in unnest(@ids)"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("ids", "STRING", id_chunk)]
        )
        found.update(row["id"] for row in client.query(query, job_config=job_config).result())
    return found


def delete_bigquery_ids(client: Any, table_id: str, ids: list[str]) -> None:
    if not ids:
        return
    from google.cloud import bigquery

    for id_chunk in [ids[start : start + 1000] for start in range(0, len(ids), 1000)]:
        query = f"delete from `{table_id}` where id in unnest(@ids)"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("ids", "STRING", id_chunk)]
        )
        client.query(query, job_config=job_config).result()


def upload_bigquery(
    rows: list[dict[str, Any]],
    project_id: str,
    dataset: str,
    table: str,
    replace_existing: bool,
) -> None:
    try:
        from google.cloud import bigquery
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing BigQuery dependency. Install backend/portal-api/requirements.txt "
            "or run this from an environment with google-cloud-bigquery available."
        ) from exc

    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.{table}"
    table_obj = client.get_table(table_id)
    ids = [row["id"] for row in rows]

    existing = existing_bigquery_ids(client, table_id, ids)
    if existing and replace_existing:
        delete_bigquery_ids(client, table_id, sorted(existing))
        print(f"Deleted {len(existing)} existing BigQuery rows before reload.")
        existing = set()

    rows_to_load = [row for row in rows if row["id"] not in existing]
    skipped = len(rows) - len(rows_to_load)
    if not rows_to_load:
        print(f"No new rows to load into {table_id}; skipped {skipped} existing events.")
        return

    schema_names = schema_field_names(list(table_obj.schema))
    if "id" not in schema_names:
        raise RuntimeError(f"BigQuery table {table_id} does not expose required field 'id'.")

    bq_rows = [filter_for_schema(row, list(table_obj.schema)) for row in rows_to_load]
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ignore_unknown_values=True,
    )
    job = client.load_table_from_json(bq_rows, table_id, job_config=job_config)
    job.result()

    print(f"Loaded {len(bq_rows)} events into BigQuery table {table_id}.")
    if skipped:
        print(f"Skipped {skipped} events already present in BigQuery.")


def main() -> None:
    args = parse_args()
    rows = generate_events(
        count=args.count,
        start_date=args.start_date,
        days=args.days,
        seed=args.seed,
        id_prefix=args.id_prefix,
    )
    write_jsonl(args.output, rows)
    print(f"Wrote {len(rows)} synthetic events to {args.output}.")

    if args.upload_firestore:
        upload_firestore(rows, args.project_id, args.collection)

    if args.upload_bigquery:
        upload_bigquery(rows, args.project_id, args.dataset, args.table, args.replace_existing)


if __name__ == "__main__":
    main()
