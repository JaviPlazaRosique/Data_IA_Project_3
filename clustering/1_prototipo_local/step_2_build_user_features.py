from __future__ import annotations

import csv
import json
import statistics
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

USERS_PATH = DATA_DIR / "synthetic_users.csv"
INTERACTIONS_PATH = DATA_DIR / "synthetic_fct_swipes.csv"
USER_FEATURES_PATH = OUTPUT_DIR / "user_features.csv"
USER_FEATURES_METADATA_PATH = ARTIFACTS_DIR / "user_features_metadata.json"

ANCHOR_DATE = date(2026, 4, 30)
ANCHOR_DATETIME = datetime.combine(ANCHOR_DATE, time(23, 59, 59), tzinfo=timezone.utc)
MIN_SWIPES_30D = 8
MIN_SWIPES_90D = 24

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

SEGMENT_NAMES = list(SEGMENT_DEFINITIONS.keys())
GENRE_NAMES = [
    genre
    for genres in SEGMENT_DEFINITIONS.values()
    for genre in genres.keys()
]


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def mean_or_zero(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def median_or_zero(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.lower() == "true"


def load_users() -> list[dict[str, Any]]:
    rows = read_csv_rows(USERS_PATH)
    users: list[dict[str, Any]] = []
    for row in rows:
        users.append(
            {
                "user_id": row["user_id"],
                "home_city": row["home_city"],
                "synthetic_persona": row["synthetic_persona"],
            }
        )
    return users


def load_interactions() -> list[dict[str, Any]]:
    rows = read_csv_rows(INTERACTIONS_PATH)
    interactions: list[dict[str, Any]] = []
    for row in rows:
        interactions.append(
            {
                **row,
                "event_timestamp": datetime.fromisoformat(row["event_timestamp"]),
                "liked": parse_bool(row["liked"]),
                "precio_min": float(row["precio_min"]),
                "precio_max": float(row["precio_max"]),
                "fecha_evento": date.fromisoformat(row["fecha_evento"]),
                "ingestion_timestamp": datetime.fromisoformat(row["ingestion_timestamp"]),
                "dwell_ms": int(row["dwell_ms"]),
                "days_until_event": int(row["days_until_event"]),
                "price_mid": float(row["price_mid"]),
            }
        )
    return interactions


def build_feature_row(
    user: dict[str, Any],
    user_rows: list[dict[str, Any]],
    window_days: int,
) -> dict[str, float]:
    window_start = ANCHOR_DATETIME - timedelta(days=window_days - 1)
    window_rows = [row for row in user_rows if row["event_timestamp"] >= window_start]
    liked_rows = [row for row in window_rows if row["liked"]]
    disliked_rows = [row for row in window_rows if not row["liked"]]
    total_swipes = len(window_rows)
    total_right_swipes = len(liked_rows)
    suffix = f"_{window_days}d"
    feature_row: dict[str, float] = {}

    feature_row[f"total_swipes{suffix}"] = float(total_swipes)
    feature_row[f"total_right_swipes{suffix}"] = float(total_right_swipes)
    feature_row[f"right_swipe_rate{suffix}"] = safe_div(total_right_swipes, total_swipes)
    feature_row[f"avg_dwell_ms{suffix}"] = mean_or_zero([float(row["dwell_ms"]) for row in window_rows])
    feature_row[f"avg_right_dwell_ms{suffix}"] = mean_or_zero([float(row["dwell_ms"]) for row in liked_rows])
    feature_row[f"distinct_segments_liked{suffix}"] = float(len({row["segmento"] for row in liked_rows}))
    feature_row[f"distinct_genres_liked{suffix}"] = float(len({row["genero"] for row in liked_rows}))
    feature_row[f"distinct_cities_liked{suffix}"] = float(len({row["ciudad"] for row in liked_rows}))

    local_likes = [row for row in liked_rows if row["ciudad"] == user["home_city"]]
    local_swipes = [row for row in window_rows if row["ciudad"] == user["home_city"]]
    feature_row[f"local_like_rate{suffix}"] = safe_div(len(local_likes), len(liked_rows))
    feature_row[f"local_swipe_share{suffix}"] = safe_div(len(local_swipes), total_swipes)
    feature_row[f"avg_days_until_event_liked{suffix}"] = mean_or_zero([float(row["days_until_event"]) for row in liked_rows])
    feature_row[f"avg_price_mid_liked{suffix}"] = mean_or_zero([float(row["price_mid"]) for row in liked_rows])
    feature_row[f"median_price_mid_liked{suffix}"] = median_or_zero([float(row["price_mid"]) for row in liked_rows])
    feature_row[f"avg_price_mid_disliked{suffix}"] = mean_or_zero([float(row["price_mid"]) for row in disliked_rows])
    feature_row[f"chat_swipe_share{suffix}"] = safe_div(
        len([row for row in window_rows if row["recommendation_context"] == "chat"]),
        total_swipes,
    )
    feature_row[f"chat_right_rate{suffix}"] = safe_div(
        len([row for row in liked_rows if row["recommendation_context"] == "chat"]),
        len([row for row in window_rows if row["recommendation_context"] == "chat"]),
    )

    if liked_rows:
        latest_like = max(row["event_timestamp"] for row in liked_rows)
        feature_row[f"days_since_last_right_swipe{suffix}"] = float((ANCHOR_DATETIME - latest_like).days)
    else:
        feature_row[f"days_since_last_right_swipe{suffix}"] = float(window_days + 7)

    for segment in SEGMENT_NAMES:
        segment_rows = [row for row in window_rows if row["segmento"] == segment]
        liked_segment_rows = [row for row in segment_rows if row["liked"]]
        feature_row[f"like_rate_segment_{slugify(segment)}{suffix}"] = safe_div(len(liked_segment_rows), len(segment_rows))

    for genre in GENRE_NAMES:
        genre_rows = [row for row in window_rows if row["genero"] == genre]
        liked_genre_rows = [row for row in genre_rows if row["liked"]]
        feature_row[f"like_rate_genre_{slugify(genre)}{suffix}"] = safe_div(len(liked_genre_rows), len(genre_rows))

    return feature_row


def build_user_features(
    users: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows_by_user: dict[str, list[dict[str, Any]]] = {}
    for user in users:
        rows_by_user[str(user["user_id"])] = []
    for row in interactions:
        rows_by_user.setdefault(str(row["user_id"]), []).append(row)

    feature_rows: list[dict[str, Any]] = []
    for user in users:
        user_rows = rows_by_user[str(user["user_id"])]
        row_30d = build_feature_row(user, user_rows, 30)
        row_90d = build_feature_row(user, user_rows, 90)
        combined: dict[str, Any] = {
            "user_id": user["user_id"],
            "home_city": user["home_city"],
            "synthetic_persona": user["synthetic_persona"],
        }
        combined.update(row_30d)
        combined.update(row_90d)
        combined["right_swipe_rate_delta_30_vs_90"] = combined["right_swipe_rate_30d"] - combined["right_swipe_rate_90d"]
        combined["total_swipes_delta_30_vs_90"] = combined["total_swipes_30d"] - combined["total_swipes_90d"]
        feature_rows.append(combined)

    training_columns = [
        "total_swipes_30d",
        "right_swipe_rate_30d",
        "avg_dwell_ms_30d",
        "distinct_segments_liked_30d",
        "distinct_cities_liked_30d",
        "local_like_rate_30d",
        "avg_days_until_event_liked_30d",
        "avg_price_mid_liked_30d",
        "chat_swipe_share_30d",
        "days_since_last_right_swipe_30d",
        "total_swipes_90d",
        "right_swipe_rate_90d",
        "avg_dwell_ms_90d",
        "distinct_segments_liked_90d",
        "distinct_genres_liked_90d",
        "distinct_cities_liked_90d",
        "local_like_rate_90d",
        "avg_days_until_event_liked_90d",
        "avg_price_mid_liked_90d",
        "avg_price_mid_disliked_90d",
        "chat_swipe_share_90d",
        "chat_right_rate_90d",
        "days_since_last_right_swipe_90d",
        "right_swipe_rate_delta_30_vs_90",
    ]
    training_columns.extend([f"like_rate_segment_{slugify(segment)}_90d" for segment in SEGMENT_NAMES])
    training_columns.extend([f"like_rate_genre_{slugify(genre)}_90d" for genre in GENRE_NAMES])
    return feature_rows, training_columns


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    users = load_users()
    interactions = load_interactions()
    feature_rows, training_columns = build_user_features(users, interactions)
    eligible_feature_rows = [
        row
        for row in feature_rows
        if row["total_swipes_30d"] >= MIN_SWIPES_30D and row["total_swipes_90d"] >= MIN_SWIPES_90D
    ]
    if len(eligible_feature_rows) != len(feature_rows):
        raise RuntimeError("Synthetic generation created users without enough activity for clustering.")

    write_csv(USER_FEATURES_PATH, eligible_feature_rows)
    write_json(
        USER_FEATURES_METADATA_PATH,
        {
            "anchor_date": ANCHOR_DATE.isoformat(),
            "min_swipes_30d": MIN_SWIPES_30D,
            "min_swipes_90d": MIN_SWIPES_90D,
            "training_columns": training_columns,
            "total_users": len(feature_rows),
            "eligible_users": len(eligible_feature_rows),
        },
    )
    print("Step 2 completed: user features built.")
    print(f"Feature rows: {len(eligible_feature_rows)}")
    print(f"Training columns: {len(training_columns)}")
    print(f"Output path: {USER_FEATURES_PATH}")


if __name__ == "__main__":
    main()
