from __future__ import annotations

import pandas as pd
import pandera.pandas as pa


def validate_schema(df: pd.DataFrame) -> None:
    schema = pa.DataFrameSchema(
        {
            "Image Index": pa.Column(str, nullable=False),
            "Finding Labels": pa.Column(str, nullable=True),
            "Patient ID": pa.Column(int, nullable=False),
            "Patient Age": pa.Column(int, nullable=False),
            "Patient Gender": pa.Column(str, nullable=False),
            "View Position": pa.Column(str, nullable=False),
        },
        strict=False,
        coerce=True,
    )
    schema.validate(df, lazy=True)