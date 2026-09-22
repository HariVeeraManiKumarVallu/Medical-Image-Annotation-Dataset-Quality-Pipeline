from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_grayscale(
    path: str | Path,
) -> np.ndarray:

    image = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        raise ValueError(
            f"Could not decode image: {path}"
        )

    return image


def normalize_8bit(
    image: np.ndarray,
) -> np.ndarray:

    if image.dtype != np.uint8:

        image = cv2.normalize(
            image,
            None,
            0,
            255,
            cv2.NORM_MINMAX,
        ).astype(np.uint8)

    else:

        image = image.copy()

    return image


def clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    grid_size: int = 8,
) -> np.ndarray:

    image = normalize_8bit(image)

    operation = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=(
            grid_size,
            grid_size,
        ),
    )

    return operation.apply(image)


def canny_edges(
    image: np.ndarray,
    low: int = 50,
    high: int = 150,
) -> np.ndarray:

    image = normalize_8bit(image)

    return cv2.Canny(
        image,
        low,
        high,
    )


def otsu_threshold(
    image: np.ndarray,
) -> np.ndarray:

    image = normalize_8bit(image)

    _, thresholded = cv2.threshold(
        image,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    return thresholded