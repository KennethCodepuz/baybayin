"""Promote the verified local expert batch to active provisional reference bundles."""

from datetime import date

from reference_bundle import build_reference_bundle


SPECIFICATION_VERSION = 'expert-reference-v1'


def promote_verified_expert_references(repository, graph, *, decision_date: str | None = None) -> list[str]:
    """Approve, bundle, and activate only checksum-verified imported expert records.

    This deliberately does not create stroke annotations or calibration thresholds.
    """
    decision_date = decision_date or date.today().isoformat()
    activated = []
    for record in repository.list_records():
        if record.get('provenance', {}).get('expertBatchId') != 'expert-reference-2026-10-24':
            continue
        target = graph.find_target(record['target'])
        if not target:
            continue
        reviewer_code = record['provenance'].get('expertCode', 'expert-reference')
        specification = repository.get_specification(record['target'], SPECIFICATION_VERSION)
        if not specification:
            specification = repository.create_specification({
                'target': record['target'], 'version': SPECIFICATION_VERSION, 'status': 'approved',
                'source': record['source'], 'reviewerCode': reviewer_code, 'decisionDate': decision_date,
            })
        if record['status'] == 'candidate':
            record['status'] = 'approved'
            record['review'] = {
                'reviewerCode': reviewer_code, 'decisionDate': decision_date,
                'notes': 'Designated as the project’s verified expert reference recording.',
                'specificationVersion': specification['version'],
            }
            record = repository.update_record(record)
        bundle_id = f"bundle-{record['id']}-{specification['version']}"
        bundle = repository.get_bundle(bundle_id)
        if not bundle:
            bundle = repository.create_bundle(build_reference_bundle(record, specification, target['sourceRefs']))
        repository.activate_bundle(record['target'], bundle['id'], reviewer_code, decision_date, 'Selected as the verified expert reference for provisional learner comparison.')
        activated.append(record['target'])
    return activated
