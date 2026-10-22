"""Build immutable, multimodal reference bundles from approved expert evidence."""

from __future__ import annotations

from multimodal import extract_stroke_features, normalize_png_data_url


class BundleError(ValueError):
    pass


def build_reference_bundle(record: dict, specification: dict, source_refs: list[str]) -> dict:
    if record.get('status') != 'approved' or record.get('dataClass') != 'reference':
        raise BundleError('Reference bundle requires an approved reference record')
    if specification.get('status') != 'approved':
        raise BundleError('Reference bundle requires an approved specification')
    if record.get('target') != specification.get('target') or record.get('review', {}).get('specificationVersion') != specification.get('version'):
        raise BundleError('Reference bundle requires matching record and specification versions')
    sample = record.get('sample')
    if not isinstance(sample, dict):
        raise BundleError('Reference record has no sample')
    normalized = normalize_png_data_url(sample.get('image'))
    stroke_features = extract_stroke_features(sample)
    return {
        'schemaVersion': 1,
        'id': f"bundle-{record['id']}-{specification['version']}",
        'targetId': record['target'],
        'referenceRecordId': record['id'],
        'specificationVersion': specification['version'],
        'sourceRefs': list(source_refs),
        'image': {
            'sourceSampleImage': 'immutable_record_sample_image',
            'normalized': normalized,
            'annotation': None,
            'approvedBy': record['review'].get('reviewerCode'),
            'approvedAt': record['review'].get('decisionDate'),
        },
        'stroke': {
            'sourceSampleId': record['id'],
            **stroke_features,
        },
        'status': 'approved',
    }