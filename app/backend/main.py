from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from knowledge_graph import KnowledgeGraph, load_knowledge_graph
from reference_library import DuplicateReferenceError, ReferenceNotFoundError, ReferenceRepository


class Canvas(BaseModel):
    model_config = ConfigDict(extra='forbid')
    width: int = Field(gt=0)
    height: int = Field(gt=0)


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
    events: list[Event] = Field(min_length=2, max_length=100_000)

    @field_validator('target')
    @classmethod
    def target_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError('Target character must not be blank')
        return value

    @model_validator(mode='after')
    def complete_strokes(self):
        active = False
        last_timestamp = -1
        for event in self.events:
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


app = FastAPI(title='Baybayin capture API')
app.state.reference_repository = ReferenceRepository(Path(__file__).resolve().parent.parent / 'data' / 'reference-library')
app.state.knowledge_graph = load_knowledge_graph(Path(__file__).resolve().parents[2] / 'knowledge-graph')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_methods=['GET', 'POST', 'PATCH'],
    allow_headers=['Content-Type'],
)


@app.post('/api/samples/check')
def check_sample(sample: Sample):
    # Checks capture structure only; this does not validate Baybayin writing.
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


def reference_repository() -> ReferenceRepository:
    return app.state.reference_repository


def knowledge_graph() -> KnowledgeGraph:
    return app.state.knowledge_graph


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
def create_reference(reference: ReferenceCreate):
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
def list_references():
    return {'records': reference_repository().list_records()}


@app.get('/api/references/manifest')
def export_reference_manifest():
    return reference_repository().manifest()


@app.get('/api/references/{record_id}')
def get_reference(record_id: str):
    try:
        return {'record': reference_repository().get_record(record_id)}
    except ReferenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reference record not found')


@app.post('/api/specifications', status_code=status.HTTP_201_CREATED)
def create_specification(specification: CharacterSpecification):
    if not knowledge_graph().is_current_release_target(specification.target):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Specification target is not in the current core release')
    try:
        return {'specification': reference_repository().create_specification(specification.model_dump(mode='json'))}
    except DuplicateReferenceError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='This specification version already exists')


@app.get('/api/specifications')
def list_specifications():
    return {'specifications': reference_repository().list_specifications()}


@app.patch('/api/references/{record_id}/review')
def transition_reference_review(record_id: str, transition: ReviewTransition):
    repository = reference_repository()
    try:
        record = repository.get_record(record_id)
    except ReferenceNotFoundError:
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
