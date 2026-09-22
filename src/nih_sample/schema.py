from __future__ import annotations

import pandas as pd
import pandera.pandas as pa


NIH_COLUMNS = [
    "Image Index",
    "Finding Labels",
    "Follow-up #",
    "Patient ID",
    "Patient Age",
    "Patient Gender",
    "View Position",
    "OriginalImageWidth",
    "OriginalImageHeight",
    "OriginalImagePixelSpacing_x",
    "OriginalImagePixelSpacing_y",
]


def validate_schema(
    df: pd.DataFrame,
) -> None:

    if {
        "Image Index",
        "Finding Labels",
        "Patient ID",
        "Patient Age",
        "Patient Gender",
        "View Position",
    }.issubset(df.columns) and "Follow-up #" not in df.columns:
        from src.chest_condition.schema import validate_schema as validate_chest_schema

        validate_chest_schema(df)
        return

    schema = pa.DataFrameSchema(
        {
            "Image Index": pa.Column(
                str,
                nullable=False,
            ),

            "Finding Labels": pa.Column(
                str,
                nullable=True,
            ),

            "Follow-up #": pa.Column(
                int,
                nullable=False,
            ),

            "Patient ID": pa.Column(
                int,
                nullable=False,
            ),

            "Patient Age": pa.Column(
                str,
                nullable=False,
            ),

            "Patient Gender": pa.Column(
                str,
                nullable=False,
            ),

            "View Position": pa.Column(
                str,
                nullable=False,
            ),

            "OriginalImageWidth": pa.Column(
                int,
                nullable=False,
            ),

            "OriginalImageHeight": pa.Column(
                int,
                nullable=False,
            ),

            "OriginalImagePixelSpacing_x": pa.Column(
                float,
                nullable=False,
            ),

            "OriginalImagePixelSpacing_y": pa.Column(
                float,
                nullable=False,
            ),
        },

        strict=False,

        coerce=True,
    )

    schema.validate(
        df,
        lazy=True,
    )