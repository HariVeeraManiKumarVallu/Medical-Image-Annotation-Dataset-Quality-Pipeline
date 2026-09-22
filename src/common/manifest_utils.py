from __future__ import annotations

from pathlib import Path

import pandas as pd


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


def normalize_image_key(value: str) -> str:
    """
    Convert an image filename/path to a normalized filename stem.

    Example:

    00030712_000.png
    /folder/00030712_000.png

    both become:

    00030712_000
    """

    return Path(str(value).strip()).stem.lower()


def discover_images(image_root: str | Path) -> pd.DataFrame:
    """
    Recursively discover every image below image_root.
    """

    image_root = Path(image_root)

    records = []

    if not image_root.exists():
        return pd.DataFrame(
            columns=[
                "image_id",
                "image_path",
                "relative_path",
                "parent_label",
                "image_key",
            ]
        )

    for path in sorted(image_root.rglob("*")):

        if not path.is_file():
            continue

        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        records.append(
            {
                "image_id": path.stem,
                "image_path": str(path.resolve()),
                "relative_path": str(path.relative_to(image_root)),
                "parent_label": (
                    path.parent.name
                    if path.parent != image_root
                    else ""
                ),
                "image_key": normalize_image_key(path.name),
            }
        )

    return pd.DataFrame(records)


def build_image_lookup(
    images_df: pd.DataFrame,
) -> dict[str, list[str]]:
    """
    Map normalized image filename -> possible local files.

    Multiple candidates are kept because silently selecting one
    would create an incorrect metadata/image connection.
    """

    lookup: dict[str, list[str]] = {}

    for _, row in images_df.iterrows():

        key = row["image_key"]

        lookup.setdefault(key, []).append(
            row["image_path"]
        )

    return lookup


def parse_labels(
    value,
    separator: str = "|",
) -> list[str]:

    if pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    return [
        x.strip()
        for x in text.split(separator)
        if x.strip()
    ]