from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path

from PIL import Image


def sha256_file(
    path: str | Path,
    chunk_size: int = 1024 * 1024,
) -> str:

    digest = hashlib.sha256()

    with Path(path).open("rb") as f:

        while chunk := f.read(chunk_size):

            digest.update(chunk)

    return digest.hexdigest()


def perceptual_hashes(
    path: str | Path,
    resize_max_side: int = 512,
) -> tuple[str, str]:

    import imagehash

    with Image.open(path) as image:

        image = image.convert("L")

        if max(image.size) > resize_max_side:

            image.thumbnail(
                (
                    resize_max_side,
                    resize_max_side,
                ),
                Image.Resampling.LANCZOS,
            )

        phash = str(
            imagehash.phash(image)
        )

        dhash = str(
            imagehash.dhash(image)
        )

        return phash, dhash


def hamming_distance(
    hex_a: str,
    hex_b: str,
) -> int:

    import imagehash

    return (
        imagehash.hex_to_hash(hex_a)
        -
        imagehash.hex_to_hash(hex_b)
    )


def find_exact_duplicates(df):

    groups = df.groupby(
        "sha256",
        dropna=False,
    )

    records = []

    for sha, group in groups:

        if not sha or len(group) < 2:
            continue

        for _, row in group.iterrows():

            records.append(
                {
                    "duplicate_type": "DUPLICATE",
                    "group_hash": sha,
                    "image_id": row["image_id"],
                    "image_path": row["image_path"],
                }
            )

    return records


def find_near_duplicates(
    df,
    distance: int = 6,
    prefix_hex: int = 4,
    max_bucket_size: int = 1000,
):

    work = df.dropna(
        subset=["phash"]
    ).copy()

    if work.empty:
        return []

    work["bucket"] = (
        work["phash"]
        .str[:prefix_hex]
    )

    pairs = []

    for _, group in work.groupby("bucket"):

        # Avoid a huge O(N²) bucket.
        if len(group) > max_bucket_size:
            group = group.head(
                max_bucket_size
            )

        rows = list(
            group.to_dict("records")
        )

        for left, right in combinations(
            rows,
            2,
        ):

            d = hamming_distance(
                left["phash"],
                right["phash"],
            )

            if d <= distance:

                pairs.append(
                    {
                        "duplicate_type": "NEAR_DUPLICATE",
                        "hamming_distance": int(d),
                        "image_id_a": left["image_id"],
                        "image_path_a": left["image_path"],
                        "image_id_b": right["image_id"],
                        "image_path_b": right["image_path"],
                    }
                )

    return pairs