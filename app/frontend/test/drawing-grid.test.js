import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('renders a four-column, three-row visual grid outside the saved drawing canvas', async () => {
  const source = await readFile(new URL('../app/drawing-canvas.js', import.meta.url), 'utf8');

  assert.match(source, /className="drawing-canvas-grid"/);
  assert.match(source, /viewBox="0 0 600 450"/);
  assert.match(source, /x1="150"/);
  assert.match(source, /x1="300"/);
  assert.match(source, /x1="450"/);
  assert.match(source, /y1="150"/);
  assert.match(source, /y1="300"/);
  assert.match(source, /canvasRef\.current\.toDataURL\('image\/png'\)/);
});
