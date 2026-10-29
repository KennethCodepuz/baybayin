"""Offline pilot comparison; does not replace or write the deployed model."""

import argparse
import json
from pathlib import Path

from model_features import _load_reference_samples, load_cleaned_manifest
from model_multioutput import evaluate_multioutput_folds
from robust_features import robust_measurements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--baseline-features', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.baseline_features.read_text(encoding='utf-8').splitlines() if line.strip()]
    manifest = {row['sample_id']: row for row in load_cleaned_manifest(args.manifest)}
    references = _load_reference_samples(args.project_root / 'expert reference')
    candidate_rows = []
    for row in rows:
        sample_path = (args.project_root / manifest[row['sample_id']]['relative_path']).resolve()
        if args.project_root.resolve() not in sample_path.parents:
            raise ValueError('Sample path escapes project root')
        sample = json.loads(sample_path.read_text(encoding='utf-8'))
        measurements = robust_measurements(references[row['target']][0], sample)
        # Research-only substitution reuses the pilot trainer's fixed nine-column interface.
        candidate_rows.append({**row, 'mask_iou': 1 - measurements['centerline_distance'],
                               'start_end_displacement': measurements['normalized_endpoint_displacement']})
    baseline = evaluate_multioutput_folds(rows, random_seed=20261028)
    candidate = evaluate_multioutput_folds(candidate_rows, random_seed=20261028)
    result = {
        'status': 'research_only', 'sample_count': len(rows), 'seed': 20261028,
        'candidate_slots': {'mask_iou': 'one minus symmetric centerline distance',
                            'start_end_displacement': 'glyph-normalized endpoint displacement'},
        'baseline': baseline['report'], 'candidate': candidate['report'],
        'limitations': 'Writer-disjoint pilot using group-protocol labels; this candidate has not been deployed.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    (args.output.parent / 'candidate-features.jsonl').write_text(
        '\n'.join(json.dumps(row, sort_keys=True) for row in candidate_rows) + '\n', encoding='utf-8')
    (args.output.parent / 'predictions.json').write_text(json.dumps({
        'baseline': baseline['predictions'], 'candidate': candidate['predictions'],
    }, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
