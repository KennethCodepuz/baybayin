from feedback import deterministic_feedback, retrieve_feedback_context
from knowledge_graph import load_knowledge_graph


def graph():
    from pathlib import Path
    return load_knowledge_graph(Path(__file__).resolve().parents[3] / 'knowledge-graph')


def test_retrieves_target_sources_and_only_relevant_error_context():
    context = retrieve_feedback_context(graph(), 'ba', ['wrong_stroke_direction'])

    assert context['target']['targetId'] == 'ba'
    assert context['sourceRefs'] == ['lopez-2025-pdf#pdf-page=56']
    assert context['errors'] == ['wrong_stroke_direction']


def test_deterministic_feedback_only_explains_validator_supplied_errors():
    result = {
        'targetId': 'ba',
        'form': {'errors': ['wrong_form']},
        'stroke': {'errors': ['wrong_stroke_direction']},
    }
    feedback = deterministic_feedback(retrieve_feedback_context(graph(), 'ba', ['wrong_form', 'wrong_stroke_direction']), result)

    assert feedback['mode'] == 'deterministic_fallback'
    assert feedback['detectedErrors'] == ['wrong_form', 'wrong_stroke_direction']
    assert feedback['sourceRefs'] == ['lopez-2025-pdf#pdf-page=56']
    assert 'direction' in feedback['message'].lower()
