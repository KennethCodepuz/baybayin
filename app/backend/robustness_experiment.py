"""Compare held-out writer predictions under controlled image and position changes."""

import argparse
import base64
import io
import json
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageDraw

from model_features import _feature_measurements, _load_reference_samples, load_cleaned_manifest
from model_multioutput import _fit_models
from model_training import _matrix
from robust_features import robust_measurements


def render(sample, width, dx=0, dy=0):
    result = deepcopy(sample)
    image = Image.new('RGB', (result['canvas']['width'], result['canvas']['height']), 'white')
    draw = ImageDraw.Draw(image)
    previous = None
    for event in result['events']:
        event['x'] += dx
        event['y'] += dy
        if not (0 <= event['x'] <= image.width and 0 <= event['y'] <= image.height):
            raise ValueError('Translation leaves canvas')
        point = (event['x'], event['y'])
        if event['type'] == 'down':
            previous = point
        if previous is not None:
            draw.line((previous, point), fill='#1b2a20', width=width)
            x, y = point
            radius = width / 2
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill='#1b2a20')
        previous = None if event['type'] == 'up' else point
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    result['image'] = 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')
    return result


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--baseline-features', type=Path, required=True)
    parser.add_argument('--candidate-features', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    baseline_rows, candidate_rows = read_rows(args.baseline_features), read_rows(args.candidate_features)
    writers = sorted({row['writer_code'] for row in baseline_rows})
    baseline = {writer: _fit_models([row for row in baseline_rows if row['writer_code'] != writer], 20261028) for writer in writers}
    candidate = {writer: _fit_models([row for row in candidate_rows if row['writer_code'] != writer], 20261028) for writer in writers}
    references = _load_reference_samples(args.project_root / 'expert reference')
    manifest = [row for row in load_cleaned_manifest(args.manifest) if row['condition'] in {'intended_conforming', 'wrong_kudlit'}]
    results = []
    for row in manifest:
        source = (args.project_root / row['relative_path']).resolve()
        if args.project_root.resolve() not in source.parents:
            raise ValueError('Sample path escapes project root')
        sample = json.loads(source.read_text(encoding='utf-8'))
        reference = references[row['target']][0]
        baseline_models, candidate_models = baseline[row['writer_code']], candidate[row['writer_code']]
        observations = []
        for width, dx, dy in [(2, 0, 0), (6, 0, 0), (12, 0, 0), (6, 20, 15)]:
            try:
                modified = render(sample, width, dx, dy)
            except ValueError:
                continue
            features = _feature_measurements(reference, modified)
            robust = robust_measurements(reference, modified)
            experimental = {**features, 'mask_iou': 1 - robust['centerline_distance'],
                            'start_end_displacement': robust['normalized_endpoint_displacement']}
            observations.append({'width': width, 'translation': [dx, dy],
                'baseline_form': baseline_models['form'].predict(_matrix([features]))[0],
                'candidate_form': candidate_models['form'].predict(_matrix([experimental]))[0],
                'baseline_kudlit': baseline_models['kudlit'].predict(_matrix([features]))[0],
                'candidate_kudlit': candidate_models['kudlit'].predict(_matrix([experimental]))[0]})
        results.append({'sample_id': row['sample_id'], 'target': row['target'], 'condition': row['condition'], 'observations': observations})
    args.output.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote controlled variations for {len(results)} writer-disjoint samples')


if __name__ == '__main__':
    main()
