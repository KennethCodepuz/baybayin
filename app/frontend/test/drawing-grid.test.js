import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('renders a four-column, three-row visual grid outside the saved drawing canvas', async () => {
  const source = await readFile(new URL('../app/drawing-canvas.js', import.meta.url), 'utf8');

  assert.match(source, /className="drawing-canvas-grid"/);
  assert.match(source, /CANVAS_WIDTH = 800/);
  assert.match(source, /CANVAS_HEIGHT = 600/);
  assert.match(source, /gridLayout\.left \+ gridLayout\.width \/ 4/);
  assert.match(source, /gridLayout\.left \+ gridLayout\.width \* 3 \/ 4/);
  assert.match(source, /width=\{gridLayout\.width\} height=\{gridLayout\.height\}/);
  assert.match(source, /canvasRef\.current\.toDataURL\('image\/png'\)/);
});
