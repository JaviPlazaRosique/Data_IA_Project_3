from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

USER_FEATURES_PATH = OUTPUT_DIR / "user_features.csv"
MODEL_METRICS_PATH = OUTPUT_DIR / "model_selection_metrics.csv"
USER_FEATURES_METADATA_PATH = ARTIFACTS_DIR / "user_features_metadata.json"
MODEL_ARTIFACTS_PATH = ARTIFACTS_DIR / "model_artifacts.json"

RANDOM_SEED = 20260430


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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

    matrix: list[list[float]] = []
    for row in rows:
        matrix.append([(float(row[column]) - means[column]) / stds[column] for column in columns])
    return matrix, means, stds


def squared_distance(point_a: list[float], point_b: list[float]) -> float:
    return sum((value_a - value_b) ** 2 for value_a, value_b in zip(point_a, point_b))


def euclidean_distance(point_a: list[float], point_b: list[float]) -> float:
    return math.sqrt(squared_distance(point_a, point_b))


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


def recompute_centers(
    points: list[list[float]],
    labels: list[int],
    centers: list[list[float]],
) -> list[list[float]]:
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
            farthest_point = max(points, key=lambda point: min(squared_distance(point, center) for center in centers))
            new_centers[index] = farthest_point[:]
            continue
        new_centers[index] = [value / counts[index] for value in new_centers[index]]
    return new_centers


def fit_kmeans(
    points: list[list[float]],
    k: int,
    base_seed: int,
    n_init: int = 8,
    max_iter: int = 100,
) -> dict[str, Any]:
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

    db_terms: list[float] = []
    for label_i in cluster_indices:
        ratios = []
        for label_j in cluster_indices:
            if label_i == label_j:
                continue
            centroid_distance = euclidean_distance(centers[label_i], centers[label_j])
            if centroid_distance == 0:
                ratios.append(float("inf"))
            else:
                ratios.append((scatters[label_i] + scatters[label_j]) / centroid_distance)
        db_terms.append(max(ratios) if ratios else 0.0)
    return mean_or_zero(db_terms)


def select_best_model(points: list[list[float]], k_values: list[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
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


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    metadata = read_json(USER_FEATURES_METADATA_PATH)
    training_columns = list(metadata["training_columns"])
    feature_rows = load_user_features()
    points, means, stds = standardize_matrix(feature_rows, training_columns)
    model_metrics, best_model = select_best_model(points, [4, 5, 6, 7, 8])
    labels_by_user = {
        str(row["user_id"]): int(label)
        for row, label in zip(feature_rows, best_model["labels"])
    }

    write_csv(MODEL_METRICS_PATH, model_metrics)
    write_json(
        MODEL_ARTIFACTS_PATH,
        {
            "selected_k": int(best_model["k"]),
            "selected_metrics": best_model["metrics"],
            "training_columns": training_columns,
            "feature_means": means,
            "feature_stds": stds,
            "centers": best_model["centers"],
            "labels_by_user": labels_by_user,
        },
    )
    print("Step 3 completed: baseline model trained.")
    print(f"Selected k: {best_model['k']}")
    print(f"Silhouette: {best_model['metrics']['silhouette_score']:.4f}")
    print(f"Davies-Bouldin: {best_model['metrics']['davies_bouldin_score']:.4f}")
    print(f"Artifacts path: {MODEL_ARTIFACTS_PATH}")


if __name__ == "__main__":
    main()
