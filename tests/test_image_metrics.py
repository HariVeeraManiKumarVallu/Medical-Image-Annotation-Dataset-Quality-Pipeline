from pathlib import Path

import cv2
import numpy as np

from src.common.image_metrics import (
    compute_image_metrics,
)


def test_image_metrics_valid(
    tmp_path: Path,
):

    image = np.zeros(
        (64, 64),
        dtype=np.uint8,
    )

    image[
        16:48,
        16:48
    ] = 180

    path = (
        tmp_path
        / "test.png"
    )

    assert cv2.imwrite(
        str(path),
        image,
    )

    result = compute_image_metrics(
        path,
        {
            "blur_min": 0,
            "contrast_min": 0,
            "clip_percent_max": 100,
            "blank_std_max": 0,
            "blank_nonzero_ratio_min": 0,
        },
    )

    assert result.readable is True

    assert result.width == 64

    assert result.height == 64

    assert result.aspect_ratio == 1.0

    assert result.pixel_entropy >= 0

    assert 0 < result.unique_pixel_ratio <= 1

    assert result.median_pixel == 0

    assert result.p01_pixel == 0

    assert result.p99_pixel == 180

    assert result.unique_pixel_count == 2

    assert 0 <= result.dark_pixel_ratio <= 1

    assert 0 <= result.bright_pixel_ratio <= 1

    assert 0 <= result.edge_density <= 1

    assert result.noise_estimate >= 0

    assert 0 <= result.background_ratio <= 1

    assert 0 <= result.border_dark_ratio <= 1

    assert result.quality_status in {
        "VALID",
        "REVIEW",
    }


def test_corrupt_image(
    tmp_path: Path,
):

    path = (
        tmp_path
        / "broken.png"
    )

    path.write_bytes(
        b"not an image"
    )

    result = compute_image_metrics(
        path,
        {},
    )

    assert result.readable is False

    assert (
        result.quality_status
        == "INVALID"
    )

    assert (
        "CORRUPT_IMAGE"
        in result.quality_flags
    )