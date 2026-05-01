from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "training_outputs" / "real_feature_clustering"
RANDOM_SEED = 20260501
RESERVED_METADATA_COLUMNS = {"user_id", "home_city", "synthetic_persona"}


def mean_or_zero(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def serialize_value(value: Any) -> Any:
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


def read_feature_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"No rows found in feature export: {path}")

    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        parsed: dict[str, Any] = {}
        for key, value in row.items():
            if key in RESERVED_METADATA_COLUMNS:
                parsed[key] = value
            else:
                parsed[key] = float(value) if value not in {"", None} else 0.0
        parsed_rows.append(parsed)
    return parsed_rows


def numeric_feature_columns(rows: list[dict[str, Any]]) -> list[str]:
    first_row = rows[0]
    return [column for column in first_row.keys() if column not in RESERVED_METADATA_COLUMNS]


def standardize_matrix(rows: list[dict[str, Any]], columns: list[str]) -> tuple[list[list[float]], dict[str, float], dict[str, float]]:
    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    for column in columns:
        values = [float(row[column]) for row in rows]
        mean_value = mean_or_zero(values)
        variance = mean_or_zero([(value - mean_value) ** 2 for value in values])
        std_value = math.sqrt(variance) if variance > 0 else 1.0
        means[column] = mean_value
        stds[column] = std_value

    matrix = []
    for row in rows:
        matrix.append([(float(row[column]) - means[column]) / stds[column] for column in columns])
    return matrix, means, stds


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


def kmeans_plus_plus(points: list[list[float]], k: int, rng: random.Random) -> list[list[float]]:
    centers = [points[rng.randrange(len(points))][:]]
    while len(centers) < k:
        distances = [min(squared_distance(point, center) for center in centers) for point in points]
        total = sum(distances)
        if total == 0:
            centers.append(points[rng.randrange(len(points))][:])
            continue
        threshold = rng.random() * total
        cumulative = 0.0
        for point, distance in zip(points, distances):
            cumulative += distance
            if cumulative >= threshold:
                centers.append(point[:])
                break
    return centers


def assign_points(points: list[list[float]], centers: list[list[float]]) -> tuple[list[int], float]:
    labels: list[int] = []
    inertia = 0.0
    for point in points:
        best_index = 0
        best_distance = squared_distance(point, centers[0])
        for index in range(1, len(centers)):
            distance = squared_distance(point, centers[index])
            if distance < best_distance:
                best_index = index
                best_distance = distance
        labels.append(best_index)
        inertia += best_distance
    return labels, inertia


def recompute_centers(points: list[list[float]], labels: list[int], centers: list[list[float]]) -> list[list[float]]:
    k = len(centers)
    dimensions = len(points[0])
    new_centers = [[0.0 for _ in range(dimensions)] for _ in range(k)]
    counts = [0 for _ in range(k)]

    for point, label in zip(points, labels):
        counts[label] += 1
        for dimension in range(dimensions):
            new_centers[label][dimension] += point[dimension]

    for index in range(k):
        if counts[index] == 0:
            new_centers[index] = max(points, key=lambda point: min(squared_distance(point, center) for center in centers))[:]
            continue
        new_centers[index] = [value / counts[index] for value in new_centers[index]]
    return new_centers


def fit_kmeans(points: list[list[float]], k: int, base_seed: int, n_init: int = 8, max_iter: int = 100) -> dict[str, Any]:
    best_model: dict[str, Any] | None = None
    for init_index in range(n_init):
        rng = random.Random(base_seed + (k * 100) + init_index)
        centers = kmeans_plus_plus(points, k, rng)
        labels: list[int] = []
        inertia = 0.0
        for _ in range(max_iter):
            labels, inertia = assign_points(points, centers)
            new_centers = recompute_centers(points, labels, centers)
            if all(euclidean_distance(old, new) < 1e-6 for old, new in zip(centers, new_centers)):
                centers = new_centers
                break
            centers = new_centers
        labels, inertia = assign_points(points, centers)
        candidate = {
            "k": k,
            "labels": labels,
            "centers": centers,
            "inertia": inertia,
            "cluster_sizes": dict(Counter(labels)),
        }
        if best_model is None or inertia < float(best_model["inertia"]):
            best_model = candidate
    if best_model is None:
        raise RuntimeError("KMeans training failed.")
    return best_model


def pairwise_distance_matrix(points: list[list[float]]) -> list[list[float]]:
    matrix = [[0.0 for _ in range(len(points))] for _ in range(len(points))]
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            distance = euclidean_distance(points[left], points[right])
            matrix[left][right] = distance
            matrix[right][left] = distance
    return matrix


def silhouette_score(points: list[list[float]], labels: list[int]) -> float:
    unique_labels = sorted(set(labels))
    if len(unique_labels) < 2:
        return 0.0
    cluster_indices: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        cluster_indices[label].append(index)
    distances = pairwise_distance_matrix(points)
    total_score = 0.0
    for index, label in enumerate(labels):
        own_cluster = cluster_indices[label]
        if len(own_cluster) <= 1:
            continue
        intra = sum(distances[index][other] for other in own_cluster if other != index) / (len(own_cluster) - 1)
        nearest = min(
            sum(distances[index][other] for other in members) / len(members)
            for other_label, members in cluster_indices.items()
            if other_label != label and members
        )
        denominator = max(intra, nearest)
        total_score += (nearest - intra) / denominator if denominator else 0.0
    return total_score / len(points)


def davies_bouldin_score(points: list[list[float]], labels: list[int], centers: list[list[float]]) -> float:
    cluster_indices: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        cluster_indices[label].append(index)
    scatters: dict[int, float] = {}
    for label, indices in cluster_indices.items():
        scatters[label] = mean_or_zero([euclidean_distance(points[index], centers[label]) for index in indices])

    db_terms = []
    for label_i in cluster_indices:
        ratios = []
        for label_j in cluster_indices:
            if label_i == label_j:
                continue
            centroid_distance = euclidean_distance(centers[label_i], centers[label_j])
            ratios.append(float("inf") if centroid_distance == 0 else (scatters[label_i] + scatters[label_j]) / centroid_distance)
        db_terms.append(max(ratios) if ratios else 0.0)
    return mean_or_zero(db_terms)


def select_best_model(points: list[list[float]], k_values: list[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = []
    best_model: dict[str, Any] | None = None
    for k in k_values:
        model = fit_kmeans(points, k, RANDOM_SEED)
        sizes = list(model["cluster_sizes"].values())
        metrics = {
            "k": k,
            "inertia": model["inertia"],
            "silhouette_score": silhouette_score(points, model["labels"]),
            "davies_bouldin_score": davies_bouldin_score(points, model["labels"], model["centers"]),
            "min_cluster_size": min(sizes),
            "max_cluster_size": max(sizes),
            "mean_cluster_size": mean_or_zero([float(size) for size in sizes]),
        }
        model["metrics"] = metrics
        results.append(metrics)
        if best_model is None:
            best_model = model
            continue
        best_metrics = best_model["metrics"]
        candidate_key = (
            metrics["min_cluster_size"] >= 12,
            round(metrics["silhouette_score"], 6),
            -round(metrics["davies_bouldin_score"], 6),
            metrics["min_cluster_size"],
            -metrics["k"],
        )
        best_key = (
            best_metrics["min_cluster_size"] >= 12,
            round(best_metrics["silhouette_score"], 6),
            -round(best_metrics["davies_bouldin_score"], 6),
            best_metrics["min_cluster_size"],
            -best_metrics["k"],
        )
        if candidate_key > best_key:
            best_model = model
    if best_model is None:
        raise RuntimeError("No model selected.")
    return results, best_model


def top_labels(feature_row: dict[str, float], prefix: str, top_n: int = 2) -> list[str]:
    candidates = [
        (key.replace(prefix, ""), float(value))
        for key, value in feature_row.items()
        if key.startswith(prefix)
    ]
    if not candidates:
        return ["n/a", "n/a"]
    candidates.sort(key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in candidates[:top_n]]
    while len(labels) < top_n:
        labels.append("n/a")
    return labels


def build_assignments(feature_rows: list[dict[str, Any]], points: list[list[float]], centers: list[list[float]], labels: list[int]) -> list[dict[str, Any]]:
    assignments = []
    for row, point, cluster_id in zip(feature_rows, points, labels):
        ordered = sorted(((index, euclidean_distance(point, center)) for index, center in enumerate(centers)), key=lambda item: item[1])
        assignments.append(
            {
                "user_id": row["user_id"],
                "home_city": row.get("home_city", ""),
                "synthetic_persona": row.get("synthetic_persona", ""),
                "cluster_id": cluster_id,
                "distance_to_centroid": ordered[0][1],
                "distance_to_next_centroid": ordered[1][1] if len(ordered) > 1 else ordered[0][1],
            }
        )
    assignments.sort(key=lambda row: (int(row["cluster_id"]), str(row["user_id"])))
    return assignments


def build_cluster_profiles(feature_rows: list[dict[str, Any]], assignments: list[dict[str, Any]], numeric_columns: list[str]) -> list[dict[str, Any]]:
    features_by_user = {str(row["user_id"]): row for row in feature_rows}
    users_by_cluster: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for assignment in assignments:
        users_by_cluster[int(assignment["cluster_id"])].append(features_by_user[str(assignment["user_id"])])

    profiles = []
    total_users = len(assignments)
    for cluster_id in sorted(users_by_cluster):
        members = users_by_cluster[cluster_id]
        aggregate = {column: mean_or_zero([float(member[column]) for member in members]) for column in numeric_columns}
        persona_counter = Counter(str(member.get("synthetic_persona", "")) for member in members if member.get("synthetic_persona"))
        city_counter = Counter(str(member.get("home_city", "")) for member in members if member.get("home_city"))
        top_segments = top_labels(aggregate, "like_rate_segment_")
        top_genres = top_labels(aggregate, "like_rate_genre_")
        dominant_persona, dominant_persona_share = ("n/a", 0.0)
        if persona_counter:
            dominant_persona, persona_count = persona_counter.most_common(1)[0]
            dominant_persona_share = persona_count / len(members)
        dominant_home_city, dominant_home_city_share = ("n/a", 0.0)
        if city_counter:
            dominant_home_city, city_count = city_counter.most_common(1)[0]
            dominant_home_city_share = city_count / len(members)

        profiles.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": len(members),
                "share_of_users": len(members) / total_users,
                "dominant_synthetic_persona": dominant_persona,
                "dominant_synthetic_persona_share": dominant_persona_share,
                "dominant_home_city": dominant_home_city,
                "dominant_home_city_share": dominant_home_city_share,
                "top_segment_1": top_segments[0],
                "top_segment_2": top_segments[1],
                "top_genre_1": top_genres[0],
                "top_genre_2": top_genres[1],
            }
        )
    return profiles


def build_cluster_neighbors(centers: list[list[float]]) -> list[dict[str, Any]]:
    neighbors = []
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train clustering from a feature export CSV.")
    parser.add_argument("--input-csv", required=True, help="Path to the feature export CSV.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for training outputs.")
    parser.add_argument("--k-values", default="4,5,6,7,8", help="Comma-separated k values to evaluate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv).resolve()
    output_dir = Path(args.output_dir).resolve()
    k_values = [int(value) for value in args.k_values.split(",") if value.strip()]

    feature_rows = read_feature_rows(input_csv)
    numeric_columns = numeric_feature_columns(feature_rows)
    points, means, stds = standardize_matrix(feature_rows, numeric_columns)
    metrics, best_model = select_best_model(points, k_values)
    assignments = build_assignments(feature_rows, points, best_model["centers"], best_model["labels"])
    profiles = build_cluster_profiles(feature_rows, assignments, numeric_columns)
    neighbors = build_cluster_neighbors(best_model["centers"])

    write_csv(output_dir / "user_cluster_assignments.csv", assignments)
    write_csv(output_dir / "cluster_profiles.csv", profiles)
    write_csv(output_dir / "cluster_neighbors.csv", neighbors)
    write_csv(output_dir / "model_selection_metrics.csv", metrics)
    write_json(
        output_dir / "training_run_summary.json",
        {
            "input_csv": str(input_csv),
            "output_dir": str(output_dir),
            "rows": len(feature_rows),
            "numeric_feature_count": len(numeric_columns),
            "selected_k": int(best_model["k"]),
            "silhouette_score": float(best_model["metrics"]["silhouette_score"]),
            "davies_bouldin_score": float(best_model["metrics"]["davies_bouldin_score"]),
            "feature_means": means,
            "feature_stds": stds,
        },
    )

    print("Step 4 completed: training adapted to feature export.")
    print(f"Input CSV: {input_csv}")
    print(f"Rows: {len(feature_rows)}")
    print(f"Selected k: {best_model['k']}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
