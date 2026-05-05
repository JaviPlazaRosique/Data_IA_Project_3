from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

REAL_EVENTS_PATH = OUTPUT_DIR / "real_events.csv"
DEMO_USERS_PATH = OUTPUT_DIR / "demo_users.csv"
SYNTHETIC_SWIPES_CSV_PATH = OUTPUT_DIR / "synthetic_swipes_preview.csv"
SYNTHETIC_SWIPES_JSONL_PATH = OUTPUT_DIR / "synthetic_swipes_raw_rows.jsonl"
GENERATION_SUMMARY_PATH = OUTPUT_DIR / "generation_summary.json"
VALIDATION_SUMMARY_PATH = OUTPUT_DIR / "validation_summary.json"

DEFAULT_PROJECT_ID = "project3grupo3"
DEFAULT_DATASET = "recomendacion_planes"
DEFAULT_SWIPES_TABLE = "swipes_raw"
DEFAULT_EVENTS_TABLE = "eventos"
DEFAULT_ANCHOR_DATE = date(2026, 5, 2)
DEFAULT_SEED = 20260502
DEFAULT_RUN_ID = "synthetic_demo_20260502"

PRICE_BAND_MIDPOINTS = {
    "bajo": 15.0,
    "medio": 45.0,
    "alto": 90.0,
}


@dataclass(frozen=True)
class PersonaConfig:
    name: str
    user_count: int
    swipe_range: tuple[int, int]
    preferred_cities: tuple[str, ...]
    segment_weights: dict[str, float]
    genre_weights: dict[str, float]
    target_price: float
    price_tolerance: float
    lead_mean_days: float
    lead_tolerance_days: float
    city_loyalty: float
    chat_share: float
    dwell_multiplier: float
    like_bias: float
    exploration_factor: float


PERSONAS = [
    PersonaConfig(
        name="music_pop_rock_local",
        user_count=35,
        swipe_range=(60, 90),
        preferred_cities=("Madrid", "Barcelona", "Valencia"),
        segment_weights={"Music": 0.78, "Arts_Theatre": 0.10, "Family": 0.06, "Sports": 0.06},
        genre_weights={"Rock": 0.42, "Pop": 0.34, "Comedy": 0.08, "Exhibition": 0.08, "Basketball": 0.08},
        target_price=52.0,
        price_tolerance=32.0,
        lead_mean_days=16.0,
        lead_tolerance_days=12.0,
        city_loyalty=0.82,
        chat_share=0.12,
        dwell_multiplier=1.04,
        like_bias=0.10,
        exploration_factor=0.16,
    ),
    PersonaConfig(
        name="flamenco_world_madrid",
        user_count=28,
        swipe_range=(55, 85),
        preferred_cities=("Madrid", "Malaga", "Jerez de la Frontera"),
        segment_weights={"Music": 0.76, "Arts_Theatre": 0.12, "Family": 0.08, "Sports": 0.04},
        genre_weights={"Pop": 0.52, "Rock": 0.16, "Theatre": 0.12, "Comedy": 0.10, "Exhibition": 0.10},
        target_price=70.0,
        price_tolerance=38.0,
        lead_mean_days=20.0,
        lead_tolerance_days=14.0,
        city_loyalty=0.74,
        chat_share=0.18,
        dwell_multiplier=1.08,
        like_bias=0.08,
        exploration_factor=0.20,
    ),
    PersonaConfig(
        name="culture_theatre_explorer",
        user_count=34,
        swipe_range=(58, 88),
        preferred_cities=("Madrid", "Malaga", "Barcelona"),
        segment_weights={"Arts_Theatre": 0.72, "Music": 0.12, "Family": 0.10, "Sports": 0.06},
        genre_weights={"Comedy": 0.28, "Musical": 0.26, "Theatre": 0.22, "Classical": 0.12, "Exhibition": 0.12},
        target_price=45.0,
        price_tolerance=26.0,
        lead_mean_days=13.0,
        lead_tolerance_days=10.0,
        city_loyalty=0.78,
        chat_share=0.28,
        dwell_multiplier=1.12,
        like_bias=0.09,
        exploration_factor=0.18,
    ),
    PersonaConfig(
        name="family_weekend_exhibition",
        user_count=35,
        swipe_range=(55, 82),
        preferred_cities=("Barcelona", "Madrid", "Valencia"),
        segment_weights={"Family": 0.72, "Arts_Theatre": 0.16, "Music": 0.08, "Sports": 0.04},
        genre_weights={"Exhibition": 0.38, "Kids": 0.28, "Circus": 0.16, "Musical": 0.10, "Pop": 0.08},
        target_price=42.0,
        price_tolerance=24.0,
        lead_mean_days=10.0,
        lead_tolerance_days=8.0,
        city_loyalty=0.90,
        chat_share=0.10,
        dwell_multiplier=0.98,
        like_bias=0.12,
        exploration_factor=0.12,
    ),
    PersonaConfig(
        name="sports_basketball_traveler",
        user_count=20,
        swipe_range=(45, 75),
        preferred_cities=("Palma de Mallorca", "Madrid", "Barcelona"),
        segment_weights={"Sports": 0.78, "Music": 0.10, "Arts_Theatre": 0.06, "Family": 0.06},
        genre_weights={"Basketball": 0.62, "Rock": 0.12, "Pop": 0.10, "Comedy": 0.08, "Exhibition": 0.08},
        target_price=80.0,
        price_tolerance=42.0,
        lead_mean_days=18.0,
        lead_tolerance_days=14.0,
        city_loyalty=0.46,
        chat_share=0.10,
        dwell_multiplier=0.94,
        like_bias=0.06,
        exploration_factor=0.22,
    ),
    PersonaConfig(
        name="broad_discovery_flexible",
        user_count=32,
        swipe_range=(65, 95),
        preferred_cities=("Madrid", "Barcelona", "Malaga", "Valencia"),
        segment_weights={"Music": 0.34, "Arts_Theatre": 0.28, "Family": 0.24, "Sports": 0.14},
        genre_weights={
            "Rock": 0.13,
            "Pop": 0.13,
            "Comedy": 0.13,
            "Musical": 0.10,
            "Theatre": 0.10,
            "Exhibition": 0.16,
            "Kids": 0.10,
            "Circus": 0.05,
            "Basketball": 0.10,
        },
        target_price=55.0,
        price_tolerance=46.0,
        lead_mean_days=14.0,
        lead_tolerance_days=14.0,
        city_loyalty=0.60,
        chat_share=0.20,
        dwell_multiplier=1.02,
        like_bias=0.05,
        exploration_factor=0.34,
    ),
]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def weighted_choice(items: list[Any], weights: list[float], rng: Any) -> Any:
    adjusted = [max(float(weight), 0.0001) for weight in weights]
    total = sum(adjusted)
    threshold = rng.random() * total
    cumulative = 0.0
    for item, weight in zip(items, adjusted):
        cumulative += weight
        if cumulative >= threshold:
            return item
    return items[-1]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalize_event_taxonomy(row: dict[str, str]) -> tuple[str, str]:
    """Map catalog labels into the analytical taxonomy used by clustering features."""
    raw_segment = (row.get("segmento") or "").strip()
    raw_genre = (row.get("genero") or "").strip()
    raw_subgenre = (row.get("subgenero") or "").strip()
    category = (row.get("categoria") or "").strip()
    subcategory = (row.get("subcategoria") or "").strip()

    text = " ".join([raw_segment, raw_genre, raw_subgenre, category, subcategory]).lower()

    if "deportes" in text or raw_segment == "Sports":
        return "Sports", "Basketball" if "basket" in text or "baloncesto" in text else "Basketball"

    if "familia" in text or raw_segment == "Miscellaneous" or raw_genre == "Family":
        if "circo" in text:
            return "Family", "Circus"
        if "parque" in text or "kids" in text or "infantil" in text:
            return "Family", "Kids"
        return "Family", "Exhibition"

    if "arte y teatro" in text or "arts & theatre" in text or raw_segment == "Arts & Theatre":
        if "comedia" in text or "stand" in text:
            return "Arts_Theatre", "Comedy"
        if "musical" in text:
            return "Arts_Theatre", "Musical"
        if "ballet" in text or "danza" in text or "cultural" in text:
            return "Arts_Theatre", "Theatre"
        return "Arts_Theatre", "Theatre"

    if "musica" in text or "música" in text or raw_segment == "Music":
        if raw_genre in {"Rock", "Alternative"} or "rock" in text or "indie" in text:
            return "Music", "Rock"
        if raw_genre == "Pop" or "pop" in text or "latin" in text or "flamenco" in text or "world" in text:
            return "Music", "Pop"
        return "Music", "Pop"

    return "Arts_Theatre", "Theatre"


def price_midpoint(row: dict[str, str]) -> float:
    return PRICE_BAND_MIDPOINTS.get((row.get("banda_precio") or "").lower(), 45.0)
