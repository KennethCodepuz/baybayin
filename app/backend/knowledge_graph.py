"""Read and validate the committed Baybayin knowledge graph for local API use."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class KnowledgeGraphError(ValueError):
    pass


@dataclass(frozen=True)
class KnowledgeGraph:
    source_id: str
    targets: tuple[dict, ...]
    target_by_key: dict[str, dict]
    target_by_id: dict[str, dict]

    def current_release_targets(self) -> tuple[dict, ...]:
        return self.targets

    def find_target(self, identifier: str) -> dict | None:
        return self.target_by_id.get(identifier) or self.target_by_key.get(identifier)

    def is_current_release_target(self, identifier: str) -> bool:
        return identifier in self.target_by_key


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise KnowledgeGraphError(f'Missing knowledge-graph file: {path.name}') from error
    except json.JSONDecodeError as error:
        raise KnowledgeGraphError(f'Invalid JSON in knowledge-graph file: {path.name}') from error


def _source_ref_is_valid(value: str, source_id: str) -> bool:
    prefix = f'{source_id}#pdf-page='
    return value.startswith(prefix) and value.removeprefix(prefix).isdigit()


def load_knowledge_graph(root: Path) -> KnowledgeGraph:
    characters = _read_json(root / 'characters.json')
    sources = _read_json(root / 'source-register.json')
    graph = _read_json(root / 'graph.json')

    source_records = sources.get('sources')
    if not isinstance(source_records, list) or len(source_records) != 1:
        raise KnowledgeGraphError('source-register.json must contain exactly one primary source')
    source_id = source_records[0].get('id')
    if not isinstance(source_id, str) or not source_id:
        raise KnowledgeGraphError('Primary source must have an id')

    base = characters.get('baseGraphemes')
    if not isinstance(base, list) or len(base) != 24:
        raise KnowledgeGraphError('characters.json must contain exactly 24 base graphemes')

    graph_nodes = graph.get('nodes')
    graph_edges = graph.get('edges')
    if not isinstance(graph_nodes, list) or not isinstance(graph_edges, list):
        raise KnowledgeGraphError('graph.json must contain nodes and edges')
    node_ids = {node.get('id') for node in graph_nodes if isinstance(node, dict)}
    if len(node_ids) != len(graph_nodes) or None in node_ids:
        raise KnowledgeGraphError('graph.json has duplicate or missing node ids')
    for edge in graph_edges:
        if not isinstance(edge, dict) or edge.get('from') not in node_ids or edge.get('to') not in node_ids:
            raise KnowledgeGraphError('graph.json has an edge with an unknown endpoint')

    target_by_key: dict[str, dict] = {}
    target_by_id: dict[str, dict] = {}
    targets = []
    for record in base:
        if not isinstance(record, dict):
            raise KnowledgeGraphError('Base grapheme record must be an object')
        identifier = record.get('id')
        key = record.get('romanization')
        refs = record.get('sourceRefs')
        if not isinstance(identifier, str) or not identifier or not isinstance(key, str) or not key:
            raise KnowledgeGraphError('Every base grapheme needs an id and romanization')
        if identifier in target_by_id or key in target_by_key:
            raise KnowledgeGraphError('Base grapheme ids and romanizations must be unique')
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and _source_ref_is_valid(ref, source_id) for ref in refs):
            raise KnowledgeGraphError(f'Base grapheme {identifier} has invalid source references')
        target = {
            'id': identifier,
            'targetId': key,
            'label': key,
            'phoneme': record.get('phoneme'),
            'class': record.get('class'),
            'sourceRefs': refs,
            'release': 'core',
            'scoringAvailable': False,
        }
        target_by_id[identifier] = target
        target_by_key[key] = target
        targets.append(target)

    return KnowledgeGraph(
        source_id=source_id,
        targets=tuple(targets),
        target_by_key=target_by_key,
        target_by_id=target_by_id,
    )