from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_config
from src.common.manifest_utils import (
    build_image_lookup,
    discover_images,
    normalize_image_key,
    parse_labels,
)
from src.nih_sample.schema import validate_schema


def build_manifest(
    config_path: str,
) -> pd.DataFrame:

    cfg = load_config(
        config_path
    )

    labels_path = Path(
        cfg["labels_csv"]
    )

    if not labels_path.exists():

        raise FileNotFoundError(
            f"NIH CSV not found: "
            f"{labels_path}"
        )

    # --------------------------------------------------------------
    # Read metadata CSV
    # --------------------------------------------------------------

    metadata = pd.read_csv(
        labels_path
    )

    # --------------------------------------------------------------
    # Validate source schema
    # --------------------------------------------------------------

    validate_schema(
        metadata
    )

    # --------------------------------------------------------------
    # Recursively discover actual image files
    # --------------------------------------------------------------

    images = discover_images(
        cfg["image_root"]
    )

    lookup = build_image_lookup(
        images
    )

    records = []

    # --------------------------------------------------------------
    # Connect each CSV row to its actual image
    # --------------------------------------------------------------

    for _, row in metadata.iterrows():

        image_key = normalize_image_key(
            row[
                cfg[
                    "image_filename_column"
                ]
            ]
        )

        candidates = lookup.get(
            image_key,
            [],
        )

        if len(candidates) == 1:
            image_path = candidates[0]
        else:
            image_path = ""

        labels = parse_labels(
            row[
                cfg[
                    "label_column"
                ]
            ],
            cfg.get(
                "separator",
                "|",
            ),
        )

        record = {
            **row.to_dict(),

            "dataset": cfg[
                "dataset_name"
            ],

            "image_id": Path(
                str(
                    row[
                        cfg[
                            "image_filename_column"
                        ]
                    ]
                )
            ).stem,

            "image_path": image_path,

            "image_found": (
                len(candidates) == 1
            ),

            "image_match_count": len(
                candidates
            ),

            "ambiguous_match": (
                len(candidates) > 1
            ),

            "labels": "|".join(
                labels
            ),

            "label_count": len(
                labels
            ),

            "match_status": (
                "MATCHED"
                if len(candidates) == 1
                else
                (
                    "AMBIGUOUS"
                    if len(candidates) > 1
                    else "MISSING"
                )
            ),
        }

        records.append(
            record
        )

    manifest = pd.DataFrame(
        records
    )

    output = (
        Path(
            cfg["processed_root"]
        )
        / "manifest.csv"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest.to_csv(
        output,
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    return manifest