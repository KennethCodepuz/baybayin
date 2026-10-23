"""Deterministic, non-scoring image-form measurements for PNG handwriting samples."""

from __future__ import annotations

import base64
import io
import math

from PIL import Image

from multimodal import FeatureError, normalize_png_data_url


class FormMatchError(ValueError):
    pass


def _mask(normalized_data_url: str, threshold: int) -> list[list[bool]]:
    prefix = 'data:image/png;base64,'
    try:
        binary = base64.b64decode(normalized_data_url.removeprefix(prefix), validate=True)
        image = Image.open(io.BytesIO(binary)).convert('L')
    except Exception as error:
        raise FormMatchError('Normalized image could not be decoded') from error
    return [[image.getpixel((x, y)) < threshold for x in range(image.width)] for y in range(image.height)]


def _centroid(mask: list[list[bool]]) -> tuple[float, float]:
    coordinates = [(x, y) for y, row in enumerate(mask) for x, is_ink in enumerate(row) if is_ink]
    if not coordinates:
        raise FormMatchError('Normalized image contains no ink mask')
    return (sum(x for x, _ in coordinates) / len(coordinates), sum(y for _, y in coordinates) / len(coordinates))


def _bounding_box(mask: list[list[bool]]) -> dict[str, int]:
    coordinates = [(x, y) for y, row in enumerate(mask) for x, is_ink in enumerate(row) if is_ink]
    if not coordinates:
        raise FormMatchError('Normalized image contains no ink mask')
    return {
        'left': min(x for x, _ in coordinates), 'top': min(y for _, y in coordinates),
        'right': max(x for x, _ in coordinates), 'bottom': max(y for _, y in coordinates),
    }


def compare_form_images(reference_data_url: str, learner_data_url: str, *, size: int = 256, threshold: int = 240) -> dict:
    """Return reproducible visual measurements without assigning Baybayin errors."""
    if not isinstance(threshold, int) or isinstance(threshold, bool) or not 0 < threshold < 256:
        raise FormMatchError('Mask threshold must be an integer between 1 and 255')
    try:
        reference = normalize_png_data_url(reference_data_url, size)
        learner = normalize_png_data_url(learner_data_url, size)
    except FeatureError as error:
        raise FormMatchError(str(error)) from error
    reference_mask, learner_mask = _mask(reference['pngDataUrl'], threshold), _mask(learner['pngDataUrl'], threshold)
    intersection = sum(reference_pixel and learner_pixel for reference_row, learner_row in zip(reference_mask, learner_mask) for reference_pixel, learner_pixel in zip(reference_row, learner_row))
    union = sum(reference_pixel or learner_pixel for reference_row, learner_row in zip(reference_mask, learner_mask) for reference_pixel, learner_pixel in zip(reference_row, learner_row))
    reference_centroid, learner_centroid = _centroid(reference_mask), _centroid(learner_mask)
    return {
        'available': True,
        'scored': False,
        'algorithmVersion': 'mask-v1',
        'errors': [],
        'measurements': {
            'maskThreshold': threshold,
            'maskIou': round(intersection / union, 12),
            'centroidDistance': round(math.dist(reference_centroid, learner_centroid) / size, 12),
            'referenceInkBounds': _bounding_box(reference_mask),
            'learnerInkBounds': _bounding_box(learner_mask),
            'referenceImageSha256': reference['sha256'],
            'learnerImageSha256': learner['sha256'],
        },
    }
