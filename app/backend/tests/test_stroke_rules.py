import pytest

from stroke_rules import StructuralRuleError, evaluate_structural_strokes


def strokes():
    return [
        [{'x': 0.0, 'y': 0.0}, {'x': 1.0, 'y': 0.0}],
        [{'x': 1.0, 'y': 0.0}, {'x': 1.0, 'y': 1.0}],
    ]


def approved_rules():
    return {
        'schemaVersion': 1, 'id': 'annotation-ka-1', 'targetId': 'ka', 'referenceBundleId': 'bundle-ka',
        'status': 'approved', 'reviewerCode': 'expert-01', 'decisionDate': '2026-10-23',
        'expectedStrokeCount': 2,
        'expectedDirections': ['right', 'down'],
        'startRegions': [
            {'left': 0, 'top': 0, 'right': 0.1, 'bottom': 0.1},
            {'left': 0.9, 'top': 0, 'right': 1, 'bottom': 0.1},
        ],
        'endRegions': [
            {'left': 0.9, 'top': 0, 'right': 1, 'bottom': 0.1},
            {'left': 0.9, 'top': 0.9, 'right': 1, 'bottom': 1},
        ],
    }


def test_structural_rules_report_only_approved_rule_violations():
    result = evaluate_structural_strokes(strokes(), approved_rules(), target_id='ka', reference_bundle_id='bundle-ka')

    assert result['available'] is True
    assert result['scored'] is False
    assert result['errors'] == []
    assert result['evidence']['ruleSource'] == 'approved_annotation'


def test_reports_count_direction_and_start_end_mismatches_separately():
    one_reversed_stroke = [[{'x': 1.0, 'y': 1.0}, {'x': 0.0, 'y': 1.0}]]

    result = evaluate_structural_strokes(one_reversed_stroke, approved_rules(), target_id='ka', reference_bundle_id='bundle-ka')

    assert result['errors'] == ['wrong_stroke_count']
    assert result['evidence']['checks']['direction'] == 'not_run_due_to_stroke_count'

    wrong_direction = [
        [{'x': 1.0, 'y': 0.0}, {'x': 0.0, 'y': 0.0}],
        strokes()[1],
    ]
    result = evaluate_structural_strokes(wrong_direction, approved_rules(), target_id='ka', reference_bundle_id='bundle-ka')
    assert 'wrong_stroke_direction' in result['errors']
    assert 'wrong_start_region' in result['errors']
    assert 'wrong_end_region' in result['errors']


def test_rejects_unapproved_or_invalid_normalized_region_rules():
    with pytest.raises(StructuralRuleError, match='approval provenance'):
        evaluate_structural_strokes(strokes(), {'status': 'draft'}, target_id='ka', reference_bundle_id='bundle-ka')
    rules = approved_rules()
    rules['startRegions'][0]['right'] = 1.1
    with pytest.raises(StructuralRuleError, match='between 0 and 1'):
        evaluate_structural_strokes(strokes(), rules, target_id='ka', reference_bundle_id='bundle-ka')


def test_rejects_unapproved_or_mismatched_annotation_even_when_rules_are_complete():
    rules = approved_rules()
    rules['status'] = 'draft'
    with pytest.raises(StructuralRuleError, match='approved'):
        evaluate_structural_strokes(strokes(), rules, target_id='ka', reference_bundle_id='bundle-ka')
    with pytest.raises(StructuralRuleError, match='match'):
        evaluate_structural_strokes(strokes(), approved_rules(), target_id='ba', reference_bundle_id='bundle-ka')
