import base64
import io

import pytest
from PIL import Image, ImageDraw

from reference_bundle import BundleError, build_reference_bundle


def image_data_url():
    image = Image.new('RGB', (80, 40), 'white')
    ImageDraw.Draw(image).line((10, 10, 60, 30), fill='black', width=4)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')


def approved_record():
    return {
        'id': 'ref-ka', 'target': 'ka', 'status': 'approved', 'dataClass': 'reference',
        'review': {'specificationVersion': 'ka-1.0', 'reviewerCode': 'expert-01', 'decisionDate': '2026-10-22'},
        'sample': {
            'image': image_data_url(), 'canvas': {'width': 100, 'height': 50},
            'events': [
                {'type': 'down', 'x': 10, 'y': 10, 'timestamp': 0},
                {'type': 'up', 'x': 70, 'y': 20, 'timestamp': 10},
            ],
        },
    }


def approved_specification():
    return {'target': 'ka', 'version': 'ka-1.0', 'status': 'approved'}


def test_builds_a_reproducible_bundle_from_matching_approved_evidence():
    bundle = build_reference_bundle(approved_record(), approved_specification(), ['lopez-2025-pdf#pdf-page=56'])

    assert bundle['targetId'] == 'ka'
    assert bundle['referenceRecordId'] == 'ref-ka'
    assert bundle['stroke']['strokeCount'] == 1
    assert bundle['image']['normalized']['width'] == 256
    assert bundle['status'] == 'approved'


def test_rejects_unapproved_or_mismatched_evidence():
    record = approved_record()
    record['status'] = 'candidate'
    with pytest.raises(BundleError, match='approved'):
        build_reference_bundle(record, approved_specification(), [])
    with pytest.raises(BundleError, match='matching'):
        build_reference_bundle(approved_record(), {**approved_specification(), 'version': 'ka-2.0'}, [])