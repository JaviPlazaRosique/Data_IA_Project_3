from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

INTERACTIONS_PATH = DATA_DIR / "synthetic_fct_swipes.csv"
USER_FEATURES_PATH = OUTPUT_DIR / "user_features.csv"
ASSIGNMENTS_PATH = OUTPUT_DIR / "user_cluster_assignments.csv"
CLUSTER_PROFILES_PATH = OUTPUT_DIR / "cluster_profiles.csv"
CLUSTER_NEIGHBORS_PATH = OUTPUT_DIR / "cluster_neighbors.csv"
CLUSTER_AFFINITY_PATH = OUTPUT_DIR / "cluster_event_affinity.csv"
USER_FEATURES_METADATA_PATH = ARTIFACTS_DIR / "user_features_metadata.json"
MODEL_ARTIFACTS_PATH = ARTIFACTS_DIR / "model_artifacts.json"

ANCHOR_DATE = date(2026, 4, 30)
ANCHOR_DATETIME = datetime.combine(ANCHOR_DATE, time(23, 59, 59), tzinfo=timezone.utc)

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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.lower() == "true"


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


def load_user_features() -> list[dict[str, Any]]:
    rows = read_csv_rows(USER_FEATURES_PATH)
    feature_rows: list[dict[str, Any]] = []
    for row in rows:
        parsed: dict[str, Any] = {}
        for key, value in row.items():
            if key in {"user_id", "home_city", "synthetic_persona"}:
                parsed[key] = value
            else:
                parsed[key] = float(value)
        feature_rows.append(parsed)
    return feature_rows


def standardize_rows(
    rows: list[dict[str, Any]],
    columns: list[str],
    means: dict[str, float],
    stds: dict[str, float],
) -> list[list[float]]:
    return [
        [(float(row[column]) - float(means[column])) / float(stds[column]) for column in columns]
        for row in rows
    ]


def squared_distance(point_a: list[float], point_b: list[float]) -> float:
    return sum((value_a - value_b) ** 2 for value_a, value_b in zip(point_a, point_b))


def euclidean_distance(point_a: list[float], point_b: list[float]) -> float:
    return math.sqrt(squared_distance(point_a, point_b))


def cosine_similarity(point_a: list[float], point_b: list[float]) -> float:
    numerator = sum(value_a * value_b for value_a, value_b in zip(point_a, point_b))
    denom_a = math.sqrt(sum(value * value for value in point_a))
    denom_b = math.sqrt(sum(value * value for value in point_b))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return numerator / (denom_a * denom_b)


def build_assignments(
    feature_rows: list[dict[str, Any]],
    points: list[list[float]],
    centers: list[list[float]],
    labels: list[int],
) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for row, point, cluster_id in zip(feature_rows, points, labels):
        ordered = sorted(
            ((index, euclidean_distance(point, center)) for index, center in enumerate(centers)),
            key=lambda item: item[1],
        )
        assignments.append(
            {
                "user_id": row["user_id"],
                "home_city": row["home_city"],
                "synthetic_persona": row["synthetic_persona"],
                "cluster_id": cluster_id,
                "distance_to_centroid": ordered[0][1],
                "distance_to_next_centroid": ordered[1][1] if len(ordered) > 1 else ordered[0][1],
                "total_swipes_90d": row["total_swipes_90d"],
                "right_swipe_rate_90d": row["right_swipe_rate_90d"],
                "local_like_rate_90d": row["local_like_rate_90d"],
                "avg_price_mid_liked_90d": row["avg_price_mid_liked_90d"],
            }
        )
    assignments.sort(key=lambda row: (int(row["cluster_id"]), str(row["user_id"])))
    return assignments


def top_labels_from_features(
    aggregate_row: dict[str, float],
    prefix: str,
    labels: list[str],
    top_n: int = 2,
) -> list[str]:
    pairs = []
    for label in labels:
        column = f"{prefix}{slugify(label)}_90d"
        pairs.append((label, float(aggregate_row.get(column, 0.0))))
    pairs.sort(key=lambda item: item[1], reverse=True)
    return [label for label, _ in pairs[:top_n]]


def build_cluster_profiles(
    feature_rows: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    features_by_user = {str(row["user_id"]): row for row in feature_rows}
    users_by_cluster: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for assignment in assignments:
        users_by_cluster[int(assignment["cluster_id"])].append(features_by_user[str(assignment["user_id"])])

    profiles: list[dict[str, Any]] = []
    total_users = len(assignments)
    for cluster_id in sorted(users_by_cluster):
        members = users_by_cluster[cluster_id]
        aggregate: dict[str, float] = {}
        numeric_columns = [key for key in members[0].keys() if key not in {"user_id", "home_city", "synthetic_persona"}]
        for column in numeric_columns:
            aggregate[column] = mean_or_zero([float(member[column]) for member in members])
        persona_counter = Counter(str(member["synthetic_persona"]) for member in members)
        city_counter = Counter(str(member["home_city"]) for member in members)
        top_segments = top_labels_from_features(aggregate, "like_rate_segment_", SEGMENT_NAMES)
        top_genres = top_labels_from_features(aggregate, "like_rate_genre_", GENRE_NAMES)
        dominant_persona, dominant_persona_count = persona_counter.most_common(1)[0]
        dominant_city, dominant_city_count = city_counter.most_common(1)[0]
        profiles.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": len(members),
                "share_of_users": safe_div(len(members), total_users),
                "dominant_synthetic_persona": dominant_persona,
                "dominant_synthetic_persona_share": safe_div(dominant_persona_count, len(members)),
                "dominant_home_city": dominant_city,
                "dominant_home_city_share": safe_div(dominant_city_count, len(members)),
                "avg_total_swipes_90d": aggregate["total_swipes_90d"],
                "avg_right_swipe_rate_90d": aggregate["right_swipe_rate_90d"],
                "avg_local_like_rate_90d": aggregate["local_like_rate_90d"],
                "avg_chat_swipe_share_90d": aggregate["chat_swipe_share_90d"],
                "avg_days_until_event_liked_90d": aggregate["avg_days_until_event_liked_90d"],
                "avg_price_mid_liked_90d": aggregate["avg_price_mid_liked_90d"],
                "top_segment_1": top_segments[0],
                "top_segment_2": top_segments[1] if len(top_segments) > 1 else top_segments[0],
                "top_genre_1": top_genres[0],
                "top_genre_2": top_genres[1] if len(top_genres) > 1 else top_genres[0],
            }
        )
    return profiles


def build_cluster_neighbors(centers: list[list[float]]) -> list[dict[str, Any]]:
    neighbors: list[dict[str, Any]] = []
    for cluster_id, center in enumerate(centers):
        scores = []
        for neighbor_id, neighbor_center in enumerate(centers):
            if cluster_id == neighbor_id:
                continue
            scores.append(
                {
                    "neighbor_cluster_id": neighbor_id,
                    "euclidean_distance": euclidean_distance(center, neighbor_center),
                    "cosine_similarity": cosine_similarity(center, neighbor_center),
                }
            )
        scores.sort(key=lambda row: (row["euclidean_distance"], -row["cosine_similarity"]))
        for rank, score in enumerate(scores, start=1):
            neighbors.append(
                {
                    "cluster_id": cluster_id,
                    "neighbor_rank": rank,
                    "neighbor_cluster_id": score["neighbor_cluster_id"],
                    "euclidean_distance": score["euclidean_distance"],
                    "cosine_similarity": score["cosine_similarity"],
                }
            )
    return neighbors


def build_cluster_event_affinity(
    interactions: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assignment_map = {str(row["user_id"]): int(row["cluster_id"]) for row in assignments}
    recent_rows = [row for row in interactions if row["event_timestamp"] >= ANCHOR_DATETIME - timedelta(days=89)]
    global_counts: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: {"total": 0, "right": 0})
    cluster_counts: dict[int, dict[tuple[str, str, str], dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"total": 0, "right": 0})
    )
    cluster_total_rights: dict[int, int] = Counter()

    for row in recent_rows:
        user_id = str(row["user_id"])
        if user_id not in assignment_map:
            continue
        cluster_id = assignment_map[user_id]
        key = (str(row["segmento"]), str(row["genero"]), str(row["subgenero"]))
        global_counts[key]["total"] += 1
        cluster_counts[cluster_id][key]["total"] += 1
        if row["liked"]:
            global_counts[key]["right"] += 1
            cluster_counts[cluster_id][key]["right"] += 1
            cluster_total_rights[cluster_id] += 1

    affinity_rows: list[dict[str, Any]] = []
    for cluster_id in sorted(cluster_counts):
        ranked_rows = []
        for key, counts in cluster_counts[cluster_id].items():
            segment, genre, subgenre = key
            global_rate = safe_div(global_counts[key]["right"], global_counts[key]["total"])
            cluster_rate = safe_div(counts["right"], counts["total"])
            ranked_rows.append(
                {
                    "cluster_id": cluster_id,
                    "segmento": segment,
                    "genero": genre,
                    "subgenero": subgenre,
                    "total_swipes": counts["total"],
                    "right_swipes": counts["right"],
                    "right_swipe_rate": cluster_rate,
                    "global_right_swipe_rate": global_rate,
                    "affinity_lift_vs_global": safe_div(cluster_rate, global_rate) if global_rate else 0.0,
                    "share_of_cluster_right_swipes": safe_div(counts["right"], cluster_total_rights[cluster_id]),
                }
            )
        ranked_rows.sort(
            key=lambda row: (
                row["affinity_lift_vs_global"],
                row["right_swipe_rate"],
                row["right_swipes"],
            ),
            reverse=True,
        )
        for rank, row in enumerate(ranked_rows, start=1):
            row["cluster_affinity_rank"] = rank
            affinity_rows.append(row)
    return affinity_rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_artifacts = read_json(MODEL_ARTIFACTS_PATH)
    metadata = read_json(USER_FEATURES_METADATA_PATH)
    training_columns = list(metadata["training_columns"])
    feature_rows = load_user_features()
    interactions = load_interactions()
    means = {key: float(value) for key, value in dict(model_artifacts["feature_means"]).items()}
    stds = {key: float(value) for key, value in dict(model_artifacts["feature_stds"]).items()}
    centers = [[float(value) for value in center] for center in model_artifacts["centers"]]
    labels_by_user = {str(key): int(value) for key, value in dict(model_artifacts["labels_by_user"]).items()}

    eligible_feature_rows = [row for row in feature_rows if str(row["user_id"]) in labels_by_user]
    points = standardize_rows(eligible_feature_rows, training_columns, means, stds)
    labels = [labels_by_user[str(row["user_id"])] for row in eligible_feature_rows]

    assignments = build_assignments(eligible_feature_rows, points, centers, labels)
    profiles = build_cluster_profiles(eligible_feature_rows, assignments)
    neighbors = build_cluster_neighbors(centers)
    affinity_rows = build_cluster_event_affinity(interactions, assignments)

    write_csv(ASSIGNMENTS_PATH, assignments)
    write_csv(CLUSTER_PROFILES_PATH, profiles)
    write_csv(CLUSTER_NEIGHBORS_PATH, neighbors)
    write_csv(CLUSTER_AFFINITY_PATH, affinity_rows)
    print("Step 4 completed: cluster outputs generated.")
    print(f"Assignments: {len(assignments)}")
    print(f"Clusters: {len(profiles)}")
    print(f"Affinity rows: {len(affinity_rows)}")
    print(f"Profiles path: {CLUSTER_PROFILES_PATH}")


if __name__ == "__main__":
    main()
