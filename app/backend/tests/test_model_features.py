import base64
import io
import json
import shutil
import tempfile
from pathlib import Path

import pytest
from openpyxl import Workbook
from PIL import Image, ImageDraw

from model_features import (
    FEATURE_SCHEMA_VERSION,
    TrainingDataError,
    build_feature_rows,
    load_cleaned_manifest,
    writer_disjoint_folds,
)


@pytest.fixture
def workspace():
    root = Path(tempfile.mkdtemp(dir='.tmp'))
    yield root
    shutil.rmtree(root)


def png_data_url(offset=0):
    image = Image.new('RGB', (80, 80), 'white')
    ImageDraw.Draw(image).line((10 + offset, 10, 60 + offset, 60), fill='black', width=5)
    output = io.BytesIO()
    image.save(output, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


def sample(target='a', offset=0):
    return {
        'version': 1,
        'createdAt': '2026-10-26T00:00:00.000Z',
        'target': target,
        'canvas': {'width': 80, 'height': 80},
        'image': png_data_url(offset),
        'events': [
            {'type': 'down', 'x': 10 + offset, 'y': 10, 'timestamp': 0, 'pointerType': 'pen'},
            {'type': 'move', 'x': 35 + offset, 'y': 35, 'timestamp': 10, 'pointerType': 'pen'},
            {'type': 'up', 'x': 60 + offset, 'y': 60, 'timestamp': 20, 'pointerType': 'pen'},
        ],
    }


def write_manifest(path, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Sheet1'
    sheet.append(['sample_id', 'relative_path', 'writer_code', 'target', 'condition', 'binary_label', 'quality_status', 'schema_status', 'training_eligibility'])
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')


def test_loads_only_eligible_cleaned_manifest_rows(workspace):
    manifest = workspace / 'cleaned.xlsx'
    write_manifest(manifest, [
        ['W01_a_conformed', 'dataset/W01/A/conformed.json', 'W01', 'a', 'intended_conforming', 'conforming', 'accepted', 'valid', 'eligible'],
        ['W01_a_review', 'dataset/W01/A/review.json', 'W01', 'a', 'wrong_form', 'non_conforming', 'review_required', 'valid', 'hold_for_review'],
    ])

    rows = load_cleaned_manifest(manifest)

    assert rows == [{
        'sample_id': 'W01_a_conformed', 'relative_path': 'dataset/W01/A/conformed.json',
        'writer_code': 'W01', 'target': 'a', 'condition': 'intended_conforming',
        'binary_label': 'conforming', 'quality_status': 'accepted', 'schema_status': 'valid',
        'training_eligibility': 'eligible',
    }]


def test_builds_finite_feature_row_against_matching_expert_reference(workspace):
    project_root = workspace
    sample_path = project_root / 'dataset' / 'W01' / 'A' / 'conformed.json'
    reference_path = project_root / 'expert reference' / 'expert_.A.json'
    write_json(sample_path, sample())
    write_json(reference_path, sample())
    manifest_rows = [{
        'sample_id': 'W01_a_conformed', 'relative_path': 'dataset/W01/A/conformed.json',
        'writer_code': 'W01', 'target': 'a', 'condition': 'intended_conforming',
        'binary_label': 'conforming', 'quality_status': 'accepted', 'schema_status': 'valid',
        'training_eligibility': 'eligible',
    }]

    rows = build_feature_rows(manifest_rows, project_root, project_root / 'expert reference')

    assert len(rows) == 1
    assert rows[0]['feature_schema_version'] == FEATURE_SCHEMA_VERSION
    assert rows[0]['sample_id'] == 'W01_a_conformed'
    assert rows[0]['writer_code'] == 'W01'
    assert rows[0]['target'] == 'a'
    assert rows[0]['reference_checksum']
    assert rows[0]['mask_iou'] == pytest.approx(1.0)
    assert all(isinstance(rows[0][name], (int, float)) for name in rows[0]['feature_names'])


def test_missing_matching_expert_reference_fails_clearly(workspace):
    sample_path = workspace / 'dataset' / 'W01' / 'A' / 'conformed.json'
    write_json(sample_path, sample())
    manifest_rows = [{
        'sample_id': 'W01_a_conformed', 'relative_path': 'dataset/W01/A/conformed.json',
        'writer_code': 'W01', 'target': 'a', 'condition': 'intended_conforming',
        'binary_label': 'conforming', 'quality_status': 'accepted', 'schema_status': 'valid',
        'training_eligibility': 'eligible',
    }]

    with pytest.raises(TrainingDataError, match='Missing expert reference'):
        build_feature_rows(manifest_rows, workspace, workspace / 'expert reference')


def test_manifest_path_cannot_escape_project_root(workspace):
    manifest_rows = [{
        'sample_id': 'W01_a_conformed', 'relative_path': '../outside.json',
        'writer_code': 'W01', 'target': 'a', 'condition': 'intended_conforming',
        'binary_label': 'conforming', 'quality_status': 'accepted', 'schema_status': 'valid',
        'training_eligibility': 'eligible',
    }]

    with pytest.raises(TrainingDataError, match='escapes'):
        build_feature_rows(manifest_rows, workspace, workspace / 'expert reference')


def test_writer_disjoint_folds_never_train_on_held_out_writer():
    rows = [
        {'sample_id': f'{writer}_a', 'writer_code': writer, 'binary_label': 'conforming'}
        for writer in ('W01', 'W02', 'W03')
    ]

    folds = writer_disjoint_folds(rows)

    assert [fold['held_out_writer'] for fold in folds] == ['W01', 'W02', 'W03']
    for fold in folds:
        assert {row['writer_code'] for row in fold['test_rows']} == {fold['held_out_writer']}
        assert fold['held_out_writer'] not in {row['writer_code'] for row in fold['train_rows']}
