import assert from 'node:assert/strict';
import test from 'node:test';

import { createCandidatePayload, readApiError } from '../lib/reference-library.js';

const sample = {
  version: 1,
  createdAt: '2026-10-20T00:00:00.000Z',
  target: 'ba',
  canvas: { width: 640, height: 400 },
  image: 'data:image/png;base64,aGVsbG8=',
  events: [
    { type: 'down', x: 10, y: 20, timestamp: 0, pointerType: 'pen' },
    { type: 'up', x: 10, y: 20, timestamp: 10, pointerType: 'pen' },
  ],
};

test('creates candidate metadata without changing the checked sample', () => {
  const payload = createCandidatePayload(sample, {
    pages: '7, 8', convention: 'pinagyamang-baybayin', inputMethod: 'pen',
    reviewerCode: 'pending', notes: 'Awaiting expert review.', dataClass: 'reference',
  });

  assert.equal(payload.sample, sample);
  assert.deepEqual(payload.source.pages, ['7', '8']);
  assert.equal(payload.dataClass, 'reference');
  assert.equal(payload.review.notes, 'Awaiting expert review.');
});

test('rejects targets outside the small developer pilot and missing review metadata', () => {
  assert.throws(() => createCandidatePayload({ ...sample, target: 'nga' }, {
    pages: '7', convention: 'pinagyamang-baybayin', inputMethod: 'pen',
    reviewerCode: 'pending', notes: 'Awaiting expert review.', dataClass: 'reference',
  }), /ba and ka/);
  assert.throws(() => createCandidatePayload(sample, {
    pages: '', convention: 'pinagyamang-baybayin', inputMethod: 'pen',
    reviewerCode: '', notes: '', dataClass: 'reference',
  }), /source page/);
});

test('uses a backend error detail when available and a stable fallback otherwise', async () => {
  assert.equal(await readApiError({ json: async () => ({ detail: 'Duplicate sample.' }) }), 'Duplicate sample.');
  assert.equal(await readApiError({ json: async () => { throw new Error('not JSON'); } }), 'The local backend could not complete this request.');
});
