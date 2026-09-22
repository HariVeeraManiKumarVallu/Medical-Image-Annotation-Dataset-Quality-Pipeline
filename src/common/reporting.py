from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _write_csv(
    df: pd.DataFrame,
    path: str | Path,
) -> None:

    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )


def _quality_score(row: pd.Series) -> float:

    score = 100.0
    penalties = {
        "BLUR": 15,
        "LOW_CONTRAST": 10,
        "CLIP_LOW": 10,
        "CLIP_HIGH": 10,
        "BLANK": 30,
        "LOW_PIXEL_VARIETY": 20,
        "LOW_RESOLUTION": 15,
        "EXTREME_ASPECT_RATIO": 10,
        "CORRUPT_IMAGE": 100,
    }

    for flag, penalty in penalties.items():
        if flag in str(row.get("quality_flags", "")):
            score -= penalty

    if str(row.get("validation_flags", "")):
        score -= 20
    if str(row.get("duplicate_flags", "")):
        score -= 15
    if str(row.get("match_status", "")) != "MATCHED":
        score -= 40

    return max(0.0, min(100.0, score))


def _schema_drift(
    source: pd.DataFrame,
    processed: pd.DataFrame,
) -> pd.DataFrame:

    columns = sorted(set(source.columns) | set(processed.columns))
    return pd.DataFrame(
        [
            {
                "column": column,
                "in_source": column in source.columns,
                "in_processed": column in processed.columns,
                "source_dtype": str(source[column].dtype)
                if column in source.columns else "",
                "processed_dtype": str(processed[column].dtype)
                if column in processed.columns else "",
            }
            for column in columns
        ]
    )


def write_quality_outputs(
    processed_root: str | Path,
    manifest: pd.DataFrame,
    validation_df: pd.DataFrame,
    duplicates_df: pd.DataFrame,
    source_manifest: pd.DataFrame | None = None,
    label_counts_df: pd.DataFrame | None = None,
) -> None:

    processed_root = Path(processed_root)
    output_root = processed_root / "quality_outputs"
    manifest = manifest.copy()
    manifest["quality_score"] = manifest.apply(
        _quality_score,
        axis=1,
    )

    _write_csv(
        manifest,
        processed_root / "cleaned_manifest.csv",
    )

    if "qc_status" in manifest.columns:
        for status in sorted(
            manifest["qc_status"].dropna().unique()
        ):
            safe_status = str(status).lower()
            _write_csv(
                manifest[
                    manifest["qc_status"] == status
                ].copy(),
                output_root / f"{safe_status}_records.csv",
            )

    if "match_status" in manifest.columns:
        _write_csv(
            manifest[
                manifest["match_status"] == "MISSING"
            ].copy(),
            output_root / "missing_images.csv",
        )

    if not duplicates_df.empty:
        _write_csv(
            duplicates_df,
            output_root / "duplicate_images.csv",
        )

    if not validation_df.empty:
        _write_csv(
            validation_df,
            output_root / "metadata_errors.csv",
        )

    rejected = pd.DataFrame(
        columns=["image_id", "decision", "reason_codes", "comment"]
    )

    _write_csv(
        rejected,
        output_root / "rejected_records.csv",
    )

    summary = pd.DataFrame(
        {
            "metric": [
                "total_records",
                "matched_records",
                "missing_records",
                "pass_records",
                "review_records",
                "unavailable_records",
                "validation_issues",
                "duplicate_candidates",
                "average_quality_score",
            ],
            "value": [
                len(manifest),
                int((manifest.get("match_status", pd.Series(dtype=str)) == "MATCHED").sum()),
                int((manifest.get("match_status", pd.Series(dtype=str)) == "MISSING").sum()),
                int((manifest.get("qc_status", pd.Series(dtype=str)) == "PASS").sum()),
                int((manifest.get("qc_status", pd.Series(dtype=str)) == "REVIEW").sum()),
                int((manifest.get("qc_status", pd.Series(dtype=str)) == "UNAVAILABLE").sum()),
                len(validation_df),
                len(duplicates_df),
                float(manifest["quality_score"].mean())
                if not manifest.empty else 0.0,
            ],
        }
    )

    _write_csv(
        summary,
        output_root / "quality_summary.csv",
    )

    if source_manifest is not None:
        before_after = pd.DataFrame(
            {
                "metric": [
                    "source_records",
                    "processed_records",
                    "source_columns",
                    "processed_columns",
                    "validation_issues",
                    "duplicate_candidates",
                ],
                "before": [
                    len(source_manifest),
                    "",
                    len(source_manifest.columns),
                    "",
                    "",
                    "",
                ],
                "after": [
                    "",
                    len(manifest),
                    "",
                    len(manifest.columns),
                    len(validation_df),
                    len(duplicates_df),
                ],
            }
        )
        schema_drift = _schema_drift(
            source_manifest,
            manifest,
        )
        _write_csv(
            before_after,
            output_root / "before_after.csv",
        )
        _write_csv(
            schema_drift,
            output_root / "schema_drift.csv",
        )

        dataset_name = str(
            manifest["dataset"].iloc[0]
        ) if "dataset" in manifest.columns and not manifest.empty else "dataset"
        powerbi_root = (
            processed_root.parents[2]
            / "powerbi"
            / dataset_name
        )
        _write_csv(manifest, powerbi_root / "cleaned_manifest.csv")
        _write_csv(validation_df, powerbi_root / "validation_issues.csv")
        _write_csv(duplicates_df, powerbi_root / "duplicates.csv")
        _write_csv(summary, powerbi_root / "quality_summary.csv")
        _write_csv(rejected, powerbi_root / "rejected_records.csv")
        _write_csv(before_after, powerbi_root / "before_after.csv")
        _write_csv(schema_drift, powerbi_root / "schema_drift.csv")
        if label_counts_df is not None:
            _write_csv(label_counts_df, powerbi_root / "label_counts.csv")

    workbook_path = processed_root / "quality_report.xlsx"

    validation_summary = (
        validation_df["reason_code"]
        .value_counts()
        .rename_axis("reason_code")
        .reset_index(name="count")
        if "reason_code" in validation_df.columns
        else pd.DataFrame(columns=["reason_code", "count"])
    )

    status_summary = (
        manifest["qc_status"]
        .value_counts()
        .rename_axis("qc_status")
        .reset_index(name="count")
        if "qc_status" in manifest.columns
        else pd.DataFrame(columns=["qc_status", "count"])
    )

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index=False)
        status_summary.to_excel(writer, sheet_name="qc_status", index=False)
        validation_summary.to_excel(writer, sheet_name="validation", index=False)
        duplicates_df.head(10000).to_excel(
            writer,
            sheet_name="duplicates",
            index=False,
        )
        if label_counts_df is not None:
            label_counts_df.to_excel(
                writer,
                sheet_name="labels",
                index=False,
            )


def label_counts(
    manifest: pd.DataFrame,
) -> pd.DataFrame:

    if "labels" not in manifest.columns:

        return pd.DataFrame(
            columns=[
                "label",
                "count",
            ]
        )

    exploded = manifest[
        ["image_id", "labels"]
    ].copy()

    exploded["label"] = (
        exploded["labels"]
        .fillna("")
        .str.split("|")
    )

    exploded = exploded.explode(
        "label"
    )

    exploded["label"] = (
        exploded["label"]
        .astype(str)
        .str.strip()
    )

    exploded = exploded[
        exploded["label"] != ""
    ]

    if exploded.empty:

        return pd.DataFrame(
            columns=[
                "label",
                "count",
            ]
        )

    return (
        exploded.groupby("label")
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            "count",
            ascending=False,
        )
    )


def _count_status(
    manifest: pd.DataFrame,
    status: str,
) -> int:

    if manifest.empty:
        return 0

    if "match_status" not in manifest.columns:
        return 0

    return int(
        (
            manifest[
                "match_status"
            ]
            .fillna("")
            == status
        ).sum()
    )


def _count_reason(
    validation_df: pd.DataFrame,
    reason_code: str,
) -> int:

    if validation_df.empty:
        return 0

    if "reason_code" not in validation_df.columns:
        return 0

    return int(
        (
            validation_df[
                "reason_code"
            ]
            == reason_code
        ).sum()
    )


def write_datasheet(
    path: str | Path,
    dataset_name: str,
    cfg: dict,
    manifest: pd.DataFrame,
    validation_df: pd.DataFrame,
) -> None:

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_records = len(
        manifest
    )

    matched = _count_status(
        manifest,
        "MATCHED",
    )

    missing = _count_status(
        manifest,
        "MISSING",
    )

    ambiguous = _count_status(
        manifest,
        "AMBIGUOUS",
    )

    orphan = _count_reason(
        validation_df,
        "ORPHAN_IMAGE",
    )

    invalid_age = _count_reason(
        validation_df,
        "INVALID_AGE",
    )

    invalid_gender = _count_reason(
        validation_df,
        "INVALID_GENDER",
    )

    invalid_view = _count_reason(
        validation_df,
        "INVALID_VIEW",
    )

    label_spelling = _count_reason(
        validation_df,
        "LABEL_SPELLING",
    )

    no_finding_conflict = _count_reason(
        validation_df,
        "NO_FINDING_CONFLICT",
    )

    empty_label = _count_reason(
        validation_df,
        "EMPTY_LABEL",
    )

    metadata_duplicate = _count_reason(
        validation_df,
        "METADATA_DUPLICATE",
    )

    lines = [

        f"# Datasheet — {dataset_name}",

        "",

        "## Dataset purpose",

        "",

        "This project creates an image-centric dataset manifest by "
        "joining source metadata and image-level labels to locally "
        "available image files. It then applies automated metadata, "
        "image-quality, duplicate and dataset-integrity checks.",

        "",

        "## Label source",

        "",

        f"`{cfg.get('label_source', 'unknown')}`",

        "",

        "## Annotation scope",

        "",

        "The supplied label files contain image-level labels. "
        "Unless a separate bounding-box or segmentation annotation "
        "file is available, these labels are not treated as lesion "
        "coordinates, bounding boxes or segmentation masks.",

        "",

        "## Dataset coverage",

        "",

        f"Metadata records: {metadata_records:,}",

        "",

        f"Images matched to local files: {matched:,}",

        "",

        f"Metadata records without local images: {missing:,}",

        "",

        f"Ambiguous image matches: {ambiguous:,}",

        "",

        f"Orphan local images: {orphan:,}",

        "",

        "Missing local images are retained in the manifest because "
        "the metadata record exists even though the corresponding "
        "image asset is unavailable in the local subset.",

        "",

        "## Metadata QC summary",

        "",

        f"Invalid age: {invalid_age:,}",

        "",

        f"Invalid gender: {invalid_gender:,}",

        "",

        f"Invalid view position: {invalid_view:,}",

        "",

        f"Unknown label spelling: {label_spelling:,}",

        "",

        f"No Finding conflicts: {no_finding_conflict:,}",

        "",

        f"Empty labels: {empty_label:,}",

        "",

        f"Duplicate metadata records: {metadata_duplicate:,}",

        "",

        "## Automated image QC",

        "",

        "For locally available and readable images, the pipeline "
        "calculates image dimensions, blur/sharpness indicators, "
        "contrast, pixel clipping, non-zero pixel ratio and "
        "readability. It also calculates SHA-256, perceptual and "
        "difference hashes for duplicate analysis.",

        "",

        "## Duplicate analysis",

        "",

        "Exact duplicate detection uses SHA-256 file hashes. "
        "Perceptual hashing is used to identify near-duplicate "
        "candidates. Near-duplicate candidates require review and "
        "are not automatically treated as erroneous records.",

        "",

        "## Human review",

        "",

        "The reviewer interface records reviewer identity, decision, "
        "reason codes and comments. Review decisions can be compared "
        "across reviewers to measure agreement.",

        "",

        "## Privacy",

        "",

        "Treat all image data and metadata as sensitive. Keep raw "
        "data local, do not publish identifiable content, and follow "
        "the source dataset's usage and privacy requirements.",

        "",

        "## Known limitations",

        "",

        "Automated thresholds are heuristic and should be tuned using "
        "a representative human-reviewed sample. QC flags identify "
        "records for review; they do not establish clinical meaning "
        "or provide a medical diagnosis.",

        "",

        "The current local image collection may represent only a "
        "subset of the records described by the metadata file. "
        "Therefore missing-image counts should be interpreted as "
        "local asset availability findings.",

    ]

    path.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )


def write_metadata_schema(
    path: str | Path,
    manifest: pd.DataFrame,
) -> None:

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    schema = {
        "columns": [
            {
                "name": column,
                "dtype": str(
                    manifest[column].dtype
                ),
            }
            for column in manifest.columns
        ]
    }

    path.write_text(
        json.dumps(
            schema,
            indent=2,
        ),
        encoding="utf-8",
    )