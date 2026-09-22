from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.common.config import load_config
from src.common.manifest_utils import (
    discover_images,
    parse_labels,
)


def parse_age(
    value,
) -> float | None:

    if pd.isna(value):
        return None

    match = re.search(
        r"\d+",
        str(value),
    )

    return (
        float(match.group())
        if match
        else None
    )


def validate_metadata(
    manifest: pd.DataFrame,
    config_path: str,
) -> pd.DataFrame:

    cfg = load_config(
        config_path
    )

    issues = []

    # --------------------------------------------------------------
    # Duplicate metadata identifiers
    # --------------------------------------------------------------

    image_counts = (
        manifest[
            "Image Index"
        ]
        .value_counts()
    )

    for image_name, count in (
        image_counts[
            image_counts > 1
        ].items()
    ):

        issues.append(
            {
                "image_id": Path(
                    str(image_name)
                ).stem,

                "reason_code":
                    "METADATA_DUPLICATE",

                "detail":
                    f"Appears {count} times.",
            }
        )

    # --------------------------------------------------------------
    # Row-level validation
    # --------------------------------------------------------------

    for _, row in manifest.iterrows():

        image_id = str(
            row["image_id"]
        )

        labels = parse_labels(
            row.get(
                cfg["label_column"],
                "",
            ),
            cfg.get(
                "separator",
                "|",
            ),
        )

        age = parse_age(
            row.get(
                cfg["age_column"]
            )
        )

        gender = str(
            row.get(
                cfg["gender_column"],
                "",
            )
        ).strip()

        view = str(
            row.get(
                cfg["view_column"],
                "",
            )
        ).strip()

        # ----------------------------------------------------------
        # Age validation
        # ----------------------------------------------------------

        if (
            age is None
            or age < 0
            or age > 100
        ):

            issues.append(
                {
                    "image_id": image_id,
                    "reason_code": "INVALID_AGE",
                    "detail": (
                        f"Age="
                        f"{row.get(cfg['age_column'])}"
                    ),
                }
            )

        # ----------------------------------------------------------
        # Gender validation
        # ----------------------------------------------------------

        if gender not in set(
            cfg.get(
                "allowed_gender",
                [],
            )
        ):

            issues.append(
                {
                    "image_id": image_id,
                    "reason_code": "INVALID_GENDER",
                    "detail": gender,
                }
            )

        # ----------------------------------------------------------
        # View validation
        # ----------------------------------------------------------

        if view not in set(
            cfg.get(
                "allowed_view_position",
                [],
            )
        ):

            issues.append(
                {
                    "image_id": image_id,
                    "reason_code": "INVALID_VIEW",
                    "detail": view,
                }
            )

        # ----------------------------------------------------------
        # Empty labels
        # ----------------------------------------------------------

        if not labels:

            issues.append(
                {
                    "image_id": image_id,
                    "reason_code": "EMPTY_LABEL",
                    "detail": (
                        "No label value."
                    ),
                }
            )

        # ----------------------------------------------------------
        # Label spelling
        # ----------------------------------------------------------

        allowed_labels = set(
            cfg.get(
                "allowed_labels",
                [],
            )
        )

        if allowed_labels:

            unknown = [
                label
                for label in labels
                if label not in allowed_labels
            ]

            if unknown:

                issues.append(
                    {
                        "image_id": image_id,
                        "reason_code":
                            "LABEL_SPELLING",
                        "detail":
                            "Unknown label(s): "
                            + "|".join(
                                unknown
                            ),
                    }
                )

        # ----------------------------------------------------------
        # No Finding conflict
        # ----------------------------------------------------------

        if (
            "No Finding" in labels
            and len(labels) > 1
        ):

            issues.append(
                {
                    "image_id": image_id,
                    "reason_code":
                        "NO_FINDING_CONFLICT",
                    "detail":
                        "No Finding combined "
                        "with another label.",
                }
            )

        # ----------------------------------------------------------
        # Image connection validation
        # ----------------------------------------------------------

        if not bool(
            row.get(
                "image_found",
                False,
            )
        ):

            code = (
                "AMBIGUOUS"
                if int(
                    row.get(
                        "image_match_count",
                        0,
                    )
                ) > 1
                else "MISSING_IMAGE"
            )

            issues.append(
                {
                    "image_id": image_id,
                    "reason_code": code,
                    "detail":
                        "match_count="
                        f"{row.get('image_match_count', 0)}",
                }
            )

    # --------------------------------------------------------------
    # Orphan local images
    # --------------------------------------------------------------

    images = discover_images(
        cfg["image_root"]
    )

    csv_keys = set(
        manifest[
            "Image Index"
        ].map(
            lambda x:
                Path(
                    str(x)
                ).stem.lower()
        )
    )

    for _, row in images.iterrows():

        if row["image_key"] not in csv_keys:

            issues.append(
                {
                    "image_id":
                        row["image_id"],

                    "reason_code":
                        "ORPHAN_IMAGE",

                    "detail":
                        row["image_path"],
                }
            )

    return pd.DataFrame(
        issues,
        columns=[
            "image_id",
            "reason_code",
            "detail",
        ],
    )