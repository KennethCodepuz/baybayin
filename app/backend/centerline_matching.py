"""Experimental symmetric centerline comparison for normalized handwriting images."""

from __future__ import annotations

import base64
import io
import math

from PIL import Image

from multimodal import normalize_png_data_url


def _skeleton(data_url: str, size: int) -> set[tuple[int, int]]:
    normalized = normalize_png_data_url(data_url, size)['pngDataUrl']
    image = Image.open(io.BytesIO(base64.b64decode(normalized.split(',', 1)[1]))).convert('L')
    points = {(x, y) for y in range(size) for x in range(size) if image.getpixel((x, y)) < 240}
    offsets = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))
    changed = True
    while changed:
        changed = False
        for phase in (0, 1):
            remove = set()
            for x, y in points:
                neighbors = [int((x + dx, y + dy) in points) for dx, dy in offsets]
                count = sum(neighbors)
                transitions = sum(neighbors[i] == 0 and neighbors[(i + 1) % 8] == 1 for i in range(8))
                if not (2 <= count <= 6 and transitions == 1):
                    continue
                n, e, s, w = neighbors[0], neighbors[2], neighbors[4], neighbors[6]
                if phase == 0 and n * e * s == 0 and e * s * w == 0:
                    remove.add((x, y))
                elif phase == 1 and n * e * w == 0 and n * s * w == 0:
                    remove.add((x, y))
            if remove:
                points.difference_update(remove)
                changed = True
    if not points:
        raise ValueError('Image contains no centerline ink')
    return points


def compare_centerlines(reference: str, learner: str, *, size: int = 128) -> dict:
    """Return both directed nearest-centerline distances and their mean, scaled by image size."""
    left, right = _skeleton(reference, size), _skeleton(learner, size)

    def directed(source: set[tuple[int, int]], target: set[tuple[int, int]]) -> float:
        return sum(min(math.dist(point, other) for other in target) for point in source) / len(source) / size

    reference_to_learner = directed(left, right)
    learner_to_reference = directed(right, left)
    return {
        'reference_to_learner': reference_to_learner,
        'learner_to_reference': learner_to_reference,
        'symmetric_distance': (reference_to_learner + learner_to_reference) / 2,
    }
