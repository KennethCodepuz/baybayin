import base64
import io

import pytest
from PIL import Image, ImageDraw

from multimodal import (
    FeatureError,
    combine_validation,
    extract_stroke_features,
    normalize_png_data_url,
    unavailable_branch_result,
)


def png_data_url(draw=False):
    image = Image.new('RGB', (80, 40), 'white')
    if draw:
        ImageDraw.Draw(image).line((10, 10, 60, 30), fill='black', width=4)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')


def sample():
    return {
        'canvas': {'width': 100, 'height': 50},
        'events': [
            {'type': 'down', 'x': 10, 'y': 10, 'timestamp': 0, 'pointerType': 'pen'},
            {'type': 'move', 'x': 40, 'y': 10, 'timestamp': 10, 'pointerType': 'pen'},
            {'type': 'up', 'x': 70, 'y': 20, 'timestamp': 20, 'pointerType': 'pen'},
            {'type': 'down', 'x': 80, 'y': 40, 'timestamp': 30, 'pointerType': 'pen'},
            {'type': 'up', 'x': 80, 'y': 40, 'timestamp': 40, 'pointerType': 'pen'},
        ],
    }


def test_normalizes_ink_to_a_deterministic_square_png():
    normalized = normalize_png_data_url(png_data_url(draw=True), size=64)

    assert normalized['width'] == 64
    assert normalized['height'] == 64
    assert normalized['inkBounds']['left'] < normalized['inkBounds']['right']
    assert normalized['pngDataUrl'].startswith('data:image/png;base64,')
    assert normalize_png_data_url(png_data_url(draw=True), size=64)['sha256'] == normalized['sha256']


def test_rejects_blank_or_non_png_image_data():
    with pytest.raises(FeatureError, match='no ink'):
        normalize_png_data_url(png_data_url())
    with pytest.raises(FeatureError, match='PNG'):
        normalize_png_data_url('data:image/jpeg;base64,aGVsbG8=')


def test_segments_strokes_without_mutating_recorded_events():
    recording = sample()
    original_events = [event.copy() for event in recording['events']]

    features = extract_stroke_features(recording)

    assert features['strokeCount'] == 2
    assert features['strokes'][0]['direction'] == 'right'
    assert features['strokes'][1]['direction'] == 'stationary'
    assert features['strokes'][0]['start'] == {'x': 0.1, 'y': 0.2}
    assert features['strokes'][0]['end'] == {'x': 0.7, 'y': 0.4}
    assert recording['events'] == original_events


def test_branch_and_hybrid_results_remain_unavailable_without_approved_thresholds():
    form = unavailable_branch_result('form', 'reference_bundle_missing')
    stroke = unavailable_branch_result('stroke', 'thresholds_pending')
    result = combine_validation('ka', form, stroke)

    assert result['form']['passed'] is None
    assert result['stroke']['passed'] is None
    assert result['overall']['available'] is False
    assert result['overall']['passed'] is None