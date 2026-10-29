"""Fit the versioned experimental centerline model from evaluated feature rows."""

import argparse
import json
from pathlib import Path

from model_multioutput import build_deployment_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--features-input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.features_input.read_text(encoding='utf-8').splitlines() if line.strip()]
    checksums = {}
    for row in rows:
        checksum = row.get('reference_checksum')
        if not checksum or (row['target'] in checksums and checksums[row['target']] != checksum):
            raise ValueError(f"Missing or inconsistent reference checksum for {row['target']}")
        checksums[row['target']] = checksum
    model = build_deployment_model(rows, random_seed=20261028)
    model.update({
        'feature_schema_version': 'pilot-centerline-v2',
        'reference_checksums': checksums,
        'feature_slot_mapping': {'mask_iou': 'one minus symmetric centerline distance',
                                 'start_end_displacement': 'glyph-normalized endpoint displacement'},
        'limitation': 'Preliminary model trained on group-protocol attempts against expert references. Pen-width and position sensitivity are reduced but not eliminated.',
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f'Refusing to overwrite existing model artifact: {args.output}')
    args.output.write_text(json.dumps(model) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
