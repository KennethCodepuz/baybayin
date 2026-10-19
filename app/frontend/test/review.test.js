import test from 'node:test';
import assert from 'node:assert/strict';
import { loadRecording, MAX_IMPORT_BYTES, fitRecording, eventsDue, drawRecordingEvent } from '../lib/review.js';

const makeSample = () => ({
  version: 1, createdAt: '2026-10-18T00:00:00.000Z', target: 'ba',
  canvas: { width: 640, height: 400 }, image: 'data:image/png;base64,aGVsbG8=',
  events: [
    { type: 'down', x: 10, y: 20, timestamp: 100, pointerType: 'pen' },
    { type: 'up', x: 10, y: 20, timestamp: 120, pointerType: 'pen' },
    { type: 'down', x: 30, y: 40, timestamp: 200, pointerType: 'pen' },
    { type: 'move', x: 35, y: 45, timestamp: 210, pointerType: 'pen' },
    { type: 'up', x: 40, y: 50, timestamp: 220, pointerType: 'pen' },
  ],
});
const fileOf = sample => ({ size: 1000, text: async () => JSON.stringify(sample) });

test('loads an existing recording through the backend without changing its values', async () => {
  const sample = makeSample();
  const original = structuredClone(sample);
  let sent;
  const result = await loadRecording(fileOf(sample), async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/api/samples/check');
    assert.equal(options.method, 'POST');
    sent = JSON.parse(options.body);
    return { ok: true };
  });
  assert.deepEqual(sent, original);
  assert.deepEqual(result, original);
  assert.deepEqual(sample, original);
});

test('rejects malformed, oversized, unsupported-version, and unreasonable-dimension files before sending', async () => {
  const unused = () => { throw new Error('Must not send invalid file'); };
  await assert.rejects(loadRecording({ size: MAX_IMPORT_BYTES + 1, text: async () => '' }, unused), /large/i);
  await assert.rejects(loadRecording({ size: 1, text: async () => '{' }, unused), /JSON/i);
  await assert.rejects(loadRecording(fileOf({ ...makeSample(), version: 2 }), unused), /version/i);
  await assert.rejects(loadRecording(fileOf({ ...makeSample(), canvas: { width: 1000001, height: 400 } }), unused), /dimensions/i);
});

test('reports backend rejection and network errors without returning a replacement', async () => {
  const file = fileOf(makeSample());
  await assert.rejects(loadRecording(file, async () => ({ ok: false, status: 422 })), /invalid|incomplete/i);
  await assert.rejects(loadRecording(file, async () => { throw new TypeError('network'); }), /backend/i);
  await assert.rejects(loadRecording(file, async () => ({ ok: false, status: 500 })), /backend/i);
});

test('fits imported dimensions without distortion and centers unused space', () => {
  assert.deepEqual(fitRecording(640, 400, 640, 400), { scale: 1, x: 0, y: 0 });
  assert.deepEqual(fitRecording(400, 400, 640, 400), { scale: 1, x: 120, y: 0 });
  assert.deepEqual(fitRecording(1280, 400, 640, 400), { scale: 0.5, x: 0, y: 100 });
});

test('selects due events in recorded order using time relative to the first event', () => {
  const events = makeSample().events;
  const original = structuredClone(events);
  assert.equal(eventsDue(events, 0, 0), 1);
  assert.equal(eventsDue(events, 1, 19), 1);
  assert.equal(eventsDue(events, 1, 20), 2);
  assert.equal(eventsDue(events, 2, 100), 3);
  assert.equal(eventsDue(events, 3, 120), 5);
  assert.deepEqual(events, original);
});

test('renders a dot and later movement in the same stroke without linking separate strokes', () => {
  const calls = [];
  const ctx = Object.fromEntries(['beginPath', 'arc', 'fill', 'moveTo', 'lineTo', 'stroke'].map(name => [name, (...args) => calls.push([name, ...args])]));
  for (const event of makeSample().events) drawRecordingEvent(ctx, event);
  assert.deepEqual(calls.filter(call => call[0] === 'arc'), [['arc', 10, 20, 2, 0, Math.PI * 2], ['arc', 30, 40, 2, 0, Math.PI * 2]]);
  assert.deepEqual(calls.filter(call => call[0] === 'moveTo'), [['moveTo', 10, 20], ['moveTo', 30, 40]]);
  assert.equal(calls.filter(call => call[0] === 'stroke').length, 3);
});
