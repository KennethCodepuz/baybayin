import assert from 'node:assert/strict';
import test from 'node:test';

import { imagePreviewSource, provisionalMeasurements } from '../lib/validation-preview.js';

test('returns a PNG data URL only for a captured image preview', () => {
  assert.equal(imagePreviewSource({ image: 'data:image/png;base64,aGVsbG8=' }), 'data:image/png;base64,aGVsbG8=');
  assert.equal(imagePreviewSource({ image: 'not-an-image' }), null);
  assert.equal(imagePreviewSource(null), null);
});

test('finds provisional measurement evidence without treating it as a score', () => {
  const result = {
    form: { evidence: [{ code: 'expert_thresholds_pending' }, { code: 'provisional_measurements', measurements: { maskIou: 0.8 } }] },
    stroke: { evidence: [{ code: 'expert_thresholds_pending' }] },
  };

  assert.deepEqual(provisionalMeasurements(result.form), { maskIou: 0.8 });
  assert.equal(provisionalMeasurements(result.stroke), null);
});
