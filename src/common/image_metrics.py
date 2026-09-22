from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ImageMetrics:

    image_path: str

    readable: bool

    width: int | None
    height: int | None
    channels: int | None
    aspect_ratio: float | None

    dtype: str | None

    min_pixel: int | None
    max_pixel: int | None
    median_pixel: float | None
    p01_pixel: float | None
    p99_pixel: float | None

    mean_pixel: float | None
    std_pixel: float | None
    pixel_entropy: float | None
    unique_pixel_ratio: float | None
    unique_pixel_count: int | None
    dark_pixel_ratio: float | None
    bright_pixel_ratio: float | None
    edge_density: float | None
    noise_estimate: float | None
    background_ratio: float | None
    border_dark_ratio: float | None

    blur_score: float | None
    contrast: float | None

    clip_low_percent: float | None
    clip_high_percent: float | None

    nonzero_ratio: float | None

    blank: bool

    quality_status: str
    quality_flags: str

    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _resize_for_metrics(
    gray: np.ndarray,
    max_side: int = 1024,
) -> np.ndarray:

    h, w = gray.shape[:2]

    largest = max(h, w)

    if largest <= max_side:
        return gray

    scale = max_side / largest

    new_width = int(w * scale)
    new_height = int(h * scale)

    return cv2.resize(
        gray,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )


def compute_image_metrics(
    image_path: str | Path,
    thresholds: dict,
    resize_max_side: int = 1024,
) -> ImageMetrics:

    image_path = str(image_path)

    try:

        # ----------------------------------------------------------
        # 1. Read actual image pixels into a NumPy array
        # ----------------------------------------------------------

        image = cv2.imread(
            image_path,
            cv2.IMREAD_UNCHANGED,
        )

        if image is None:

            return ImageMetrics(
                image_path=image_path,
                readable=False,
                width=None,
                height=None,
                channels=None,
                aspect_ratio=None,
                dtype=None,
                min_pixel=None,
                max_pixel=None,
                median_pixel=None,
                p01_pixel=None,
                p99_pixel=None,
                mean_pixel=None,
                std_pixel=None,
                pixel_entropy=None,
                unique_pixel_ratio=None,
                unique_pixel_count=None,
                dark_pixel_ratio=None,
                bright_pixel_ratio=None,
                edge_density=None,
                noise_estimate=None,
                background_ratio=None,
                border_dark_ratio=None,
                blur_score=None,
                contrast=None,
                clip_low_percent=None,
                clip_high_percent=None,
                nonzero_ratio=None,
                blank=False,
                quality_status="INVALID",
                quality_flags="CORRUPT_IMAGE",
                error="OpenCV could not decode the file.",
            )

        # ----------------------------------------------------------
        # 2. Determine dimensions/channels
        # ----------------------------------------------------------

        if image.ndim == 2:

            height, width = image.shape
            channels = 1

            gray = image

        else:

            height, width = image.shape[:2]
            channels = image.shape[2]

            gray = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY,
            )

        # ----------------------------------------------------------
        # 3. Reduce resolution only for metric computation
        # ----------------------------------------------------------

        gray = _resize_for_metrics(
            gray,
            resize_max_side,
        )

        gray = gray.astype(
            np.uint8,
            copy=False,
        )

        # ----------------------------------------------------------
        # 4. Pixel statistics
        # ----------------------------------------------------------

        min_pixel = int(gray.min())
        max_pixel = int(gray.max())
        median_pixel = float(np.median(gray))
        p01_pixel = float(np.percentile(gray, 1))
        p99_pixel = float(np.percentile(gray, 99))

        mean_pixel = float(gray.mean())
        contrast = float(gray.std())

        aspect_ratio = float(width / height)

        histogram = np.bincount(
            gray.ravel(),
            minlength=256,
        ).astype(np.float64)

        probabilities = histogram[
            histogram > 0
        ] / gray.size

        pixel_entropy = float(
            -np.sum(
                probabilities
                * np.log2(probabilities)
            )
        )

        unique_pixel_ratio = float(
            np.count_nonzero(histogram)
            / 256.0
        )

        unique_pixel_count = int(
            np.count_nonzero(histogram)
        )

        dark_pixel_ratio = float(
            np.mean(gray <= 1)
        )

        bright_pixel_ratio = float(
            np.mean(gray >= 254)
        )

        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))

        noise_estimate = float(
            np.median(
                np.abs(
                    gray.astype(np.float32)
                    - cv2.GaussianBlur(gray, (3, 3), 0)
                )
            )
        )

        background_ratio = float(
            np.mean(gray <= 5)
        )

        border_width = max(
            1,
            min(gray.shape) // 20,
        )
        border = np.concatenate(
            [
                gray[:border_width, :].ravel(),
                gray[-border_width:, :].ravel(),
                gray[:, :border_width].ravel(),
                gray[:, -border_width:].ravel(),
            ]
        )
        border_dark_ratio = float(
            np.mean(border <= 5)
        )

        # ----------------------------------------------------------
        # 5. Blur metric
        #
        # Variance of Laplacian:
        # higher generally means more high-frequency detail.
        # ----------------------------------------------------------

        blur_score = float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F,
            ).var()
        )

        # ----------------------------------------------------------
        # 6. Pixel clipping
        # ----------------------------------------------------------

        clip_low = float(
            np.mean(gray <= 1) * 100.0
        )

        clip_high = float(
            np.mean(gray >= 254) * 100.0
        )

        # ----------------------------------------------------------
        # 7. Non-zero / non-background ratio
        # ----------------------------------------------------------

        nonzero_ratio = float(
            np.mean(gray > 5)
        )

        # ----------------------------------------------------------
        # 8. Blank-image heuristic
        # ----------------------------------------------------------

        blank = bool(
            contrast
            <= float(
                thresholds.get(
                    "blank_std_max",
                    2.0,
                )
            )
            or
            nonzero_ratio
            <= float(
                thresholds.get(
                    "blank_nonzero_ratio_min",
                    0.05,
                )
            )
        )

        # ----------------------------------------------------------
        # 9. Quality flags
        # ----------------------------------------------------------

        flags: list[str] = []

        if blur_score < float(
            thresholds.get(
                "blur_min",
                20.0,
            )
        ):
            flags.append("BLUR")

        if contrast < float(
            thresholds.get(
                "contrast_min",
                10.0,
            )
        ):
            flags.append("LOW_CONTRAST")

        if clip_low > float(
            thresholds.get(
                "clip_percent_max",
                5.0,
            )
        ):
            flags.append("CLIP_LOW")

        if clip_high > float(
            thresholds.get(
                "clip_percent_max",
                5.0,
            )
        ):
            flags.append("CLIP_HIGH")

        if blank:
            flags.append("BLANK")

        if unique_pixel_ratio < float(
            thresholds.get(
                "unique_pixel_ratio_min",
                0.01,
            )
        ):
            flags.append("LOW_PIXEL_VARIETY")

        if width < int(
            thresholds.get(
                "min_width",
                256,
            )
        ) or height < int(
            thresholds.get(
                "min_height",
                256,
            )
        ):
            flags.append("LOW_RESOLUTION")

        min_aspect_ratio = float(
            thresholds.get(
                "min_aspect_ratio",
                0.5,
            )
        )
        max_aspect_ratio = float(
            thresholds.get(
                "max_aspect_ratio",
                2.0,
            )
        )

        if not min_aspect_ratio <= aspect_ratio <= max_aspect_ratio:
            flags.append("EXTREME_ASPECT_RATIO")

        quality_status = (
            "VALID"
            if not flags
            else "REVIEW"
        )

        return ImageMetrics(
            image_path=image_path,
            readable=True,
            width=int(width),
            height=int(height),
            channels=int(channels),
            aspect_ratio=aspect_ratio,
            dtype=str(image.dtype),
            min_pixel=min_pixel,
            max_pixel=max_pixel,
            median_pixel=median_pixel,
            p01_pixel=p01_pixel,
            p99_pixel=p99_pixel,
            mean_pixel=mean_pixel,
            std_pixel=contrast,
            pixel_entropy=pixel_entropy,
            unique_pixel_ratio=unique_pixel_ratio,
            unique_pixel_count=unique_pixel_count,
            dark_pixel_ratio=dark_pixel_ratio,
            bright_pixel_ratio=bright_pixel_ratio,
            edge_density=edge_density,
            noise_estimate=noise_estimate,
            background_ratio=background_ratio,
            border_dark_ratio=border_dark_ratio,
            blur_score=blur_score,
            contrast=contrast,
            clip_low_percent=clip_low,
            clip_high_percent=clip_high,
            nonzero_ratio=nonzero_ratio,
            blank=blank,
            quality_status=quality_status,
            quality_flags="|".join(flags),
            error=None,
        )

    except Exception as exc:

        return ImageMetrics(
            image_path=image_path,
            readable=False,
            width=None,
            height=None,
            channels=None,
            aspect_ratio=None,
            dtype=None,
            min_pixel=None,
            max_pixel=None,
            median_pixel=None,
            p01_pixel=None,
            p99_pixel=None,
            mean_pixel=None,
            std_pixel=None,
            pixel_entropy=None,
            unique_pixel_ratio=None,
            unique_pixel_count=None,
            dark_pixel_ratio=None,
            bright_pixel_ratio=None,
            edge_density=None,
            noise_estimate=None,
            background_ratio=None,
            border_dark_ratio=None,
            blur_score=None,
            contrast=None,
            clip_low_percent=None,
            clip_high_percent=None,
            nonzero_ratio=None,
            blank=False,
            quality_status="INVALID",
            quality_flags="CORRUPT_IMAGE",
            error=str(exc),
        )