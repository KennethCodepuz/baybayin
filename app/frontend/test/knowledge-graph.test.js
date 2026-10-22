import assert from 'node:assert/strict';
import test from 'node:test';

import { catalogTargets, selectedTarget } from '../lib/knowledge-graph.js';

const catalog = {
  sourceId: 'lopez-2025-pdf',
  targets: [
    { id: 'vowel-a', targetId: 'a', label: 'a', class: 'vowel', sourceRefs: ['lopez-2025-pdf#pdf-page=56'], readiness: 'awaiting_candidate', scoringAvailable: false },
    { id: 'consonant-ba', targetId: 'ba', label: 'ba', phoneme: '/b/', class: 'consonant_a', sourceRefs: ['lopez-2025-pdf#pdf-page=56'], readiness: 'reference_ready', scoringAvailable: false },
  ],
};

test('returns source-backed selectable targets without enabling scoring', () => {
  const targets = catalogTargets(catalog);
  assert.equal(targets.length, 2);
  assert.equal(targets[1].targetId, 'ba');
  assert.equal(targets[1].scoringAvailable, false);
});

test('finds a target by its sample target ID and rejects unknown values', () => {
  assert.equal(selectedTarget(catalog, 'ba').id, 'consonant-ba');
  assert.equal(selectedTarget(catalog, 'nope'), null);
  assert.deepEqual(catalogTargets({ targets: [] }), []);
});