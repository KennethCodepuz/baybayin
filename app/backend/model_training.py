"""Train and evaluate preliminary Baybayin classifiers without writer leakage."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from statistics import median

from evaluation_metrics import binary_metrics
from model_features import writer_disjoint_folds


FEATURE_NAMES = [
    'mask_iou', 'centroid_distance', 'ink_width_difference', 'ink_height_difference',
    'stroke_count_difference', 'stroke_path_distance', 'path_length_ratio',
    'start_end_displacement', 'direction_match_ratio',
]
MODEL_VERSION = 'pilot-rf-v1'


class ModelTrainingError(ValueError):
    """Raised when provisional model training inputs are incomplete or unsafe."""


class WeightedRandomForest:
    """Small deterministic binary forest for the fixed pilot feature schema."""

    def __init__(self, *, random_seed: int, tree_count: int = 200, max_depth: int = 5, min_leaf_size: int = 2):
        self.random_seed = random_seed
        self.tree_count = tree_count
        self.max_depth = max_depth
        self.min_leaf_size = min_leaf_size
        self.trees: list[dict] = []

    @staticmethod
    def _gini(rows: list[tuple[list[float], bool]], weights: dict[bool, float]) -> float:
        total = sum(weights[label] for _, label in rows)
        if not total:
            return 0.0
        return 1 - sum((sum(weights[label] for _, actual in rows if actual == label) / total) ** 2 for label in (False, True))

    @staticmethod
    def _majority(rows: list[tuple[list[float], bool]], weights: dict[bool, float]) -> bool:
        return sum(weights[actual] for _, actual in rows if actual) >= sum(weights[actual] for _, actual in rows if not actual)

    def _build_tree(self, rows: list[tuple[list[float], bool]], weights: dict[bool, float], depth: int, generator: random.Random) -> dict:
        prediction = self._majority(rows, weights)
        if depth >= self.max_depth or len(rows) < self.min_leaf_size * 2 or len({label for _, label in rows}) == 1:
            return {'prediction': prediction}
        feature_indexes = generator.sample(range(len(FEATURE_NAMES)), k=max(1, int(math.sqrt(len(FEATURE_NAMES)))))
        best = None
        for feature_index in feature_indexes:
            values = sorted({features[feature_index] for features, _ in rows})
            for left_value, right_value in zip(values, values[1:]):
                threshold = (left_value + right_value) / 2
                left = [row for row in rows if row[0][feature_index] <= threshold]
                right = [row for row in rows if row[0][feature_index] > threshold]
                if len(left) < self.min_leaf_size or len(right) < self.min_leaf_size:
                    continue
                impurity = (len(left) * self._gini(left, weights) + len(right) * self._gini(right, weights)) / len(rows)
                candidate = (impurity, feature_index, threshold, left, right)
                if best is None or candidate[:3] < best[:3]:
                    best = candidate
        if best is None:
            return {'prediction': prediction}
        _, feature_index, threshold, left, right = best
        return {
            'prediction': prediction,
            'feature_index': feature_index,
            'threshold': threshold,
            'left': self._build_tree(left, weights, depth + 1, generator),
            'right': self._build_tree(right, weights, depth + 1, generator),
        }

    def fit(self, matrix: list[list[float]], labels: list[bool]) -> 'WeightedRandomForest':
        counts = {label: labels.count(label) for label in (False, True)}
        if not counts[False] or not counts[True]:
            raise ModelTrainingError('Random Forest training needs both binary classes')
        weights = {label: len(labels) / (2 * counts[label]) for label in (False, True)}
        source = list(zip(matrix, labels))
        generator = random.Random(self.random_seed)
        self.trees = [
            self._build_tree([generator.choice(source) for _ in source], weights, 0, random.Random(generator.randrange(2**32)))
            for _ in range(self.tree_count)
        ]
        return self

    @staticmethod
    def _predict_tree(tree: dict, features: list[float]) -> bool:
        while 'feature_index' in tree:
            tree = tree['left'] if features[tree['feature_index']] <= tree['threshold'] else tree['right']
        return bool(tree['prediction'])

    def predict(self, matrix: list[list[float]]) -> list[bool]:
        if not self.trees:
            raise ModelTrainingError('Random Forest has not been fitted')
        return [score >= 0.5 for score in self.predict_scores(matrix)]

    def predict_scores(self, matrix: list[list[float]]) -> list[float]:
        if not self.trees:
            raise ModelTrainingError('Random Forest has not been fitted')
        return [sum(self._predict_tree(tree, features) for tree in self.trees) / len(self.trees) for features in matrix]

    def artifact(self) -> dict:
        return {
            'model_version': MODEL_VERSION, 'algorithm': 'weighted_random_forest',
            'random_seed': self.random_seed, 'tree_count': self.tree_count,
            'max_depth': self.max_depth, 'min_leaf_size': self.min_leaf_size,
            'feature_names': FEATURE_NAMES, 'trees': self.trees,
        }

    @classmethod
    def from_artifact(cls, artifact: dict) -> 'WeightedRandomForest':
        if artifact.get('model_version') != MODEL_VERSION or artifact.get('feature_names') != FEATURE_NAMES:
            raise ModelTrainingError('Model artifact does not match the current feature schema')
        model = cls(
            random_seed=artifact['random_seed'], tree_count=artifact['tree_count'],
            max_depth=artifact['max_depth'], min_leaf_size=artifact['min_leaf_size'],
        )
        if not isinstance(artifact.get('trees'), list) or len(artifact['trees']) != model.tree_count:
            raise ModelTrainingError('Model artifact has invalid trees')
        model.trees = artifact['trees']
        return model


def _validate_rows(rows: list[dict]) -> None:
    if not rows:
        raise ModelTrainingError('At least one feature row is required')
    for row in rows:
        if row.get('binary_label') not in {'conforming', 'non_conforming'}:
            raise ModelTrainingError('Each feature row needs a binary label')
        if not row.get('writer_code') or not row.get('sample_id'):
            raise ModelTrainingError('Each feature row needs a writer code and sample ID')
        for name in FEATURE_NAMES:
            value = row.get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise ModelTrainingError(f'Feature {name} must be finite')


def _error_value(row: dict, name: str) -> float:
    value = float(row[name])
    if name == 'mask_iou':
        return 1 - value
    if name == 'path_length_ratio':
        if value <= 0:
            raise ModelTrainingError('path_length_ratio must be positive')
        return abs(math.log(value))
    if name == 'direction_match_ratio':
        return 1 - value
    return value


def fit_deterministic_baseline(rows: list[dict]) -> dict:
    """Fit transparent, conforming-reference thresholds from training rows only."""
    _validate_rows(rows)
    conforming = [row for row in rows if row['binary_label'] == 'conforming']
    non_conforming = [row for row in rows if row['binary_label'] == 'non_conforming']
    if not conforming or not non_conforming:
        raise ModelTrainingError('Baseline training needs both binary classes')
    centers, scales = {}, {}
    for name in FEATURE_NAMES:
        values = [_error_value(row, name) for row in conforming]
        center = median(values)
        centers[name] = center
        scales[name] = max(median([abs(value - center) for value in values]), 0.01)

    def score(row: dict) -> float:
        return sum(abs(_error_value(row, name) - centers[name]) / scales[name] for name in FEATURE_NAMES) / len(FEATURE_NAMES)

    conforming_scores = [score(row) for row in conforming]
    non_conforming_scores = [score(row) for row in non_conforming]
    threshold = (median(conforming_scores) + median(non_conforming_scores)) / 2
    return {'feature_names': FEATURE_NAMES, 'centers': centers, 'scales': scales, 'threshold': threshold}


def predict_deterministic_baseline(model: dict, row: dict) -> tuple[bool, float]:
    _validate_rows([row])
    score = sum(
        abs(_error_value(row, name) - model['centers'][name]) / model['scales'][name]
        for name in model['feature_names']
    ) / len(model['feature_names'])
    return score > model['threshold'], round(score, 12)


def _matrix(rows: list[dict]) -> list[list[float]]:
    return [[float(row[name]) for name in FEATURE_NAMES] for row in rows]


def _metrics(predictions: list[dict]) -> dict:
    expected = [prediction['expected_non_conforming'] for prediction in predictions]
    predicted = [prediction['predicted_non_conforming'] for prediction in predictions]
    metrics = binary_metrics(expected, predicted)
    specificity_denominator = metrics['trueNegative'] + metrics['falsePositive']
    specificity = metrics['trueNegative'] / specificity_denominator if specificity_denominator else 0.0
    return {**metrics, 'balancedAccuracy': (metrics['recall'] + specificity) / 2, 'count': len(predictions)}


def _group_metrics(predictions: list[dict], key: str) -> dict:
    return {
        group: _metrics([prediction for prediction in predictions if prediction[key] == group])
        for group in sorted({prediction[key] for prediction in predictions})
    }


def run_leave_one_writer_out(rows: list[dict], *, random_seed: int, model_output_dir: Path | None = None) -> dict:
    """Evaluate both methods with no held-out writer records used for fitting."""
    _validate_rows(rows)
    predictions, folds, saved_models = [], [], []
    for fold_index, fold in enumerate(writer_disjoint_folds(rows), start=1):
        training_rows, test_rows = fold['train_rows'], fold['test_rows']
        baseline = fit_deterministic_baseline(training_rows)
        classifier = WeightedRandomForest(random_seed=random_seed)
        classifier.fit(_matrix(training_rows), [row['binary_label'] == 'non_conforming' for row in training_rows])
        training_writers = sorted({row['writer_code'] for row in training_rows})
        held_out_writer = fold['held_out_writer']
        if held_out_writer in training_writers:
            raise ModelTrainingError('Held-out writer entered a training fold')
        folds.append({
            'fold': fold_index, 'held_out_writer': held_out_writer, 'training_writers': training_writers,
            'training_count': len(training_rows), 'test_count': len(test_rows),
        })
        if model_output_dir:
            model_output_dir.mkdir(parents=True, exist_ok=True)
            path = model_output_dir / f'fold-{fold_index}-{held_out_writer}.json'
            path.write_text(json.dumps({
                **classifier.artifact(), 'training_writers': training_writers, 'held_out_writer': held_out_writer,
            }) + '\n', encoding='utf-8')
            saved_models.append(str(path))
        for row, random_forest_prediction in zip(test_rows, classifier.predict(_matrix(test_rows))):
            expected = row['binary_label'] == 'non_conforming'
            baseline_prediction, baseline_score = predict_deterministic_baseline(baseline, row)
            base = {
                'sample_id': row['sample_id'], 'writer_code': row['writer_code'], 'target': row['target'],
                'held_out_writer': held_out_writer, 'expected_non_conforming': expected,
            }
            predictions.extend([
                {**base, 'method': 'deterministic_baseline', 'predicted_non_conforming': baseline_prediction, 'decision_score': baseline_score},
                {**base, 'method': 'random_forest', 'predicted_non_conforming': bool(random_forest_prediction)},
            ])

    methods = {}
    for method in ('deterministic_baseline', 'random_forest'):
        method_predictions = [prediction for prediction in predictions if prediction['method'] == method]
        if len({prediction['sample_id'] for prediction in method_predictions}) != len(rows):
            raise ModelTrainingError('Evaluation requires exactly one out-of-fold prediction per sample')
        methods[method] = {
            'overall': _metrics(method_predictions),
            'by_writer': _group_metrics(method_predictions, 'writer_code'),
            'by_target': _group_metrics(method_predictions, 'target'),
        }
    return {
        'model_version': MODEL_VERSION, 'random_seed': random_seed, 'feature_names': FEATURE_NAMES,
        'folds': folds, 'predictions': predictions, 'saved_models': saved_models,
        'report': {
            'methods': methods,
            'limitation': 'Preliminary group-protocol labels only. These results are not expert-reviewed final thesis performance.',
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Train writer-disjoint preliminary Baybayin classifiers.')
    parser.add_argument('--features-input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--random-seed', type=int, default=20261028)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.features_input.read_text(encoding='utf-8').splitlines() if line.strip()]
    result = run_leave_one_writer_out(rows, random_seed=args.random_seed, model_output_dir=args.output_dir / 'models')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'predictions.json').write_text(json.dumps(result['predictions'], indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'evaluation-report.json').write_text(json.dumps({key: value for key, value in result.items() if key != 'predictions'}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
