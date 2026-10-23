import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('renders a four-column, three-row visual grid outside the saved drawing canvas', async () => {
  const source = await readFile(new URL('../app/drawing-canvas.js', import.meta.url), 'utf8');

  assert.match(source, /className="drawing-canvas-grid"/);
  assert.match(source, /x1="160"/);
  assert.match(source, /x1="320"/);
  assert.match(source, /x1="480"/);
  assert.match(source, /y1="133\.333"/);
  assert.match(source, /y1="266\.667"/);
  assert.match(source, /canvasRef\.current\.toDataURL\('image\/png'\)/);
});
