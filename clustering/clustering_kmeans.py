#!/usr/bin/env python3
"""Verbose K-Means clustering pipeline for swipe interactions.

This script:
1. Reads the swipe CSV
2. Cleans types and enforces basic data coherence
3. Aggregates interactions by user_id
4. Builds behavior features for clustering
5. Scales numeric variables
6. Tests K-Means with several K values
7. Selects the best K using silhouette score
8. Fits the final K-Means model
9. Writes several output files to support analysis and interpretation
"""

from __future__ import annotations

import argparse
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a verbose K-Means clustering workflow on swipe interactions."
    )
    parser.add_argument(
        "--input",
        default="clustering/swipe_interactions_synthetic.csv",
        help="Path to the input CSV with swipe interactions.",
    )
    parser.add_argument(
        "--output-dir",
        default="clustering/output",
        help="Directory where all output files will be written.",
    )
    parser.add_argument(
        "--k-range",
        default="2,3,4,5,6,7,8",
        help="Comma-separated list of K values to test.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for K-Means reproducibility.",
    )
    parser.add_argument(
        "--n-init",
        type=int,
        default=20,
        help="Number of K-Means initializations.",
    )
    return parser.parse_args()


def require_module(module_name: str, install_hint: str):
    try:
        return __import__(module_name)
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"Missing dependency '{module_name}'. Install it with: {install_hint}"
        ) from exc


@dataclass
class VerboseLogger:
    lines: list[str]

    def log(self, message: str) -> None:
        self.lines.append(message)
        print(message)

    def section(self, title: str) -> None:
        line = f"\n{'=' * 12} {title} {'=' * 12}"
        self.log(line)

    def write(self, path: Path) -> None:
        path.write_text("\n".join(self.lines).strip() + "\n", encoding="utf-8")


def parse_bool(value) -> bool | None:
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    return None


def slugify(text: str) -> str:
    text = str(text).strip().lower()
    replacements = {
        " ": "_",
        "&": "and",
        "/": "_",
        "-": "_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = "".join(ch for ch in text if ch.isalnum() or ch == "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


def entropy_from_series(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    probs = series.value_counts(normalize=True)
    return float(-(probs * np.log2(probs)).sum())


def rate_for_subset(df: pd.DataFrame, column: str, value: str) -> float:
    subset = df[df[column] == value]
    if subset.empty:
        return 0.0
    return float(subset["liked"].mean())


def ratio_of_subset(df: pd.DataFrame, column: str, value: str) -> float:
    if df.empty:
        return 0.0
    return float((df[column] == value).mean())


def safe_mean(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    return float(series.mean())


def read_input_csv(path: Path, logger: VerboseLogger) -> pd.DataFrame:
    logger.section("Step 1 - Read CSV")
    logger.log(f"Reading input file from: {path}")
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")

    df = pd.read_csv(path)
    logger.log(f"Loaded {len(df):,} interaction rows.")
    logger.log(f"Detected {len(df.columns)} columns in the CSV.")
    logger.log(f"Column names: {', '.join(df.columns)}")
    return df


def clean_data(df: pd.DataFrame, logger: VerboseLogger) -> tuple[pd.DataFrame, dict]:
    logger.section("Step 2 - Clean Types And Coherence")
    metrics: dict[str, float | int] = {
        "input_rows": int(len(df)),
    }

    required_columns = [
        "interaction_id",
        "event_timestamp",
        "user_id",
        "session_id",
        "event_id",
        "interaction_type",
        "swipe_direction",
        "liked",
        "recommendation_context",
        "segmento",
        "genero",
        "subgenero",
        "ciudad",
        "precio_min",
        "precio_max",
        "fecha_evento",
        "recinto_id",
        "ingestion_timestamp",
    ]
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    logger.log("All required columns are present.")
    logger.log("Dropping duplicate rows by interaction_id if any exist.")
    df = df.copy()
    df = df.drop_duplicates(subset=["interaction_id"])
    metrics["rows_after_dedup"] = int(len(df))
    logger.log(f"Rows after deduplication: {len(df):,}")

    logger.log("Casting timestamps, booleans and price columns to proper types.")
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce")
    df["ingestion_timestamp"] = pd.to_datetime(df["ingestion_timestamp"], errors="coerce")
    df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
    df["liked"] = df["liked"].apply(parse_bool)
    df["precio_min"] = pd.to_numeric(df["precio_min"], errors="coerce")
    df["precio_max"] = pd.to_numeric(df["precio_max"], errors="coerce")

    logger.log("Checking logical consistency between swipe_direction and liked.")
    mismatch_mask = (
        ((df["swipe_direction"] == "right") & (df["liked"] != True))
        | ((df["swipe_direction"] == "left") & (df["liked"] != False))
    )
    metrics["direction_liked_mismatches"] = int(mismatch_mask.sum())
    logger.log(
        f"Rows with mismatched direction and liked before correction: {metrics['direction_liked_mismatches']}"
    )
    df.loc[df["swipe_direction"] == "right", "liked"] = True
    df.loc[df["swipe_direction"] == "left", "liked"] = False

    logger.log("Keeping only swipe interactions, since K-Means will be trained on swipe behavior.")
    df = df[df["interaction_type"].str.lower() == "swipe"].copy()
    metrics["rows_after_interaction_filter"] = int(len(df))
    logger.log(f"Rows after filtering interaction_type='swipe': {len(df):,}")

    logger.log("Checking malformed prices where precio_max < precio_min.")
    swap_mask = df["precio_max"] < df["precio_min"]
    metrics["price_swaps"] = int(swap_mask.sum())
    if metrics["price_swaps"] > 0:
        logger.log(f"Found {metrics['price_swaps']} swapped price rows. Fixing them now.")
        df.loc[swap_mask, ["precio_min", "precio_max"]] = df.loc[
            swap_mask, ["precio_max", "precio_min"]
        ].to_numpy()
    else:
        logger.log("No swapped price rows detected.")

    logger.log("Dropping rows with missing values in critical columns.")
    valid_mask = (
        df["event_timestamp"].notna()
        & df["ingestion_timestamp"].notna()
        & df["fecha_evento"].notna()
        & df["liked"].notna()
        & df["precio_min"].notna()
        & df["precio_max"].notna()
        & df["user_id"].notna()
    )
    metrics["rows_dropped_invalid"] = int((~valid_mask).sum())
    df = df[valid_mask].copy()
    logger.log(f"Rows dropped due to invalid or missing critical values: {metrics['rows_dropped_invalid']}")

    logger.log("Creating row-level derived variables used later in aggregation.")
    df["days_until_event"] = (df["fecha_evento"] - df["event_timestamp"].dt.normalize()).dt.days
    df["avg_price"] = (df["precio_min"] + df["precio_max"]) / 2.0
    df["is_right_swipe"] = df["swipe_direction"].eq("right").astype(int)

    metrics["clean_rows"] = int(len(df))
    metrics["unique_users"] = int(df["user_id"].nunique())
    logger.log(f"Clean interaction rows ready for feature engineering: {len(df):,}")
    logger.log(f"Unique users available for clustering: {metrics['unique_users']}")
    return df, metrics


def build_user_features(df: pd.DataFrame, logger: VerboseLogger) -> pd.DataFrame:
    logger.section("Step 3 - Aggregate By user_id And Build Features")
    logger.log("The clustering unit will be the user, not the individual swipe row.")
    logger.log("Aggregating interactions to create one feature vector per user.")

    all_segments = sorted(df["segmento"].dropna().unique().tolist())
    all_contexts = sorted(df["recommendation_context"].dropna().unique().tolist())
    logger.log(f"Detected segments for aggregation: {', '.join(all_segments)}")
    logger.log(f"Detected recommendation contexts: {', '.join(all_contexts)}")

    max_timestamp = df["event_timestamp"].max()
    rows: list[dict] = []

    for user_id, g in df.groupby("user_id"):
        liked_df = g[g["liked"]]
        disliked_df = g[~g["liked"]]

        row: dict[str, float | int | str] = {
            "user_id": user_id,
            "total_swipes": int(len(g)),
            "right_swipe_rate": float(g["liked"].mean()),
            "left_swipe_rate": float((~g["liked"]).mean()),
            "distinct_segments_liked": int(liked_df["segmento"].nunique()),
            "distinct_genres_liked": int(liked_df["genero"].nunique()),
            "distinct_cities_liked": int(liked_df["ciudad"].nunique()),
            "avg_liked_price": safe_mean(liked_df["avg_price"]),
            "avg_disliked_price": safe_mean(disliked_df["avg_price"]),
            "avg_days_until_event_liked": safe_mean(liked_df["days_until_event"]),
            "avg_days_until_event_disliked": safe_mean(disliked_df["days_until_event"]),
            "genre_entropy_all": entropy_from_series(g["genero"]),
            "genre_entropy_liked": entropy_from_series(liked_df["genero"]),
            "city_entropy_liked": entropy_from_series(liked_df["ciudad"]),
            "recency_days": float((max_timestamp - g["event_timestamp"].max()).days),
            "activity_span_days": float((g["event_timestamp"].max() - g["event_timestamp"].min()).days),
            "sessions_count": int(g["session_id"].nunique()),
            "events_seen": int(g["event_id"].nunique()),
        }

        for segment in all_segments:
            slug = slugify(segment)
            row[f"{slug}_like_rate"] = rate_for_subset(g, "segmento", segment)
            row[f"{slug}_swipe_share"] = ratio_of_subset(g, "segmento", segment)

        for context in all_contexts:
            slug = slugify(context)
            row[f"{slug}_share"] = ratio_of_subset(g, "recommendation_context", context)

        rows.append(row)

    features = pd.DataFrame(rows).sort_values("user_id").reset_index(drop=True)
    logger.log(f"Built a user-level feature table with {len(features):,} rows.")

    logger.log("Handling missing values caused by users without likes or dislikes in some subsets.")
    numeric_cols = [c for c in features.columns if c != "user_id"]
    features[numeric_cols] = features[numeric_cols].replace([np.inf, -np.inf], np.nan)
    for col in numeric_cols:
        if features[col].isna().any():
            if col.startswith("avg_"):
                features[col] = features[col].fillna(features[col].median())
            else:
                features[col] = features[col].fillna(0.0)

    logger.log("Applying log1p to count-like variables to reduce skew and stabilize K-Means.")
    for col in [
        "total_swipes",
        "distinct_segments_liked",
        "distinct_genres_liked",
        "distinct_cities_liked",
        "sessions_count",
        "events_seen",
    ]:
        features[col] = np.log1p(features[col])

    logger.log(f"Final number of user-level features: {len(features.columns) - 1}")
    logger.log(f"Feature columns: {', '.join(c for c in features.columns if c != 'user_id')}")
    return features


def scale_features(features: pd.DataFrame, logger: VerboseLogger):
    logger.section("Step 4 - Scale Numeric Variables")
    sklearn = require_module("sklearn", "pip install scikit-learn")
    StandardScaler = sklearn.preprocessing.StandardScaler

    feature_cols = [c for c in features.columns if c != "user_id"]
    X_raw = features[feature_cols].astype(float)
    logger.log("Using StandardScaler so all features contribute on a comparable scale.")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    scaled_df = pd.DataFrame(X_scaled, columns=feature_cols, index=features.index)
    logger.log(f"Scaled feature matrix shape: {scaled_df.shape[0]} users x {scaled_df.shape[1]} features")
    return feature_cols, X_raw, scaled_df, scaler


def evaluate_kmeans(
    features: pd.DataFrame,
    scaled_df: pd.DataFrame,
    k_values: list[int],
    random_state: int,
    n_init: int,
    logger: VerboseLogger,
):
    logger.section("Step 5 - Test Multiple K Values With K-Means")
    sklearn = require_module("sklearn", "pip install scikit-learn")
    KMeans = sklearn.cluster.KMeans
    metrics = sklearn.metrics

    X = scaled_df.to_numpy()
    results: list[dict] = []
    best = None

    logger.log(
        "For each K we will fit K-Means and compute inertia, silhouette, "
        "Calinski-Harabasz and Davies-Bouldin."
    )

    for k in k_values:
        if k < 2 or k >= len(features):
            logger.log(f"Skipping invalid K={k} because it is outside the valid range.")
            continue

        logger.log(f"Fitting K-Means with k={k}, random_state={random_state}, n_init={n_init}.")
        model = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        labels = model.fit_predict(X)

        result = {
            "k": k,
            "n_clusters": int(len(set(labels))),
            "inertia": float(model.inertia_),
            "silhouette": float(metrics.silhouette_score(X, labels)),
            "calinski_harabasz": float(metrics.calinski_harabasz_score(X, labels)),
            "davies_bouldin": float(metrics.davies_bouldin_score(X, labels)),
        }
        results.append(result)
        logger.log(
            f"Results for k={k}: inertia={result['inertia']:.4f}, "
            f"silhouette={result['silhouette']:.4f}, "
            f"calinski_harabasz={result['calinski_harabasz']:.2f}, "
            f"davies_bouldin={result['davies_bouldin']:.4f}"
        )

        if best is None or result["silhouette"] > best["metrics"]["silhouette"]:
            logger.log(f"k={k} is currently the best model by silhouette score.")
            best = {
                "model": model,
                "labels": labels,
                "metrics": result,
            }

    results_df = pd.DataFrame(results).sort_values("k").reset_index(drop=True)
    if best is None:
        raise SystemExit("No valid K value was available to fit K-Means.")

    logger.log(
        f"Selected best K-Means model: k={best['metrics']['k']} "
        f"with silhouette={best['metrics']['silhouette']:.4f}"
    )
    return results_df, best


def build_cluster_profiles(features: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    prof = features.copy()
    prof["cluster_label"] = labels
    numeric_cols = [c for c in prof.columns if c not in {"user_id", "cluster_label"}]
    grouped = prof.groupby("cluster_label")[numeric_cols].mean().reset_index()
    return grouped


def build_cluster_sizes(labels: np.ndarray) -> pd.DataFrame:
    sizes = pd.Series(labels).value_counts().sort_index().rename_axis("cluster_label").reset_index(name="users")
    sizes["share"] = sizes["users"] / sizes["users"].sum()
    return sizes


def build_centroids_raw(best_model, raw_feature_df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    centers_scaled = best_model.cluster_centers_
    centroid_df = pd.DataFrame(centers_scaled, columns=feature_cols)
    centroid_df.insert(0, "cluster_label", range(len(centroid_df)))
    return centroid_df


def build_cluster_top_traits(features: pd.DataFrame, labels: np.ndarray, top_n: int = 5) -> pd.DataFrame:
    frame = features.copy()
    frame["cluster_label"] = labels
    numeric_cols = [c for c in frame.columns if c not in {"user_id", "cluster_label"}]
    global_means = frame[numeric_cols].mean()

    rows: list[dict] = []
    for label in sorted(frame["cluster_label"].unique()):
        subset = frame[frame["cluster_label"] == label]
        means = subset[numeric_cols].mean()
        deltas = (means - global_means).sort_values(ascending=False)
        top_positive = deltas.head(top_n)
        top_negative = deltas.tail(top_n).sort_values()

        for rank, (feature, delta) in enumerate(top_positive.items(), start=1):
            rows.append(
                {
                    "cluster_label": label,
                    "direction": "positive",
                    "rank": rank,
                    "feature": feature,
                    "delta_vs_global_mean": float(delta),
                }
            )
        for rank, (feature, delta) in enumerate(top_negative.items(), start=1):
            rows.append(
                {
                    "cluster_label": label,
                    "direction": "negative",
                    "rank": rank,
                    "feature": feature,
                    "delta_vs_global_mean": float(delta),
                }
            )
    return pd.DataFrame(rows)


def interpret_clusters(features: pd.DataFrame, labels: np.ndarray, top_n: int = 5) -> str:
    frame = features.copy()
    frame["cluster_label"] = labels
    numeric_cols = [c for c in frame.columns if c not in {"user_id", "cluster_label"}]
    global_means = frame[numeric_cols].mean()

    sections = ["Cluster interpretation"]
    for label in sorted(frame["cluster_label"].unique()):
        subset = frame[frame["cluster_label"] == label]
        means = subset[numeric_cols].mean()
        deltas = (means - global_means).sort_values(ascending=False)
        top_positive = deltas.head(top_n)
        top_negative = deltas.tail(top_n).sort_values()

        sections.append(
            textwrap.dedent(
                f"""
                Cluster {label}
                - users: {len(subset)}
                - strongest positive traits: {', '.join(f'{idx} ({val:+.2f})' for idx, val in top_positive.items())}
                - strongest negative traits: {', '.join(f'{idx} ({val:+.2f})' for idx, val in top_negative.items())}
                """
            ).strip()
        )
    return "\n\n".join(sections)


def create_human_summary(
    clean_metrics: dict,
    best_metrics: dict,
    sizes_df: pd.DataFrame,
    interpretation_text: str,
) -> str:
    sizes_lines = []
    for _, row in sizes_df.iterrows():
        sizes_lines.append(
            f"- Cluster {int(row['cluster_label'])}: {int(row['users'])} users ({row['share']:.2%})"
        )

    return "\n".join(
        [
            "Cleaning summary",
            json.dumps(clean_metrics, indent=2),
            "",
            "Selected K-Means model",
            f"- Best k: {best_metrics['k']}",
            f"- Silhouette: {best_metrics['silhouette']:.4f}",
            f"- Calinski-Harabasz: {best_metrics['calinski_harabasz']:.2f}",
            f"- Davies-Bouldin: {best_metrics['davies_bouldin']:.4f}",
            f"- Inertia: {best_metrics['inertia']:.4f}",
            "",
            "Cluster sizes",
            *sizes_lines,
            "",
            interpretation_text,
        ]
    )


def save_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def persist_outputs(
    output_dir: Path,
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    features: pd.DataFrame,
    scaled_df: pd.DataFrame,
    feature_cols: list[str],
    kmeans_results: pd.DataFrame,
    best: dict,
    logger: VerboseLogger,
) -> None:
    logger.section("Step 6 - Write Output Files")
    logger.log("Saving intermediate and final artifacts so the clustering can be audited later.")

    assignments = features[["user_id"]].copy()
    assignments["cluster_label"] = best["labels"]

    profiles = build_cluster_profiles(features, best["labels"])
    sizes = build_cluster_sizes(best["labels"])
    top_traits = build_cluster_top_traits(features, best["labels"])
    centroids_scaled = pd.DataFrame(best["model"].cluster_centers_, columns=feature_cols)
    centroids_scaled.insert(0, "cluster_label", range(len(centroids_scaled)))
    interpretation_text = interpret_clusters(features, best["labels"])
    report_text = create_human_summary({}, best["metrics"], sizes, interpretation_text)

    # Rebuild report with actual cleaning metrics later in main.
    raw_df.to_csv(output_dir / "raw_interactions_snapshot.csv", index=False)
    clean_df.to_csv(output_dir / "clean_interactions.csv", index=False)
    features.to_csv(output_dir / "user_features.csv", index=False)
    scaled_with_user = pd.concat([features[["user_id"]], scaled_df], axis=1)
    scaled_with_user.to_csv(output_dir / "scaled_user_features.csv", index=False)
    pd.DataFrame({"feature": feature_cols}).to_csv(output_dir / "feature_list.csv", index=False)
    kmeans_results.to_csv(output_dir / "kmeans_metrics.csv", index=False)
    assignments.to_csv(output_dir / "kmeans_assignments.csv", index=False)
    profiles.to_csv(output_dir / "kmeans_cluster_profiles.csv", index=False)
    sizes.to_csv(output_dir / "kmeans_cluster_sizes.csv", index=False)
    centroids_scaled.to_csv(output_dir / "kmeans_cluster_centroids_scaled.csv", index=False)
    top_traits.to_csv(output_dir / "kmeans_cluster_top_traits.csv", index=False)

    logger.log(f"Saved: {output_dir / 'raw_interactions_snapshot.csv'}")
    logger.log(f"Saved: {output_dir / 'clean_interactions.csv'}")
    logger.log(f"Saved: {output_dir / 'user_features.csv'}")
    logger.log(f"Saved: {output_dir / 'scaled_user_features.csv'}")
    logger.log(f"Saved: {output_dir / 'feature_list.csv'}")
    logger.log(f"Saved: {output_dir / 'kmeans_metrics.csv'}")
    logger.log(f"Saved: {output_dir / 'kmeans_assignments.csv'}")
    logger.log(f"Saved: {output_dir / 'kmeans_cluster_profiles.csv'}")
    logger.log(f"Saved: {output_dir / 'kmeans_cluster_sizes.csv'}")
    logger.log(f"Saved: {output_dir / 'kmeans_cluster_centroids_scaled.csv'}")
    logger.log(f"Saved: {output_dir / 'kmeans_cluster_top_traits.csv'}")


def main() -> None:
    args = parse_args()
    logger = VerboseLogger(lines=[])

    logger.section("K-Means Clustering Workflow")
    logger.log("This script will run a complete user clustering workflow using only K-Means.")
    logger.log("It is intentionally verbose so that each stage of the pipeline is easy to follow.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.log(f"Output directory ready at: {output_dir}")

    input_path = Path(args.input)
    k_values = [int(x.strip()) for x in args.k_range.split(",") if x.strip()]
    logger.log(f"K values that will be tested: {k_values}")
    logger.log(f"K-Means random_state: {args.random_state}")
    logger.log(f"K-Means n_init: {args.n_init}")

    raw_df = read_input_csv(input_path, logger)
    clean_df, clean_metrics = clean_data(raw_df, logger)
    features = build_user_features(clean_df, logger)
    feature_cols, _raw_feature_matrix, scaled_df, _scaler = scale_features(features, logger)
    kmeans_results, best = evaluate_kmeans(
        features=features,
        scaled_df=scaled_df,
        k_values=k_values,
        random_state=args.random_state,
        n_init=args.n_init,
        logger=logger,
    )

    persist_outputs(
        output_dir=output_dir,
        raw_df=raw_df,
        clean_df=clean_df,
        features=features,
        scaled_df=scaled_df,
        feature_cols=feature_cols,
        kmeans_results=kmeans_results,
        best=best,
        logger=logger,
    )

    logger.section("Step 7 - Final Human-Readable Summary")
    sizes_df = build_cluster_sizes(best["labels"])
    interpretation_text = interpret_clusters(features, best["labels"])
    report_text = create_human_summary(clean_metrics, best["metrics"], sizes_df, interpretation_text)
    save_text(output_dir / "clustering_report.txt", report_text)
    logger.log(f"Saved: {output_dir / 'clustering_report.txt'}")

    logger.section("Step 8 - Persist Execution Log")
    logger.log("Writing the verbose execution log so the whole run can be reviewed later.")
    logger.write(output_dir / "execution_log.txt")
    logger.log("Done. K-Means clustering workflow finished successfully.")


if __name__ == "__main__":
    main()
