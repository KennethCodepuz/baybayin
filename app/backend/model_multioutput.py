"""Preliminary error-specific model validation using expert-reference-relative features."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation_metrics import binary_metrics
from model_features import extract_features_for_sample, writer_disjoint_folds
from model_training import FEATURE_NAMES, MODEL_VERSION, ModelTrainingError, WeightedRandomForest, _matrix, _validate_rows
from robust_features import robust_measurements


OUTPUT_ERROR_CLASSES = {
    'form': 'wrong_form', 'count': 'wrong_count', 'process': 'wrong_process', 'kudlit': 'wrong_kudlit',
}
MULTIOUTPUT_MODEL_VERSION = 'pilot-multioutput-v1'
MODIFIED_TARGETS = {'be', 'bi', 'bo', 'bu', 'b', 'b_'}


def _applicable(output: str, target: str) -> bool:
    return output != 'kudlit' or target in MODIFIED_TARGETS


def _fit_models(rows: list[dict], random_seed: int) -> dict[str, WeightedRandomForest]:
    _validate_rows([{**row, 'binary_label': 'conforming'} for row in rows])
    models = {}
    for index, (output, error_class) in enumerate(OUTPUT_ERROR_CLASSES.items()):
        training_rows = [row for row in rows if _applicable(output, row['target'])]
        labels = [row['condition'] == error_class for row in training_rows]
        model = WeightedRandomForest(random_seed=random_seed + index)
        model.fit(_matrix(training_rows), labels)
        models[output] = model
    return models


def build_deployment_model(rows: list[dict], *, random_seed: int) -> dict:
    """Fit one all-current-data model after cross-validation is complete."""
    models = _fit_models(rows, random_seed)
    return {
        'model_version': MULTIOUTPUT_MODEL_VERSION, 'feature_schema_version': 'pilot-v1',
        'random_seed': random_seed, 'feature_names': FEATURE_NAMES,
        'outputs': {name: {'error_class': error_class, 'artifact': models[name].artifact()} for name, error_class in OUTPUT_ERROR_CLASSES.items()},
        'training_count': len(rows),
        'limitation': 'Trained on group-protocol attempts and compared against expert reference recordings. Preliminary model validation only.',
    }


def validate_multioutput_features(model: dict, features: dict) -> dict:
    """Turn fixed feature-schema measurements into separate learner-safe model outputs."""
    if model.get('model_version') != MULTIOUTPUT_MODEL_VERSION or model.get('feature_names') != FEATURE_NAMES:
        raise ModelTrainingError('Multi-output model does not match the current feature schema')
    if model.get('feature_schema_version') == 'pilot-centerline-v2':
        if features.get('feature_schema_version') != 'pilot-centerline-v2':
            raise ModelTrainingError('Candidate feature schema mismatch')
        if model.get('reference_checksums', {}).get(features.get('target')) != features.get('reference_checksum'):
            raise ModelTrainingError('Candidate expert reference checksum mismatch')
    _validate_rows([{**features, 'sample_id': 'live', 'writer_code': 'live', 'binary_label': 'conforming'}])
    matrix = _matrix([features])
    validation, detected = {}, []
    for output, descriptor in model['outputs'].items():
        if not _applicable(output, features['target']):
            validation[output] = {'state': 'not_applicable', 'confidence': None}
            continue
        forest = WeightedRandomForest.from_artifact(descriptor['artifact'])
        confidence = forest.predict_scores(matrix)[0]
        state = 'needs_practice' if confidence >= 0.5 else 'pass'
        validation[output] = {'state': state, 'confidence': round(confidence, 4)}
        if state == 'needs_practice':
            detected.append(output)
    evidence = {name: features[name] for name in FEATURE_NAMES}
    if model.get('feature_schema_version') == 'pilot-centerline-v2':
        evidence['centerline_similarity'] = evidence.pop('mask_iou')
        evidence['normalized_endpoint_displacement'] = evidence.pop('start_end_displacement')
    return {
        'schemaVersion': 1, 'state': 'preliminary_model_validation', 'target': features['target'],
        'message': 'Preliminary model validation complete.' if not detected else 'Preliminary model validation found areas to practise.',
        'validation': validation,
        'overall': {'state': 'needs_practice' if detected else 'pass', 'detected': detected},
        'evidence': evidence,
        'limitation': model['limitation'],
    }


def _metrics(predictions: list[dict]) -> dict:
    expected = [prediction['expected_error'] for prediction in predictions]
    predicted = [prediction['predicted_error'] for prediction in predictions]
    return {**binary_metrics(expected, predicted), 'count': len(predictions)}


def evaluate_multioutput_folds(rows: list[dict], *, random_seed: int) -> dict:
    """Evaluate every output with writer-disjoint folds before fitting deployment data."""
    predictions, folds = [], []
    for index, fold in enumerate(writer_disjoint_folds(rows), start=1):
        models = _fit_models(fold['train_rows'], random_seed)
        held_out_writer = fold['held_out_writer']
        folds.append({'fold': index, 'held_out_writer': held_out_writer, 'training_writers': sorted({row['writer_code'] for row in fold['train_rows']}), 'training_count': len(fold['train_rows']), 'test_count': len(fold['test_rows'])})
        for row in fold['test_rows']:
            for output, error_class in OUTPUT_ERROR_CLASSES.items():
                if not _applicable(output, row['target']):
                    continue
                confidence = models[output].predict_scores(_matrix([row]))[0]
                predictions.append({
                    'sample_id': row['sample_id'], 'writer_code': row['writer_code'], 'target': row['target'],
                    'held_out_writer': held_out_writer, 'output': output,
                    'expected_error': row['condition'] == error_class, 'predicted_error': confidence >= 0.5,
                    'confidence': round(confidence, 4),
                })
    return {
        'model_version': MULTIOUTPUT_MODEL_VERSION, 'random_seed': random_seed, 'feature_names': FEATURE_NAMES,
        'folds': folds, 'predictions': predictions,
        'report': {'outputs': {output: _metrics([item for item in predictions if item['output'] == output]) for output in OUTPUT_ERROR_CLASSES}, 'limitation': 'Generic wrong_process records are not direction/order labels.'},
    }


def validate_sample_with_model(sample: dict, model_path: Path, expert_reference_root: Path) -> dict:
    if not model_path.is_file():
        raise ModelTrainingError('Preliminary multi-output model is unavailable')
    model = json.loads(model_path.read_text(encoding='utf-8'))
    features = extract_features_for_sample(sample, expert_reference_root)
    if model.get('feature_schema_version') == 'pilot-centerline-v2':
        from model_features import _load_reference_samples
        references = _load_reference_samples(expert_reference_root)
        reference = references[sample['target']][0]
        robust = robust_measurements(reference, sample)
        features.update({
            'feature_schema_version': 'pilot-centerline-v2',
            'mask_iou': 1 - robust['centerline_distance'],
            'start_end_displacement': robust['normalized_endpoint_displacement'],
        })
    return validate_multioutput_features(model, features)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description='Train the preliminary multi-output Baybayin validation model.')
    parser.add_argument('--features-input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--random-seed', type=int, default=20261028)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.features_input.read_text(encoding='utf-8').splitlines() if line.strip()]
    evaluation = evaluate_multioutput_folds(rows, random_seed=args.random_seed)
    deployment = build_deployment_model(rows, random_seed=args.random_seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'multioutput-predictions.json').write_text(json.dumps(evaluation['predictions'], indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'multioutput-evaluation.json').write_text(json.dumps({key: value for key, value in evaluation.items() if key != 'predictions'}, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'multioutput-deployment-model.json').write_text(json.dumps(deployment) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
