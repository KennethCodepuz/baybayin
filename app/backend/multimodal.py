"""Deterministic image and stroke infrastructure for the future hybrid validator."""

from __future__ import annotations

import base64
import hashlib
import io
import math
from typing import Literal

from PIL import Image, ImageChops, ImageOps


class FeatureError(ValueError):
    pass


def _decode_png_data_url(data_url: str) -> Image.Image:
    prefix = 'data:image/png;base64,'
    if not isinstance(data_url, str) or not data_url.startswith(prefix):
        raise FeatureError('Image must be a PNG data URL')
    try:
        binary = base64.b64decode(data_url.removeprefix(prefix), validate=True)
        image = Image.open(io.BytesIO(binary))
        image.load()
    except Exception as error:
        raise FeatureError('Image must contain valid PNG data') from error
    if image.format != 'PNG':
        raise FeatureError('Image must contain valid PNG data')
    return image


def normalize_png_data_url(data_url: str, size: int = 256) -> dict:
    """Crop visible ink, preserve its aspect ratio, and place it on a white square."""
    if not isinstance(size, int) or size < 32 or size > 2048:
        raise FeatureError('Normalized image size must be between 32 and 2048 pixels')
    image = _decode_png_data_url(data_url).convert('RGBA')
    background = Image.new('RGBA', image.size, 'white')
    background.alpha_composite(image)
    rgb = background.convert('RGB')
    difference = ImageChops.difference(rgb, Image.new('RGB', rgb.size, 'white'))
    bounds = difference.getbbox()
    if not bounds:
        raise FeatureError('Image contains no ink to normalize')
    left, top, right, bottom = bounds
    padding = max(2, round(max(right - left, bottom - top) * 0.08))
    crop = rgb.crop((max(0, left - padding), max(0, top - padding), min(rgb.width, right + padding), min(rgb.height, bottom + padding)))
    crop.thumbnail((size, size), Image.Resampling.LANCZOS)
    normalized = Image.new('L', (size, size), color=255)
    x = (size - crop.width) // 2
    y = (size - crop.height) // 2
    normalized.paste(ImageOps.grayscale(crop), (x, y))
    output = io.BytesIO()
    normalized.save(output, format='PNG', optimize=False)
    binary = output.getvalue()
    return {
        'schemaVersion': 1,
        'width': size,
        'height': size,
        'inkBounds': {'left': left, 'top': top, 'right': right, 'bottom': bottom},
        'pngDataUrl': 'data:image/png;base64,' + base64.b64encode(binary).decode('ascii'),
        'sha256': hashlib.sha256(binary).hexdigest(),
    }


def _normalized_point(event: dict, width: float, height: float) -> dict:
    return {'x': round(event['x'] / width, 6), 'y': round(event['y'] / height, 6)}


def _direction(start: dict, end: dict) -> Literal['right', 'left', 'down', 'up', 'stationary']:
    dx = end['x'] - start['x']
    dy = end['y'] - start['y']
    if abs(dx) < 0.02 and abs(dy) < 0.02:
        return 'stationary'
    if abs(dx) >= abs(dy):
        return 'right' if dx > 0 else 'left'
    return 'down' if dy > 0 else 'up'


def extract_stroke_features(sample: dict) -> dict:
    """Return reproducible, non-scoring features from structurally checked events."""
    canvas = sample.get('canvas', {})
    width, height = canvas.get('width'), canvas.get('height')
    events = sample.get('events')
    if not isinstance(width, (int, float)) or width <= 0 or not isinstance(height, (int, float)) or height <= 0:
        raise FeatureError('Sample has invalid canvas dimensions')
    if not isinstance(events, list) or not events:
        raise FeatureError('Sample has no events')

    raw_strokes: list[list[dict]] = []
    active: list[dict] | None = None
    for event in events:
        event_type = event.get('type')
        if event_type == 'down':
            if active is not None:
                raise FeatureError('Stroke starts before the previous stroke ends')
            active = [event]
        elif event_type in {'move', 'up'}:
            if active is None:
                raise FeatureError('Stroke event appears before a down event')
            active.append(event)
            if event_type == 'up':
                raw_strokes.append(active)
                active = None
        else:
            raise FeatureError('Sample has an unsupported event type')
    if active is not None:
        raise FeatureError('Sample ends with an incomplete stroke')

    strokes = []
    for index, events_in_stroke in enumerate(raw_strokes):
        points = [_normalized_point(event, width, height) for event in events_in_stroke]
        start, end = points[0], points[-1]
        length = sum(math.dist((previous['x'], previous['y']), (point['x'], point['y'])) for previous, point in zip(points, points[1:]))
        xs, ys = [point['x'] for point in points], [point['y'] for point in points]
        strokes.append({
            'index': index,
            'points': points,
            'start': start,
            'end': end,
            'direction': _direction(start, end),
            'pathLength': round(length, 6),
            'boundingBox': {'left': min(xs), 'top': min(ys), 'right': max(xs), 'bottom': max(ys)},
        })
    return {'schemaVersion': 1, 'strokeCount': len(strokes), 'strokes': strokes}


def unavailable_branch_result(branch: Literal['form', 'stroke'], reason: str, source_refs: list[str] | None = None) -> dict:
    return {
        'available': False,
        'passed': None,
        'errors': [],
        'evidence': [{'code': reason}],
        'sourceRefs': source_refs or [],
        'branch': branch,
    }


def combine_validation(target_id: str, form: dict, stroke: dict, reference_bundle_id: str | None = None) -> dict:
    """Preserve branch outcomes; do not score until both approved branches are available."""
    available = bool(form.get('available')) and bool(stroke.get('available'))
    passed = form.get('passed') is True and stroke.get('passed') is True if available else None
    source_refs = list(dict.fromkeys([*form.get('sourceRefs', []), *stroke.get('sourceRefs', [])]))
    return {
        'schemaVersion': 1,
        'targetId': target_id,
        'referenceBundleId': reference_bundle_id,
        'form': form,
        'stroke': stroke,
        'overall': {
            'available': available,
            'passed': passed,
            'policyVersion': 'pending-expert-thresholds' if not available else 'expert-approved-policy-required',
        },
        'sourceRefs': source_refs,
    }