from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USERS_PATH = DATA_DIR / "synthetic_users.csv"
EVENTS_PATH = DATA_DIR / "synthetic_events_catalog.csv"
INTERACTIONS_PATH = DATA_DIR / "synthetic_fct_swipes.csv"

ANCHOR_DATE = date(2026, 4, 30)
RANDOM_SEED = 20260430

SEGMENT_DEFINITIONS: dict[str, dict[str, list[str]]] = {
    "Music": {
        "Rock": ["Indie_Rock", "Alternative_Rock"],
        "Pop": ["Mainstream_Pop", "Latin_Pop"],
        "Electronic": ["House", "Techno"],
        "Urban": ["Trap", "Hip_Hop"],
    },
    "Sports": {
        "Football": ["La_Liga", "International_Friendly"],
        "Basketball": ["ACB", "EuroLeague"],
        "Tennis": ["ATP", "Exhibition"],
    },
    "Arts_Theatre": {
        "Theatre": ["Drama", "Contemporary"],
        "Musical": ["Broadway", "Local_Musical"],
        "Comedy": ["Stand_Up", "Improvised"],
        "Classical": ["Symphonic", "Chamber"],
    },
    "Family": {
        "Kids": ["Interactive_Show", "Storytelling"],
        "Circus": ["Acrobatic", "Family_Circus"],
        "Exhibition": ["Science", "Immersive"],
    },
}

CITIES = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Malaga"]
CITY_VENUES = {
    "Madrid": ["Madrid_Arena", "River_Stage", "Centro_Cultural", "Distrito_Club"],
    "Barcelona": ["Forum_BCN", "Montjuic_Hall", "Raval_Stage", "Diagonal_Arena"],
    "Valencia": ["Turia_Live", "Mediterraneo_Hall", "Marina_Stage", "Ciutat_Arena"],
    "Sevilla": ["Cartuja_Live", "Triana_Hall", "Guadalquivir_Stage", "Alameda_Club"],
    "Bilbao": ["Nervion_Hall", "Abando_Arena", "Bilbao_Live", "Arenal_Stage"],
    "Malaga": ["Costa_Del_Sol_Live", "Malaga_Forum", "Muelle_Club", "Alcazaba_Hall"],
}

GENRE_BASE_PRICE = {
    "Rock": 46,
    "Pop": 57,
    "Electronic": 68,
    "Urban": 52,
    "Football": 98,
    "Basketball": 78,
    "Tennis": 88,
    "Theatre": 41,
    "Musical": 62,
    "Comedy": 34,
    "Classical": 48,
    "Kids": 26,
    "Circus": 32,
    "Exhibition": 24,
}


@dataclass(frozen=True)
class PersonaConfig:
    name: str
    user_count: int
    activity_range: tuple[int, int]
    segment_weights: dict[str, float]
    genre_weights: dict[str, float]
    target_price: float
    price_tolerance: float
    lead_mean: float
    lead_tolerance: float
    city_loyalty: float
    context_chat_share: float
    dwell_multiplier: float
    exploration_factor: float
    like_bias: float


PERSONAS = [
    PersonaConfig(
        name="music_local_budget",
        user_count=40,
        activity_range=(85, 140),
        segment_weights={"Music": 0.72, "Arts_Theatre": 0.14, "Family": 0.08, "Sports": 0.06},
        genre_weights={
            "Rock": 0.38,
            "Pop": 0.24,
            "Electronic": 0.12,
            "Urban": 0.08,
            "Theatre": 0.08,
            "Comedy": 0.05,
            "Exhibition": 0.05,
        },
        target_price=40.0,
        price_tolerance=28.0,
        lead_mean=20.0,
        lead_tolerance=14.0,
        city_loyalty=0.88,
        context_chat_share=0.12,
        dwell_multiplier=1.00,
        exploration_factor=0.16,
        like_bias=0.10,
    ),
    PersonaConfig(
        name="sports_travel_premium",
        user_count=38,
        activity_range=(70, 125),
        segment_weights={"Sports": 0.74, "Music": 0.12, "Arts_Theatre": 0.08, "Family": 0.06},
        genre_weights={
            "Football": 0.40,
            "Basketball": 0.30,
            "Tennis": 0.18,
            "Rock": 0.05,
            "Comedy": 0.04,
            "Exhibition": 0.03,
        },
        target_price=90.0,
        price_tolerance=44.0,
        lead_mean=36.0,
        lead_tolerance=22.0,
        city_loyalty=0.56,
        context_chat_share=0.10,
        dwell_multiplier=0.92,
        exploration_factor=0.20,
        like_bias=0.06,
    ),
    PersonaConfig(
        name="arts_culture_local",
        user_count=38,
        activity_range=(68, 118),
        segment_weights={"Arts_Theatre": 0.75, "Music": 0.14, "Family": 0.07, "Sports": 0.04},
        genre_weights={
            "Theatre": 0.30,
            "Musical": 0.26,
            "Comedy": 0.18,
            "Classical": 0.16,
            "Rock": 0.05,
            "Exhibition": 0.05,
        },
        target_price=46.0,
        price_tolerance=30.0,
        lead_mean=28.0,
        lead_tolerance=16.0,
        city_loyalty=0.82,
        context_chat_share=0.26,
        dwell_multiplier=1.10,
        exploration_factor=0.18,
        like_bias=0.09,
    ),
    PersonaConfig(
        name="family_weekend_local",
        user_count=40,
        activity_range=(60, 105),
        segment_weights={"Family": 0.63, "Arts_Theatre": 0.20, "Music": 0.10, "Sports": 0.07},
        genre_weights={
            "Kids": 0.28,
            "Circus": 0.22,
            "Exhibition": 0.18,
            "Musical": 0.12,
            "Comedy": 0.12,
            "Pop": 0.08,
        },
        target_price=32.0,
        price_tolerance=18.0,
        lead_mean=18.0,
        lead_tolerance=10.0,
        city_loyalty=0.92,
        context_chat_share=0.08,
        dwell_multiplier=0.96,
        exploration_factor=0.12,
        like_bias=0.12,
    ),
    PersonaConfig(
        name="electronic_night_explorer",
        user_count=42,
        activity_range=(90, 150),
        segment_weights={"Music": 0.68, "Arts_Theatre": 0.14, "Sports": 0.10, "Family": 0.08},
        genre_weights={
            "Electronic": 0.36,
            "Urban": 0.26,
            "Pop": 0.16,
            "Rock": 0.10,
            "Comedy": 0.06,
            "Basketball": 0.06,
        },
        target_price=68.0,
        price_tolerance=34.0,
        lead_mean=30.0,
        lead_tolerance=18.0,
        city_loyalty=0.48,
        context_chat_share=0.20,
        dwell_multiplier=1.06,
        exploration_factor=0.28,
        like_bias=0.08,
    ),
    PersonaConfig(
        name="broad_discovery_flexible",
        user_count=42,
        activity_range=(75, 130),
        segment_weights={"Music": 0.34, "Arts_Theatre": 0.28, "Sports": 0.20, "Family": 0.18},
        genre_weights={
            "Rock": 0.12,
            "Pop": 0.10,
            "Electronic": 0.07,
            "Urban": 0.06,
            "Football": 0.09,
            "Basketball": 0.08,
            "Tennis": 0.06,
            "Theatre": 0.12,
            "Musical": 0.08,
            "Comedy": 0.09,
            "Classical": 0.05,
            "Kids": 0.03,
            "Circus": 0.02,
            "Exhibition": 0.03,
        },
        target_price=56.0,
        price_tolerance=42.0,
        lead_mean=24.0,
        lead_tolerance=18.0,
        city_loyalty=0.64,
        context_chat_share=0.18,
        dwell_multiplier=1.02,
        exploration_factor=0.34,
        like_bias=0.05,
    ),
]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def weighted_choice(items: list[Any], weights: list[float], rng: random.Random) -> Any:
    adjusted = [max(weight, 0.0001) for weight in weights]
    total = sum(adjusted)
    threshold = rng.random() * total
    cumulative = 0.0
    for item, weight in zip(items, adjusted):
        cumulative += weight
        if cumulative >= threshold:
            return item
    return items[-1]


def slugify(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "_")


def serialize_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 6)
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Cannot write empty CSV: {path}")
    keys = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: serialize_value(row.get(key, "")) for key in keys})


def build_events(rng: random.Random) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    start_date = ANCHOR_DATE - timedelta(days=110)
    event_counter = 1
    for city in CITIES:
        venues = CITY_VENUES[city]
        for segment, genres in SEGMENT_DEFINITIONS.items():
            for genre, subgenres in genres.items():
                for subgenre in subgenres:
                    for slot in range(8):
                        day_offset = int(slot * 32 + rng.randint(-4, 4))
                        event_date = start_date + timedelta(days=day_offset)
                        event_date = min(max(event_date, start_date), ANCHOR_DATE + timedelta(days=120))
                        price_mid = GENRE_BASE_PRICE[genre] + rng.randint(-12, 12)
                        price_band = rng.randint(6, 18)
                        price_min = max(8, price_mid - price_band)
                        price_max = price_mid + price_band
                        venue_index = (slot + event_counter) % len(venues)
                        venue_name = venues[venue_index]
                        venue_id = f"{slugify(city)}_{slugify(venue_name)}"
                        events.append(
                            {
                                "event_id": f"evt_{event_counter:05d}",
                                "event_name": f"{genre}_{subgenre}_{city}_{slot + 1}",
                                "segmento": segment,
                                "genero": genre,
                                "subgenero": subgenre,
                                "ciudad": city,
                                "recinto_id": venue_id,
                                "recinto_nombre": venue_name,
                                "precio_min": float(price_min),
                                "precio_max": float(price_max),
                                "fecha_evento": event_date,
                            }
                        )
                        event_counter += 1
    return events


def build_users(rng: random.Random) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    user_counter = 1
    for persona in PERSONAS:
        for _ in range(persona.user_count):
            home_city = weighted_choice(CITIES, [1.0] * len(CITIES), rng)
            activity_target = rng.randint(*persona.activity_range)
            users.append(
                {
                    "user_id": f"user_{user_counter:04d}",
                    "home_city": home_city,
                    "synthetic_persona": persona.name,
                    "target_activity": activity_target,
                    "target_price": persona.target_price + rng.randint(-8, 8),
                    "price_tolerance": clamp(persona.price_tolerance + rng.randint(-5, 5), 12.0, 55.0),
                    "lead_mean": clamp(persona.lead_mean + rng.randint(-5, 5), 8.0, 50.0),
                    "lead_tolerance": clamp(persona.lead_tolerance + rng.randint(-4, 4), 6.0, 28.0),
                    "city_loyalty": clamp(persona.city_loyalty + rng.uniform(-0.06, 0.06), 0.35, 0.96),
                    "context_chat_share": clamp(persona.context_chat_share + rng.uniform(-0.04, 0.04), 0.02, 0.40),
                    "dwell_multiplier": clamp(persona.dwell_multiplier + rng.uniform(-0.08, 0.08), 0.80, 1.25),
                    "exploration_factor": clamp(persona.exploration_factor + rng.uniform(-0.05, 0.05), 0.08, 0.40),
                    "like_bias": persona.like_bias + rng.uniform(-0.03, 0.03),
                }
            )
            user_counter += 1
    return users


def persona_by_name(name: str) -> PersonaConfig:
    for persona in PERSONAS:
        if persona.name == name:
            return persona
    raise KeyError(name)


def sample_valid_events(
    events: list[dict[str, Any]],
    swipe_date: date,
    seen_events: set[str],
    rng: random.Random,
    sample_size: int = 40,
) -> list[tuple[dict[str, Any], int]]:
    candidates: list[tuple[dict[str, Any], int]] = []
    attempts = 0
    while len(candidates) < sample_size and attempts < sample_size * 30:
        event = events[rng.randrange(len(events))]
        attempts += 1
        if event["event_id"] in seen_events:
            continue
        days_until = (event["fecha_evento"] - swipe_date).days
        if 1 <= days_until <= 120:
            candidates.append((event, days_until))
    if candidates:
        return candidates
    fallback: list[tuple[dict[str, Any], int]] = []
    for event in events:
        days_until = (event["fecha_evento"] - swipe_date).days
        if 1 <= days_until <= 120:
            fallback.append((event, days_until))
            if len(fallback) >= sample_size:
                break
    return fallback


def preference_score(
    persona: PersonaConfig,
    user: dict[str, Any],
    event: dict[str, Any],
    days_until_event: int,
) -> float:
    segment_pref = persona.segment_weights.get(event["segmento"], 0.02)
    genre_pref = persona.genre_weights.get(event["genero"], 0.01)
    price_mid = (event["precio_min"] + event["precio_max"]) / 2.0
    price_fit = 1.0 - clamp(abs(price_mid - float(user["target_price"])) / float(user["price_tolerance"]), 0.0, 2.0) / 2.0
    lead_fit = 1.0 - clamp(abs(days_until_event - float(user["lead_mean"])) / float(user["lead_tolerance"]), 0.0, 2.0) / 2.0
    city_fit = float(user["city_loyalty"]) if event["ciudad"] == user["home_city"] else (1.0 - float(user["city_loyalty"]))
    exploration_bonus = float(user["exploration_factor"]) * 0.2
    return (
        0.40
        + 1.60 * segment_pref
        + 1.20 * genre_pref
        + 0.70 * price_fit
        + 0.55 * lead_fit
        + 0.55 * city_fit
        + exploration_bonus
    )


def like_probability(
    persona: PersonaConfig,
    user: dict[str, Any],
    event: dict[str, Any],
    days_until_event: int,
    context: str,
) -> float:
    score = preference_score(persona, user, event, days_until_event)
    context_bonus = 0.08 if context == "chat" and persona.name in {"arts_culture_local", "broad_discovery_flexible"} else 0.0
    noise_adjustment = 0.10 * float(user["exploration_factor"])
    raw = -2.45 + score + float(user["like_bias"]) + context_bonus + noise_adjustment
    probability = 1.0 / (1.0 + math.exp(-raw))
    return clamp(probability, 0.03, 0.95)


def build_interactions(
    users: list[dict[str, Any]],
    events: list[dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    interactions: list[dict[str, Any]] = []
    interaction_counter = 1
    for user in users:
        persona = persona_by_name(str(user["synthetic_persona"]))
        seen_events: set[str] = set()
        session_counter = 1
        target_interactions = int(user["target_activity"])
        for swipe_index in range(target_interactions):
            days_ago = int((rng.random() ** 1.6) * 119)
            swipe_date = ANCHOR_DATE - timedelta(days=days_ago)
            hour = rng.randint(9, 23)
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            event_timestamp = datetime.combine(swipe_date, time(hour, minute, second), tzinfo=timezone.utc)
            candidates = sample_valid_events(events, swipe_date, seen_events, rng)
            if not candidates:
                continue
            candidate_events = [item[0] for item in candidates]
            weights = [preference_score(persona, user, item[0], item[1]) for item in candidates]
            chosen_event = weighted_choice(candidate_events, weights, rng)
            days_until_event = (chosen_event["fecha_evento"] - swipe_date).days
            seen_events.add(str(chosen_event["event_id"]))
            context = "chat" if rng.random() < float(user["context_chat_share"]) else "swipe"
            liked = rng.random() < like_probability(persona, user, chosen_event, days_until_event, context)
            dwell_base = rng.randint(2500, 9000) if liked else rng.randint(350, 2800)
            dwell_ms = int(dwell_base * float(user["dwell_multiplier"]))
            if swipe_index % 6 == 0:
                session_counter += 1
            interactions.append(
                {
                    "interaction_id": f"int_{interaction_counter:07d}",
                    "event_timestamp": event_timestamp,
                    "user_id": user["user_id"],
                    "session_id": f"{user['user_id']}_session_{session_counter:03d}",
                    "event_id": chosen_event["event_id"],
                    "interaction_type": "swipe",
                    "swipe_direction": "right" if liked else "left",
                    "liked": liked,
                    "recommendation_context": context,
                    "segmento": chosen_event["segmento"],
                    "genero": chosen_event["genero"],
                    "subgenero": chosen_event["subgenero"],
                    "ciudad": chosen_event["ciudad"],
                    "precio_min": chosen_event["precio_min"],
                    "precio_max": chosen_event["precio_max"],
                    "fecha_evento": chosen_event["fecha_evento"],
                    "recinto_id": chosen_event["recinto_id"],
                    "ingestion_timestamp": event_timestamp + timedelta(minutes=rng.randint(1, 60)),
                    "dwell_ms": dwell_ms,
                    "home_city": user["home_city"],
                    "synthetic_persona": user["synthetic_persona"],
                    "days_until_event": days_until_event,
                    "price_mid": round((chosen_event["precio_min"] + chosen_event["precio_max"]) / 2.0, 2),
                }
            )
            interaction_counter += 1
    interactions.sort(key=lambda row: (row["event_timestamp"], row["interaction_id"]))
    return interactions


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RANDOM_SEED)
    users = build_users(rng)
    events = build_events(rng)
    interactions = build_interactions(users, events, rng)
    write_csv(USERS_PATH, users)
    write_csv(EVENTS_PATH, events)
    write_csv(INTERACTIONS_PATH, interactions)
    print("Step 1 completed: synthetic data generated.")
    print(f"Users: {len(users)}")
    print(f"Events: {len(events)}")
    print(f"Interactions: {len(interactions)}")
    print(f"Data path: {INTERACTIONS_PATH}")


if __name__ == "__main__":
    main()
