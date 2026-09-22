from __future__ import annotations

from pathlib import Path

import cv2
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def save_manifest_samples(
    manifest: pd.DataFrame,
    output_dir: str | Path,
    n: int = 12,
) -> None:

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    sample = manifest[
        manifest["image_found"] == True
    ].head(n)  # noqa: E712

    for idx, row in sample.iterrows():

        image = cv2.imread(
            row["image_path"],
            cv2.IMREAD_GRAYSCALE,
        )

        if image is None:
            continue

        plt.figure(
            figsize=(7, 7)
        )

        plt.imshow(
            image,
            cmap="gray",
        )

        labels = row.get(
            "labels",
            "",
        )

        plt.title(
            f"{row['image_id']}\n"
            f"Labels: {labels}"
        )

        plt.axis("off")

        plt.tight_layout()

        plt.savefig(
            output_dir
            / f"sample_{idx}.png",
            dpi=120,
        )

        plt.close()


def save_quality_charts(
    manifest: pd.DataFrame,
    metrics_df: pd.DataFrame,
    output_dir: str | Path,
) -> None:

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if "qc_status" in manifest.columns:
        counts = manifest["qc_status"].value_counts()
        plt.figure(figsize=(7, 5))
        counts.plot(kind="bar", color="#35618f")
        plt.title("QC status")
        plt.xlabel("Status")
        plt.ylabel("Records")
        plt.tight_layout()
        plt.savefig(output_dir / "qc_status.png", dpi=140)
        plt.close()

    for column in [
        "contrast",
        "blur_score",
        "pixel_entropy",
        "unique_pixel_ratio",
        "aspect_ratio",
    ]:
        if column not in metrics_df.columns:
            continue

        values = pd.to_numeric(
            metrics_df[column],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        plt.figure(figsize=(8, 5))
        values.plot(kind="hist", bins=40, color="#4f8a6d")
        plt.title(f"{column.replace('_', ' ').title()} distribution")
        plt.xlabel(column)
        plt.ylabel("Images")
        plt.tight_layout()
        plt.savefig(output_dir / f"{column}.png", dpi=140)
        plt.close()

    if "labels" in manifest.columns:
        labels = (
            manifest["labels"]
            .fillna("")
            .str.split("|")
            .explode()
            .astype(str)
            .str.strip()
        )
        labels = labels[labels != ""]
        counts = labels.value_counts().head(20).sort_values()

        if not counts.empty:
            plt.figure(figsize=(9, 7))
            counts.plot(kind="barh", color="#ad6b3d")
            plt.title("Top labels")
            plt.xlabel("Records")
            plt.tight_layout()
            plt.savefig(output_dir / "top_labels.png", dpi=140)
            plt.close()


def save_duplicate_comparisons(
    duplicates_df: pd.DataFrame,
    output_dir: str | Path,
    max_pairs: int = 100,
) -> None:

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if duplicates_df.empty:
        return

    for index, row in duplicates_df.head(max_pairs).iterrows():
        left = cv2.imread(str(row.get("image_path_a", "")), cv2.IMREAD_GRAYSCALE)
        right = cv2.imread(str(row.get("image_path_b", "")), cv2.IMREAD_GRAYSCALE)

        if left is None or right is None:
            continue

        figure, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].imshow(left, cmap="gray")
        axes[1].imshow(right, cmap="gray")
        axes[0].set_title(str(row.get("image_id_a", "left")))
        axes[1].set_title(str(row.get("image_id_b", "right")))

        for axis in axes:
            axis.axis("off")

        figure.suptitle(
            f"{row.get('duplicate_type', 'DUPLICATE')} comparison"
        )
        figure.tight_layout()
        figure.savefig(
            output_dir / f"pair_{index}.png",
            dpi=140,
        )
        plt.close(figure)