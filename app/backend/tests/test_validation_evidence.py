import base64
import io

from PIL import Image, ImageDraw

from reference_bundle import build_reference_bundle
from validation_evidence import provisional_bundle_evidence


def png_data_url():
    image = Image.new('RGB', (80, 40), 'white')
    ImageDraw.Draw(image).line((10, 10, 60, 30), fill='black', width=4)
    output = io.BytesIO()
    image.save(output, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


def sample():
    return {
        'image': png_data_url(), 'canvas': {'width': 100, 'height': 50},
        'events': [
            {'type': 'down', 'x': 10, 'y': 10},
            {'type': 'move', 'x': 40, 'y': 15},
            {'type': 'up', 'x': 70, 'y': 20},
        ],
    }


def bundle():
    record = {
        'id': 'ref-ka', 'target': 'ka', 'status': 'approved', 'dataClass': 'reference',
        'review': {'specificationVersion': 'ka-1.0', 'reviewerCode': 'expert-01', 'decisionDate': '2026-10-23'},
        'sample': sample(),
    }
    return build_reference_bundle(record, {'target': 'ka', 'version': 'ka-1.0', 'status': 'approved'}, ['lopez-2025-pdf#pdf-page=56'])


def test_bundle_produces_form_and_stroke_measurements_but_no_score_before_calibration():
    result = provisional_bundle_evidence(sample(), bundle(), ['lopez-2025-pdf#pdf-page=56'])

    assert result['form']['available'] is False
    assert result['form']['passed'] is None
    assert result['form']['evidence'][0]['code'] == 'expert_thresholds_pending'
    assert result['form']['evidence'][1]['code'] == 'provisional_measurements'
    assert result['form']['evidence'][1]['measurements']['maskIou'] == 1.0
    assert result['stroke']['evidence'][1]['measurements']['comparisons'][0]['normalizedDistance'] == 0.0
