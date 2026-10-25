from kudlit_rules import evaluate_kudlit


def annotation():
    return {'schemaVersion': 1, 'id': 'be-v1', 'targetId': 'be', 'referenceBundleId': 'bundle-be', 'status': 'approved', 'reviewerCode': 'expert-01', 'decisionDate': '2026-10-25', 'expectedStrokeCount': 2, 'mark': {'strokeIndices': [1], 'kind': 'horizontal_line', 'position': 'above', 'regions': [{'left': .4, 'top': 0, 'right': .6, 'bottom': .16}]}}


def stroke(left, top, right, bottom):
    return {'boundingBox': {'left': left, 'top': top, 'right': right, 'bottom': bottom}}


def test_kudlit_mark_is_checked_in_the_full_canvas_region():
    result = evaluate_kudlit([stroke(.2, .3, .8, .8), stroke(.45, .05, .55, .08)], annotation(), target_id='be', reference_bundle_id='bundle-be')
    assert result['errors'] == []
    below = evaluate_kudlit([stroke(.2, .3, .8, .8), stroke(.45, .9, .55, .93)], annotation(), target_id='be', reference_bundle_id='bundle-be')
    assert below['errors'] == ['misplaced_kudlit']
