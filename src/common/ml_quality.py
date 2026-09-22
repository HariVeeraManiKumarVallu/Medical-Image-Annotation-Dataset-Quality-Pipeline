from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "width",
    "height",
    "aspect_ratio",
    "blur_score",
    "contrast",
    "pixel_entropy",
    "unique_pixel_ratio",
    "dark_pixel_ratio",
    "bright_pixel_ratio",
    "nonzero_ratio",
]


def _feature_frame(manifest: pd.DataFrame) -> pd.DataFrame:
    available = [column for column in FEATURES if column in manifest.columns]
    values = manifest[available].apply(pd.to_numeric, errors="coerce")
    return values.fillna(values.median()).fillna(0.0)


def add_anomaly_scores(
    manifest: pd.DataFrame,
    output_dir: str | Path,
) -> pd.DataFrame:
    result = manifest.copy()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result["anomaly_score"] = 0.0
    result["anomaly_flag"] = False

    if len(result) < 10 or "image_found" not in result.columns:
        return result

    available = result["image_found"].astype(str).str.lower().isin(
        ["true", "1", "yes"]
    )
    indices = result.index[available]

    if len(indices) < 10:
        return result

    features = _feature_frame(result.loc[indices])
    model = IsolationForest(
        contamination="auto",
        random_state=42,
        n_estimators=100,
    )
    model.fit(features)

    scores = model.decision_function(features)
    flags = model.predict(features) == -1
    result.loc[indices, "anomaly_score"] = scores
    result.loc[indices, "anomaly_flag"] = flags

    result.loc[indices, ["image_id", "anomaly_score", "anomaly_flag"]].to_csv(
        output_dir / "anomaly_predictions.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    return result




def write_patient_groups(
    manifest: pd.DataFrame,
    output_dir: str | Path,
) -> None:

    if "Patient ID" not in manifest.columns:
        return

    grouped = (
        manifest.groupby("Patient ID", dropna=False)
        .agg(
            image_count=("image_id", "nunique"),
            label_count=("label_count", "sum"),
            matched_count=("image_found", "sum"),
        )
        .reset_index()
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    grouped.to_csv(
        Path(output_dir) / "patient_groups.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )


def write_feature_clusters(
    manifest: pd.DataFrame,
    output_dir: str | Path,
    n_clusters: int = 8,
) -> None:

    if len(manifest) < n_clusters or "image_id" not in manifest.columns:
        return

    features = _feature_frame(manifest)
    model = make_pipeline(
        StandardScaler(),
        KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
        ),
    )
    clusters = manifest[["image_id"]].copy()
    clusters["feature_cluster"] = model.fit_predict(features)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    clusters.to_csv(
        Path(output_dir) / "feature_clusters.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )
