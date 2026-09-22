import pandas as pd

from src.nih_sample.validate_metadata import (
    validate_metadata,
)


def test_invalid_age_and_no_finding_conflict(
    tmp_path,
):

    image_root = (
        tmp_path
        / "images"
    )

    image_root.mkdir()

    config_dir = (
        tmp_path
        / "configs"
    )

    config_dir.mkdir()

    config = (
        config_dir
        / "nih.yaml"
    )

    config.write_text(
        """dataset_name: nih_sample
label_source: csv
image_root: images
labels_csv: labels.csv
processed_root: processed
datasheet_path: datasheet.md
separator: "|"
image_filename_column: Image Index
label_column: Finding Labels
age_column: Patient Age
gender_column: Patient Gender
view_column: View Position
patient_id_column: Patient ID
allowed_gender: [M, F]
allowed_view_position: [AP, PA]
""",
        encoding="utf-8",
    )

    manifest = pd.DataFrame(
        [
            {
                "Image Index":
                    "x.png",

                "Finding Labels":
                    "No Finding|Mass",

                "image_id":
                    "x",

                "image_found":
                    False,

                "image_match_count":
                    0,

                "ambiguous_match":
                    False,

                "Patient Age":
                    "411Y",

                "Patient Gender":
                    "M",

                "View Position":
                    "PA",
            }
        ]
    )

    issues = validate_metadata(
        manifest,
        str(config),
    )

    codes = set(
        issues[
            "reason_code"
        ].tolist()
    )

    assert (
        "INVALID_AGE"
        in codes
    )

    assert (
        "NO_FINDING_CONFLICT"
        in codes
    )

    assert (
        "MISSING_IMAGE"
        in codes
    )