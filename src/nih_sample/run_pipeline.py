from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.common.config import (
    ensure_output_dirs,
    load_config,
)
from src.common.hashing import (
    find_exact_duplicates,
    find_near_duplicates,
    perceptual_hashes,
    sha256_file,
)
from src.common.image_metrics import (
    compute_image_metrics,
)
from src.common.ml_quality import (
    add_anomaly_scores,
    write_feature_clusters,
    write_patient_groups,
)
from src.common.reporting import (
    label_counts,
    write_quality_outputs,
    write_datasheet,
    write_metadata_schema,
)
from src.common.visualization import (
    save_duplicate_comparisons,
    save_manifest_samples,
    save_quality_charts,
)
from src.nih_sample.build_manifest import (
    build_manifest,
)
from src.nih_sample.validate_metadata import (
    validate_metadata,
)


def _metric_row(args):

    path, thresholds, resize_max_side = args

    result = compute_image_metrics(
        path,
        thresholds,
        resize_max_side,
    )

    data = result.to_dict()

    sha = ""
    phash = ""
    dhash = ""

    if result.readable:

        try:

            sha = sha256_file(
                path
            )

            phash, dhash = (
                perceptual_hashes(
                    path,
                    resize_max_side,
                )
            )

        except Exception as exc:

            data["hash_error"] = str(
                exc
            )

    data.update(
        {
            "sha256": sha,
            "phash": phash,
            "dhash": dhash,
        }
    )

    return data


def run(
    config_path: str,
) -> None:

    cfg = load_config(
        config_path
    )

    ensure_output_dirs(
        cfg
    )

    processed = Path(
        cfg["processed_root"]
    )

    # ==============================================================
    # STEP 1 — Build image/CSV manifest
    # ==============================================================

    manifest = build_manifest(
        config_path
    )

    # ==============================================================
    # STEP 2 — Metadata validation
    # ==============================================================

    validation = validate_metadata(
        manifest,
        config_path,
    )

    validation.to_csv(
        processed
        / "validation_issues.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    # ==============================================================
    # STEP 3 — Image metrics + hashes
    # ==============================================================

    targets = [
        (
            p,
            cfg["quality_thresholds"],
            cfg["hashing"].get(
                "resize_max_side",
                512,
            ),
        )
        for p in manifest.loc[
            manifest["image_found"],
            "image_path",
        ]
    ]

    rows = []

    with ThreadPoolExecutor(
        max_workers=8
    ) as pool:

        for data in tqdm(
            pool.map(
                _metric_row,
                targets,
            ),
            total=len(targets),
            desc="Image QC",
        ):

            rows.append(
                data
            )

    metrics_df = pd.DataFrame(
        rows
    )

    if not metrics_df.empty:

        metrics_df["image_id"] = (
            metrics_df[
                "image_path"
            ]
            .map(
                lambda x:
                    Path(x).stem
            )
        )

    metrics_df.to_csv(
        processed
        / "image_metrics.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    # ==============================================================
    # STEP 4 — Duplicates
    # ==============================================================

    exact = (
        find_exact_duplicates(
            metrics_df
        )
        if not metrics_df.empty
        else []
    )

    near = (
        find_near_duplicates(
            metrics_df,
            distance=cfg[
                "hashing"
            ].get(
                "near_duplicate_distance",
                6,
            ),
            prefix_hex=cfg[
                "hashing"
            ].get(
                "bucket_prefix_hex",
                4,
            ),
        )
        if not metrics_df.empty
        else []
    )

    duplicates_df = pd.DataFrame(
        exact + near
    )

    duplicates_df.to_csv(
        processed
        / "duplicates.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    # ==============================================================
    # STEP 5 — Merge image metrics back into manifest
    # ==============================================================

    metric_columns = [
        "image_id",
        "readable",
        "width",
        "height",
        "aspect_ratio",
        "median_pixel",
        "p01_pixel",
        "p99_pixel",
        "dark_pixel_ratio",
        "bright_pixel_ratio",
        "pixel_entropy",
        "unique_pixel_ratio",
        "unique_pixel_count",
        "edge_density",
        "noise_estimate",
        "background_ratio",
        "border_dark_ratio",
        "blur_score",
        "contrast",
        "clip_low_percent",
        "clip_high_percent",
        "nonzero_ratio",
        "quality_status",
        "quality_flags",
        "sha256",
        "phash",
        "dhash",
    ]

    merged = manifest.merge(
        metrics_df[
            metric_columns
        ],
        on="image_id",
        how="left",
        suffixes=(
            "",
            "_metric",
        ),
    )

    # ==============================================================
    # STEP 6 — Validation flags
    # ==============================================================

    if not validation.empty:

        issue_map = (
            validation
            .groupby("image_id")[
                "reason_code"
            ]
            .apply(
                lambda s:
                    "|".join(
                        sorted(
                            set(s)
                        )
                    )
            )
            .to_dict()
        )

    else:

        issue_map = {}

    merged[
        "validation_flags"
    ] = (
        merged[
            "image_id"
        ]
        .map(issue_map)
        .fillna("")
    )

    # ==============================================================
    # STEP 7 — Duplicate flags
    # ==============================================================

    duplicate_flags = {}

    if not duplicates_df.empty:

        for _, dup in (
            duplicates_df.iterrows()
        ):

            if (
                dup.get(
                    "duplicate_type"
                )
                == "DUPLICATE"
            ):

                duplicate_flags.setdefault(
                    str(
                        dup["image_id"]
                    ),
                    set(),
                ).add(
                    "DUPLICATE"
                )

            elif (
                dup.get(
                    "duplicate_type"
                )
                == "NEAR_DUPLICATE"
            ):

                duplicate_flags.setdefault(
                    str(
                        dup[
                            "image_id_a"
                        ]
                    ),
                    set(),
                ).add(
                    "NEAR_DUPLICATE"
                )

                duplicate_flags.setdefault(
                    str(
                        dup[
                            "image_id_b"
                        ]
                    ),
                    set(),
                ).add(
                    "NEAR_DUPLICATE"
                )

    merged[
        "duplicate_flags"
    ] = merged[
        "image_id"
    ].map(
        lambda x:
            "|".join(
                sorted(
                    duplicate_flags.get(
                        str(x),
                        set(),
                    )
                )
            )
    )

    merged = add_anomaly_scores(
        merged,
        processed / "ml",
    )

    write_patient_groups(merged, processed / "ml")
    write_feature_clusters(merged, processed / "ml")

    # ==============================================================
    # STEP 8 — Final QC state
    # ==============================================================

    available = (
        merged[
            "image_found"
        ]
        .fillna(False)
        .astype(bool)
    )

    has_qc_issue = (
        merged[
            "ambiguous_match"
        ]
        .fillna(False)
        .astype(bool)

        |

        merged[
            "quality_status"
        ].isin(
            [
                "REVIEW",
                "INVALID",
            ]
        )

        |

        merged[
            "validation_flags"
        ].fillna("").ne("")

        |

        merged[
            "duplicate_flags"
        ].fillna("").ne("")

        |

        merged[
            "anomaly_flag"
        ].fillna(False).astype(bool)
    )

    merged[
        "needs_review"
    ] = (
        available
        & has_qc_issue
    )

    merged[
        "qc_status"
    ] = "UNAVAILABLE"

    merged.loc[
        available
        & ~has_qc_issue,
        "qc_status",
    ] = "PASS"

    merged.loc[
        available
        & has_qc_issue,
        "qc_status",
    ] = "REVIEW"

    merged.to_csv(
        processed
        / "cleaned_manifest.csv",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    write_quality_outputs(
        processed,
        merged,
        validation,
        duplicates_df,
        source_manifest=manifest,
        label_counts_df=label_counts(merged),
    )

    # ==============================================================
    # STEP 9 — Visual examples
    # ==============================================================

    save_manifest_samples(
        merged,
        Path(
            cfg["project_root"]
        )
        / "reports"
        / "visualizations"
        / cfg["dataset_name"],
        n=12,
    )

    save_quality_charts(
        merged,
        metrics_df,
        Path(cfg["project_root"])
        / "reports"
        / "visualizations"
        / cfg["dataset_name"],
    )

    save_duplicate_comparisons(
        duplicates_df,
        Path(cfg["project_root"])
        / "reports"
        / "duplicate_comparisons"
        / cfg["dataset_name"],
    )

    # ==============================================================
    # STEP 10 — Datasheet
    # ==============================================================

    write_datasheet(
        cfg["datasheet_path"],
        cfg["dataset_name"],
        cfg,
        merged,
        validation,
    )

    # ==============================================================
    # STEP 11 — Metadata schema
    # ==============================================================

    write_metadata_schema(
        Path(
            cfg["project_root"]
        )
        / "outputs"
        / "metadata_schema.json",
        merged,
    )

    print(
        f"[{cfg['dataset_name']}] complete"
    )

    print(
        f"Manifest: "
        f"{processed / 'manifest.csv'}"
    )

    print(
        f"Image metrics: "
        f"{processed / 'image_metrics.csv'}"
    )

    print(
        f"Duplicates: "
        f"{processed / 'duplicates.csv'}"
    )

    print(
        f"Cleaned manifest: "
        f"{processed / 'cleaned_manifest.csv'}"
    )

    print(
        f"Validation issues: "
        f"{len(validation):,}"
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        default="configs/nih_sample.yaml",
    )

    args = parser.parse_args()

    run(
        args.config
    )