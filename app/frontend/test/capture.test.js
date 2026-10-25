import test from 'node:test';
import assert from 'node:assert/strict';
import { DrawingCapture } from '../lib/capture.js';

const point = (x, y, timestamp, pointerType = 'pen') => ({ x, y, timestamp, pointerType });

test('captures ordered strokes and returns the final image and dimensions', () => {
  const capture = new DrawingCapture(640, 400);
  capture.start(point(10, 20, 100));
  capture.move(point(30, 40, 112));
  capture.end(point(35, 45, 120));
  capture.start(point(50, 60, 140, 'touch'));
  capture.end(point(50, 60, 150, 'touch'));
  const sample = capture.sample(' ka ', 'data:image/png;base64,abc');
  assert.equal(sample.target, 'ka');
  assert.deepEqual(sample.canvas, { width: 640, height: 400 });
  assert.equal(sample.image, 'data:image/png;base64,abc');
  assert.deepEqual(sample.events.map(event => event.type), ['down', 'move', 'up', 'down', 'up']);
  assert.equal(capture.strokeCount, 2);
  sample.events[0].x = 999;
  assert.equal(capture.events[0].x, 10);
});

test('refuses missing targets, empty, unfinished and interrupted drawings', () => {
  const capture = new DrawingCapture(640, 400);
  assert.throws(() => capture.sample('ka', 'image'), /draw/i);
  capture.start(point(1, 2, 10));
  assert.throws(() => capture.sample('ka', 'image'), /finish/i);
  capture.cancel(point(3, 4, 11));
  assert.throws(() => capture.sample('ka', 'image'), /interrupted/i);
  capture.clear();
  capture.start(point(1, 2, 12));
  capture.end(point(3, 4, 13));
  assert.throws(() => capture.sample(' ', 'image'), /target/i);
});

test('ignores stray pointer events and extra starts', () => {
  const capture = new DrawingCapture(640, 400);
  capture.move(point(1, 2, 1));
  capture.end(point(1, 2, 2));
  capture.start(point(1, 2, 3));
  capture.start(point(3, 4, 4));
  capture.end(point(5, 6, 5));
  assert.equal(capture.strokeCount, 1);
  assert.deepEqual(capture.events.map(event => event.type), ['down', 'up']);
});

test('undo removes only the latest completed stroke', () => {
  const capture = new DrawingCapture(600, 450);
  capture.start(point(1, 2, 1));
  capture.end(point(3, 4, 2));
  capture.start(point(5, 6, 3));
  capture.end(point(7, 8, 4));
  capture.undoStroke();
  assert.equal(capture.strokeCount, 1);
  assert.deepEqual(capture.events.map(event => event.type), ['down', 'up']);
});
