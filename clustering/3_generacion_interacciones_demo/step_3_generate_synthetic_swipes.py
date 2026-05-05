from __future__ import annotations

import argparse
import csv
import json
import random
import uuid
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from unicodedata import combining, normalize

from demo_config import (
    DEFAULT_ANCHOR_DATE,
    DEFAULT_PROJECT_ID,
    DEFAULT_RUN_ID,
    DEFAULT_SEED,
    DEMO_USERS_PATH,
    GENERATION_SUMMARY_PATH,
    PERSONAS,
    REAL_EVENTS_PATH,
    SYNTHETIC_SWIPES_CSV_PATH,
    SYNTHETIC_SWIPES_JSONL_PATH,
    clamp,
    ensure_output_dir,
    normalize_event_taxonomy,
    price_midpoint,
    weighted_choice,
)


PREVIEW_FIELDNAMES = [
    "message_id",
    "user_id",
    "persona",
    "event_id",
    "direction",
    "swiped_at",
    "dwell_ms",
    "recommendation_context",
    "rank_position",
    "segmento",
    "genero",
    "ciudad",
    "banda_precio",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate v2 synthetic swipe rows against real catalog events."
    )
    parser.add_argument("--events-csv", type=Path, default=REAL_EVENTS_PATH)
    parser.add_argument("--users-csv", type=Path, default=DEMO_USERS_PATH)
    parser.add_argument("--preview-csv", type=Path, default=SYNTHETIC_SWIPES_CSV_PATH)
    parser.add_argument("--raw-jsonl", type=Path, default=SYNTHETIC_SWIPES_JSONL_PATH)
    parser.add_argument("--summary-json", type=Path, default=GENERATION_SUMMARY_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--anchor-date", default=DEFAULT_ANCHOR_DATE.isoformat())
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def normalize_text(value: str) -> str:
    decomposed = normalize("NFKD", value or "")
    without_accents = "".join(char for char in decomposed if not combining(char))
    return without_accents.lower().strip()


def enrich_events(events: list[dict[str, str]]) -> list[dict[str, str]]:
    enriched: list[dict[str, str]] = []
    for row in events:
        segmento, genero = normalize_event_taxonomy(row)
        enriched.append(
            {
                **row,
                "analytic_segmento": segmento,
                "analytic_genero": genero,
                "price_midpoint": str(price_midpoint(row)),
            }
        )
    return enriched


def choose_days_back(rng: random.Random) -> int:
    bucket = rng.random()
    if bucket < 0.42:
        return rng.randint(0, 6)
    if bucket < 0.78:
        return rng.randint(7, 29)
    return rng.randint(30, 89)


def random_swiped_at(anchor: date, rng: random.Random) -> datetime:
    anchor_dt = datetime.combine(anchor, time(12, 0), tzinfo=timezone.utc)
    days_back = choose_days_back(rng)
    seconds_back = rng.randint(0, 23 * 60 * 60)
    return anchor_dt - timedelta(days=days_back, seconds=seconds_back)


def event_affinity(
    event: dict[str, str],
    user: dict[str, str],
    persona_name: str,
    swiped_at: datetime,
) -> float:
    persona = next(persona for persona in PERSONAS if persona.name == persona_name)
    segment = event["analytic_segmento"]
    genre = event["analytic_genero"]
    city = event.get("ciudad") or ""
    home_city = user.get("home_city") or ""

    segment_score = persona.segment_weights.get(segment, 0.02)
    genre_score = persona.genre_weights.get(genre, 0.02)
    city_score = 1.0 if normalize_text(city) == normalize_text(home_city) else 0.0
    price_score = 1.0 - abs(float(event["price_midpoint"]) - persona.target_price) / persona.price_tolerance

    try:
        event_date = date.fromisoformat(event["fecha"])
        lead_days = (event_date - swiped_at.date()).days
    except ValueError:
        lead_days = persona.lead_mean_days

    lead_score = 1.0 - abs(lead_days - persona.lead_mean_days) / persona.lead_tolerance_days

    weighted = (
        0.30 * segment_score
        + 0.30 * genre_score
        + 0.16 * persona.city_loyalty * city_score
        + 0.14 * clamp(price_score, 0.0, 1.0)
        + 0.10 * clamp(lead_score, 0.0, 1.0)
    )
    return clamp(weighted + persona.exploration_factor * 0.04, 0.0, 1.0)


def pick_event_index(
    event_indexes: list[int],
    events: list[dict[str, str]],
    user: dict[str, str],
    persona_name: str,
    swiped_at: datetime,
    rng: random.Random,
) -> int:
    persona = next(persona for persona in PERSONAS if persona.name == persona_name)
    candidate_indexes = event_indexes

    if rng.random() >= persona.exploration_factor:
        target_segment = weighted_choice(
            list(persona.segment_weights.keys()),
            list(persona.segment_weights.values()),
            rng,
        )
        target_genre = weighted_choice(
            list(persona.genre_weights.keys()),
            list(persona.genre_weights.values()),
            rng,
        )
        matching_both = [
            index
            for index in event_indexes
            if events[index]["analytic_segmento"] == target_segment
            and events[index]["analytic_genero"] == target_genre
        ]
        matching_segment = [
            index for index in event_indexes if events[index]["analytic_segmento"] == target_segment
        ]
        matching_genre = [
            index for index in event_indexes if events[index]["analytic_genero"] == target_genre
        ]

        if matching_both:
            candidate_indexes = matching_both
        elif matching_segment:
            candidate_indexes = matching_segment
        elif matching_genre:
            candidate_indexes = matching_genre

    weights = [
        max(event_affinity(events[index], user, persona_name, swiped_at), 0.01)
        for index in candidate_indexes
    ]
    total = sum(weights)
    threshold = rng.random() * total
    cumulative = 0.0
    for event_index, weight in zip(candidate_indexes, weights):
        cumulative += weight
        if cumulative >= threshold:
            return event_index
    return candidate_indexes[-1]


def like_probability(affinity: float, persona_name: str) -> float:
    persona = next(persona for persona in PERSONAS if persona.name == persona_name)
    return clamp(0.10 + persona.like_bias + affinity * 0.82, 0.04, 0.92)


def dwell_ms(liked: bool, persona_name: str, rng: random.Random) -> int:
    persona = next(persona for persona in PERSONAS if persona.name == persona_name)
    mean = 8200 if liked else 2100
    sigma = 2300 if liked else 850
    value = rng.gauss(mean * persona.dwell_multiplier, sigma)
    return int(clamp(value, 350, 26000))


def rank_position(affinity: float, rng: random.Random) -> int:
    base = 1 + int((1.0 - affinity) * 18)
    noise = int(rng.expovariate(0.45))
    return int(clamp(base + noise, 1, 50))


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_message_id(run_id: str, user_id: str, event_id: str, swiped_at: datetime) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{run_id}:{user_id}:{event_id}:{iso_z(swiped_at)}"))


def build_payload(
    *,
    run_id: str,
    user: dict[str, str],
    event: dict[str, str],
    direction: str,
    swiped_at: datetime,
    dwell: int,
    rank: int,
    context: str,
    message_id: str,
) -> dict[str, Any]:
    event_id = event["id"]
    return {
        "schema_version": "2.0",
        "interaction_type": "swipe",
        "user_id": user["user_id"],
        "event_id": event_id,
        "direction": direction,
        "swiped_at": iso_z(swiped_at),
        "dwell_ms": dwell,
        "session_id": f"synthetic_demo_session_{user['user_id'][:8]}",
        "recommendation_context": context,
        "rank_position": rank,
        "recommendation_id": f"synthetic_demo_reco_{message_id[:12]}",
        "producer": {
            "surface": "synthetic_demo_generator",
            "client_version": "demo-v2",
        },
        "event_snapshot": {
            "event_id": event_id,
            "segmento": event["analytic_segmento"],
            "genero": event["analytic_genero"],
            "subgenero": event.get("subgenero") or event.get("subcategoria"),
            "ciudad": event.get("ciudad"),
            "recinto_id": event.get("recinto_id"),
            "fecha_evento": event.get("fecha"),
            "precio_min": None,
            "precio_max": None,
            "banda_precio": event.get("banda_precio"),
        },
        "data_origin": "synthetic_demo",
        "synthetic_run_id": run_id,
        "synthetic_persona": user["persona"],
    }


def build_raw_row(project_id: str, payload: dict[str, Any], message_id: str, publish_time: datetime) -> dict[str, Any]:
    attributes = {
        "user_id": payload["user_id"],
        "event_id": payload["event_id"],
        "schema_version": payload["schema_version"],
        "data_origin": payload["data_origin"],
        "synthetic_run_id": payload["synthetic_run_id"],
    }
    return {
        "subscription_name": f"projects/{project_id}/subscriptions/swipe-events-bq-synthetic-demo",
        "message_id": message_id,
        "publish_time": iso_z(publish_time),
        "data": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        "attributes": json.dumps(attributes, ensure_ascii=False, separators=(",", ":")),
    }


def main() -> None:
    args = parse_args()
    ensure_output_dir()
    rng = random.Random(args.seed)

    events = enrich_events(read_csv(args.events_csv))
    users = read_csv(args.users_csv)
    anchor = date.fromisoformat(args.anchor_date)

    if not events:
        raise RuntimeError(f"No events found in {args.events_csv}")
    if not users:
        raise RuntimeError(f"No users found in {args.users_csv}")

    raw_rows: list[dict[str, Any]] = []
    preview_rows: list[dict[str, Any]] = []
    segment_counter: Counter[str] = Counter()
    genre_counter: Counter[str] = Counter()
    persona_counter: Counter[str] = Counter()
    right_counter: Counter[str] = Counter()

    for user in users:
        persona_name = user["persona"]
        available_indexes = list(range(len(events)))
        planned_swipes = min(int(user["planned_swipes"]), len(available_indexes))

        for _ in range(planned_swipes):
            swiped_at = random_swiped_at(anchor, rng)
            event_index = pick_event_index(available_indexes, events, user, persona_name, swiped_at, rng)
            available_indexes.remove(event_index)
            event = events[event_index]

            affinity = event_affinity(event, user, persona_name, swiped_at)
            liked = rng.random() < like_probability(affinity, persona_name)
            direction = "right" if liked else "left"
            dwell = dwell_ms(liked, persona_name, rng)
            rank = rank_position(affinity, rng)
            context = "chat" if rng.random() < float(user["chat_share"]) else "quick_match"
            message_id = build_message_id(args.run_id, user["user_id"], event["id"], swiped_at)
            publish_time = swiped_at + timedelta(seconds=rng.randint(1, 240))

            payload = build_payload(
                run_id=args.run_id,
                user=user,
                event=event,
                direction=direction,
                swiped_at=swiped_at,
                dwell=dwell,
                rank=rank,
                context=context,
                message_id=message_id,
            )
            raw_rows.append(build_raw_row(args.project_id, payload, message_id, publish_time))
            preview_rows.append(
                {
                    "message_id": message_id,
                    "user_id": user["user_id"],
                    "persona": persona_name,
                    "event_id": event["id"],
                    "direction": direction,
                    "swiped_at": iso_z(swiped_at),
                    "dwell_ms": dwell,
                    "recommendation_context": context,
                    "rank_position": rank,
                    "segmento": event["analytic_segmento"],
                    "genero": event["analytic_genero"],
                    "ciudad": event.get("ciudad"),
                    "banda_precio": event.get("banda_precio"),
                }
            )

            persona_counter[persona_name] += 1
            segment_counter[event["analytic_segmento"]] += 1
            genre_counter[event["analytic_genero"]] += 1
            right_counter[direction] += 1

    args.preview_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.preview_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PREVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(preview_rows)

    with args.raw_jsonl.open("w", encoding="utf-8") as file:
        for row in raw_rows:
            file.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    summary = {
        "run_id": args.run_id,
        "users": len(users),
        "events": len(events),
        "synthetic_swipes": len(raw_rows),
        "right_swipe_rate": round(right_counter["right"] / max(1, len(raw_rows)), 4),
        "personas": dict(sorted(persona_counter.items())),
        "segments": dict(sorted(segment_counter.items())),
        "genres": dict(sorted(genre_counter.items())),
        "preview_csv": str(args.preview_csv),
        "raw_jsonl": str(args.raw_jsonl),
    }
    args.summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Generated {len(raw_rows)} synthetic v2 swipes")
    print(f"Preview CSV: {args.preview_csv}")
    print(f"Raw BigQuery JSONL: {args.raw_jsonl}")
    print(f"Summary JSON: {args.summary_json}")


if __name__ == "__main__":
    main()
