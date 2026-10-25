from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from feedback import deterministic_feedback, retrieve_feedback_context
from form_matching import FormMatchError
from knowledge_graph import KnowledgeGraph, load_knowledge_graph
from kudlit_rules import KudlitRuleError, validate_kudlit_annotation
from learner_validation import learner_result
from multimodal import FeatureError, combine_validation, unavailable_branch_result, validate_png_data_url
from reference_bundle import BundleError, build_reference_bundle
from expert_reference_batch import import_batch, preflight_batch
from reference_library import DuplicateReferenceError, InvalidReferenceIdentifierError, ReferenceNotFoundError, ReferenceRepository
from security import require_reference_token
from stroke_matching import StrokeMatchError
from scoring import score_form_measurements, score_stroke_measurements
from validation_evidence import provisional_bundle_evidence


class Canvas(BaseModel):
    model_config = ConfigDict(extra='forbid')
    width: int = Field(gt=0, le=4096)
    height: int = Field(gt=0, le=4096)


class Event(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    type: Literal['down', 'move', 'up']
    x: float
    y: float
    timestamp: float = Field(ge=0)
    pointerType: str = Field(min_length=1, max_length=20)


class Sample(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal[1]
    createdAt: str = Field(min_length=1, max_length=40)
    target: str = Field(min_length=1, max_length=100)
    canvas: Canvas
    image: str = Field(pattern=r'^data:image/png;base64,[A-Za-z0-9+/]+={0,2}$', max_length=10_000_000)
    events: list[Event] = Field(min_length=2, max_length=10_000)

    @field_validator('target')
    @classmethod
    def target_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError('Target character must not be blank')
        return value

    @field_validator('image')
    @classmethod
    def image_must_be_a_safe_png(cls, value):
        try:
            validate_png_data_url(value)
        except FeatureError as error:
            raise ValueError(str(error)) from error
        return value

    @model_validator(mode='after')
    def complete_strokes(self):
        active = False
        last_timestamp = -1
        for event in self.events:
            if event.x < 0 or event.x > self.canvas.width or event.y < 0 or event.y > self.canvas.height:
                raise ValueError('Event coordinates must be inside the canvas')
            if event.timestamp < last_timestamp:
                raise ValueError('Event timestamps must be ordered')
            last_timestamp = event.timestamp
            if event.type == 'down':
                if active:
                    raise ValueError('A stroke cannot start before the previous stroke ends')
                active = True
            elif not active:
                raise ValueError('A stroke must start before move or up')
            elif event.type == 'up':
                active = False
        if active:
            raise ValueError('The last stroke is incomplete')
        return self


class SourceReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=200)
    pages: list[str] = Field(min_length=1, max_length=20)
    convention: str = Field(min_length=1, max_length=100)


class CaptureMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    inputMethod: str = Field(min_length=1, max_length=50)


class InitialReview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reviewerCode: str = Field(min_length=1, max_length=100)
    notes: str = Field(min_length=1, max_length=2_000)


class ReferenceCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sample: Sample
    dataClass: Literal['reference', 'test']
    source: SourceReference
    capture: CaptureMetadata
    review: InitialReview

class ReviewTransition(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['approved', 'rejected', 'superseded']
    reviewerCode: str = Field(min_length=1, max_length=100)
    decisionDate: date
    notes: str = Field(min_length=1, max_length=2_000)
    specificationVersion: str | None = Field(default=None, min_length=1, max_length=100)


class CharacterSpecification(BaseModel):
    model_config = ConfigDict(extra='forbid')
    target: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9._-]+$')
    status: Literal['draft', 'approved']
    source: SourceReference
    reviewerCode: str | None = Field(default=None, min_length=1, max_length=100)
    decisionDate: date | None = None

    @model_validator(mode='after')
    def approved_specification_needs_reviewer_decision(self):
        if self.status == 'approved' and (not self.reviewerCode or not self.decisionDate):
            raise ValueError('An approved specification needs a reviewer code and decision date')
        return self


class ReferenceBundleCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    referenceRecordId: str = Field(min_length=1, max_length=100)


class ReferenceBundleActivation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reviewerCode: str = Field(min_length=1, max_length=100)
    decisionDate: date
    reason: str = Field(min_length=1, max_length=2_000)


class ExpertBatchImport(BaseModel):
    model_config = ConfigDict(extra='forbid')
    importerCode: str = Field(min_length=1, max_length=100)


class StrokeAnnotationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    annotation: dict


class BranchFeedback(BaseModel):
    model_config = ConfigDict(extra='forbid')
    errors: list[str] = Field(default_factory=list, max_length=20)


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    targetId: str = Field(min_length=1, max_length=100)
    form: BranchFeedback
    stroke: BranchFeedback


app = FastAPI(title='Baybayin capture API')
app.state.reference_repository = ReferenceRepository(Path(__file__).resolve().parent.parent / 'data' / 'reference-library')
app.state.knowledge_graph = load_knowledge_graph(Path(__file__).resolve().parents[2] / 'knowledge-graph')
app.state.expert_reference_root = Path(__file__).resolve().parents[2] / 'expert reference'
app.state.expert_batch_manifest = Path(__file__).resolve().parent.parent / 'research' / 'expert-reference-batch-2026-10-24.json'
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_methods=['GET', 'POST', 'PATCH'],
    allow_headers=['Content-Type', 'Authorization'],
)


@app.post('/api/samples/check')
def check_sample(sample: Sample):
    # Checks capture structure and current target eligibility; this does not validate Baybayin writing.
    if not knowledge_graph().is_current_release_target(sample.target):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Sample target is not in the current release',
        )
    return {'sample': sample}


@app.get('/api/knowledge-graph/catalog')
def knowledge_graph_catalog():
    graph = knowledge_graph()
    return {
        'sourceId': graph.source_id,
        'version': 1,
        'targets': [public_target(target) for target in graph.current_release_targets()],
    }


@app.get('/api/knowledge-graph/readiness')
def knowledge_graph_readiness():
    return {'targets': [public_target(target) for target in knowledge_graph().current_release_targets()]}


@app.get('/api/knowledge-graph/targets/{target_id}')
def knowledge_graph_target(target_id: str):
    target = knowledge_graph().find_target(target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Knowledge-graph target not found')
    return {'target': public_target(target)}


@app.post('/api/reference-bundles', status_code=status.HTTP_201_CREATED)
def create_reference_bundle(request: ReferenceBundleCreate, _: None = Depends(require_reference_token)):
    repository = reference_repository()
    try:
        record = repository.get_record(request.referenceRecordId)
    except (ReferenceNotFoundError, InvalidReferenceIdentifierError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reference record not found')
    version = record.get('review', {}).get('specificationVersion')
    specification = repository.get_specification(record['target'], version) if version else None
    target = knowledge_graph().find_target(record['target'])
    if not target:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Reference target is not in the current core release')
    try:
        bundle = build_reference_bundle(record, specification or {}, target['sourceRefs'])
        return {'bundle': repository.create_bundle(bundle)}
    except BundleError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))
    except DuplicateReferenceError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A bundle already exists for this approved record and specification')


@app.get('/api/reference-bundles')
def list_reference_bundles(_: None = Depends(require_reference_token)):
    repository = reference_repository()
    return {'bundles': repository.list_bundles(), 'activeTargets': repository.active_bundle_registry()['targets']}


@app.post('/api/reference-bundles/{bundle_id}/activate')
def activate_reference_bundle(bundle_id: str, activation: ReferenceBundleActivation, _: None = Depends(require_reference_token)):
    repository = reference_repository()
    try:
        bundle = repository.get_bundle(bundle_id)
    except InvalidReferenceIdentifierError:
        bundle = None
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reference bundle not found')
    try:
        active = repository.activate_bundle(
            bundle['targetId'], bundle_id, activation.reviewerCode,
            activation.decisionDate.isoformat(), activation.reason,
        )
        return {'activeBundle': active}
    except ReferenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Only an approved bundle with an approved reference record can become active')


@app.post('/api/validation/preview')
def validation_preview(sample: Sample):
    target = knowledge_graph().find_target(sample.target)
    if not target:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Sample target is not in the current core release')
    repository = reference_repository()
    canonical_target_id = target['targetId']
    bundle = repository.get_active_bundle(canonical_target_id)
    if bundle:
        try:
            annotation = repository.get_annotation(canonical_target_id, bundle['id'])
            evidence = provisional_bundle_evidence(sample.model_dump(), bundle, target['sourceRefs'], annotation)
        except (FeatureError, FormMatchError, StrokeMatchError, KudlitRuleError) as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))
        calibration = repository.get_calibration(canonical_target_id, bundle['id'])
        if calibration:
            form = score_form_measurements(evidence['form']['evidence'][1]['measurements'], calibration, target_id=canonical_target_id, reference_bundle_id=bundle['id'])
            stroke = score_stroke_measurements(evidence['stroke']['evidence'][1]['measurements'], calibration, target_id=canonical_target_id, reference_bundle_id=bundle['id'])
            form['sourceRefs'] = target['sourceRefs']
            stroke['sourceRefs'] = target['sourceRefs']
            return combine_validation(canonical_target_id, form, stroke, bundle['id'])
        return combine_validation(canonical_target_id, evidence['form'], evidence['stroke'], bundle['id'])
    has_inactive_bundle = any(item['targetId'] == canonical_target_id for item in repository.list_bundles())
    reason = 'reference_bundle_activation_pending' if has_inactive_bundle else 'reference_bundle_missing'
    form = unavailable_branch_result('form', reason, target['sourceRefs'])
    stroke = unavailable_branch_result('stroke', reason, target['sourceRefs'])
    return combine_validation(canonical_target_id, form, stroke, None)


@app.post('/api/learner-validation')
def validate_learner_practice(sample: Sample):
    """Public, write-free learner endpoint that hides private reference evidence."""
    return learner_result(validation_preview(sample))


@app.post('/api/feedback')
def validation_feedback(request: FeedbackRequest):
    errors = [*request.form.errors, *request.stroke.errors]
    try:
        context = retrieve_feedback_context(knowledge_graph(), request.targetId, errors)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Knowledge-graph target not found')
    return deterministic_feedback(context, {
        'targetId': request.targetId,
        'form': request.form.model_dump(),
        'stroke': request.stroke.model_dump(),
    })


def reference_repository() -> ReferenceRepository:
    return app.state.reference_repository


def knowledge_graph() -> KnowledgeGraph:
    return app.state.knowledge_graph


def expert_batch_manifest() -> dict:
    try:
        import json
        return json.loads(app.state.expert_batch_manifest.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Expert batch manifest is unavailable') from error


def expert_batch_report() -> dict:
    return preflight_batch(
        expert_batch_manifest(), app.state.expert_reference_root, Sample.model_validate,
        knowledge_graph().is_current_release_target,
    )


@app.get('/api/reference-batches/expert-2026-10-24/preflight')
def preflight_expert_batch(_: None = Depends(require_reference_token)):
    return expert_batch_report()


@app.post('/api/reference-batches/expert-2026-10-24/import')
def import_expert_batch(request: ExpertBatchImport, _: None = Depends(require_reference_token)):
    return import_batch(
        expert_batch_manifest(), app.state.expert_reference_root, reference_repository(), Sample.model_validate,
        knowledge_graph().is_current_release_target, request.importerCode,
    )


@app.get('/api/reference-batches/expert-2026-10-24/coverage')
def expert_batch_coverage(_: None = Depends(require_reference_token)):
    records = reference_repository().list_records()
    active = reference_repository().active_bundle_registry()['targets']
    result = []
    for target in knowledge_graph().current_release_targets():
        target_id = target['targetId']
        target_records = [record for record in records if record['target'] == target_id and record['dataClass'] == 'reference']
        result.append({
            'target': target_id,
            'status': 'active' if target_id in active else ('candidate' if any(record['status'] == 'candidate' for record in target_records) else ('approved_inactive' if any(record['status'] == 'approved' for record in target_records) else 'missing')),
        })
    return {'batchId': expert_batch_manifest()['batchId'], 'targets': result}


def target_readiness(target_id: str) -> str:
    records = [
        record for record in reference_repository().list_records()
        if record['target'] == target_id and record['dataClass'] == 'reference'
    ]
    if not records:
        return 'awaiting_candidate'
    approved = [record for record in records if record['status'] == 'approved']
    for record in approved:
        version = record['review'].get('specificationVersion')
        specification = reference_repository().get_specification(target_id, version) if version else None
        if specification and specification['status'] == 'approved':
            return 'reference_ready'
    return 'awaiting_expert_approval'


def public_target(target: dict) -> dict:
    return {**target, 'readiness': target_readiness(target['targetId'])}


@app.post('/api/references', status_code=status.HTTP_201_CREATED)
def create_reference(reference: ReferenceCreate, _: None = Depends(require_reference_token)):
    repository = reference_repository()
    if not knowledge_graph().is_current_release_target(reference.sample.target):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Reference target is not in the current core release')
    sample = reference.sample.model_dump(mode='json')
    record = {
        'target': reference.sample.target,
        'sample': sample,
        'dataClass': reference.dataClass,
        'status': 'candidate',
        'source': reference.source.model_dump(mode='json'),
        'capture': reference.capture.model_dump(mode='json'),
        'review': {
            'reviewerCode': reference.review.reviewerCode,
            'notes': reference.review.notes,
            'decisionDate': None,
            'specificationVersion': None,
        },
        'provenance': {
            'importedAt': datetime.now(timezone.utc).isoformat(),
            'checksum': repository.checksum(sample),
            'schemaVersion': 1,
        },
    }
    try:
        return {'record': repository.create_record(record)}
    except DuplicateReferenceError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This sample is already in the reference library')


@app.get('/api/references')
def list_references(_: None = Depends(require_reference_token)):
    return {'records': reference_repository().list_records()}


@app.post('/api/stroke-annotations', status_code=status.HTTP_201_CREATED)
def create_stroke_annotation(request: StrokeAnnotationCreate, _: None = Depends(require_reference_token)):
    annotation = request.annotation
    target_id, bundle_id = annotation.get('targetId'), annotation.get('referenceBundleId')
    bundle = reference_repository().get_bundle(bundle_id) if isinstance(bundle_id, str) else None
    if not bundle or bundle.get('targetId') != target_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Annotation must reference an existing matching bundle')
    try:
        validate_kudlit_annotation(annotation, target_id=target_id, reference_bundle_id=bundle_id)
        return {'annotation': reference_repository().create_annotation(annotation)}
    except (KudlitRuleError, DuplicateReferenceError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))


@app.get('/api/stroke-annotations')
def list_stroke_annotations(_: None = Depends(require_reference_token)):
    return {'annotations': reference_repository().list_annotations()}


@app.get('/api/references/manifest')
def export_reference_manifest(_: None = Depends(require_reference_token)):
    return reference_repository().manifest()


@app.get('/api/references/{record_id}')
def get_reference(record_id: str, _: None = Depends(require_reference_token)):
    try:
        return {'record': reference_repository().get_record(record_id)}
    except (ReferenceNotFoundError, InvalidReferenceIdentifierError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reference record not found')


@app.post('/api/specifications', status_code=status.HTTP_201_CREATED)
def create_specification(specification: CharacterSpecification, _: None = Depends(require_reference_token)):
    if not knowledge_graph().is_current_release_target(specification.target):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Specification target is not in the current core release')
    try:
        return {'specification': reference_repository().create_specification(specification.model_dump(mode='json'))}
    except DuplicateReferenceError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This specification version already exists')


@app.get('/api/specifications')
def list_specifications(_: None = Depends(require_reference_token)):
    return {'specifications': reference_repository().list_specifications()}


@app.patch('/api/references/{record_id}/review')
def transition_reference_review(record_id: str, transition: ReviewTransition, _: None = Depends(require_reference_token)):
    repository = reference_repository()
    try:
        record = repository.get_record(record_id)
    except (ReferenceNotFoundError, InvalidReferenceIdentifierError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reference record not found')

    allowed = {
        'candidate': {'approved', 'rejected'},
        'approved': {'superseded'},
        'rejected': set(),
        'superseded': set(),
    }
    if transition.status not in allowed[record['status']]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='This record status cannot make that transition')

    if transition.status == 'approved':
        if not transition.specificationVersion:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Approval requires an approved specification version')
        specification = repository.get_specification(record['target'], transition.specificationVersion)
        if not specification or specification['status'] != 'approved':
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Approval requires a matching approved specification')

    record['status'] = transition.status
    record['review'] = transition.model_dump(mode='json')
    return {'record': repository.update_record(record)}
