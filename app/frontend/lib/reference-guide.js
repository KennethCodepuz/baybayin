const VOWELS = new Set(['a', 'e', 'i', 'o', 'u']);
const MODIFIED_TARGETS = new Set(['be', 'bi', 'bo', 'bu', 'b', 'b_']);
const ABOVE_TARGETS = new Set(['be', 'bi', 'b_']);
const DOT_TARGETS = new Set(['bi', 'bu']);
const CANCELLATION_TARGETS = new Set(['b', 'b_']);

export function referenceAssetName(target) {
  if (MODIFIED_TARGETS.has(target)) return 'ba';
  return VOWELS.has(target) ? target.toUpperCase() : target;
}

export function referenceBounds(image) {
  const source = document.createElement('canvas');
  source.width = image.width;
  source.height = image.height;
  const context = source.getContext('2d');
  context.drawImage(image, 0, 0);
  const pixels = context.getImageData(0, 0, image.width, image.height).data;
  let left = image.width;
  let top = image.height;
  let right = -1;
  let bottom = -1;

  for (let y = 0; y < image.height; y += 1) {
    for (let x = 0; x < image.width; x += 1) {
      const index = (y * image.width + x) * 4;
      if (pixels[index] < 245 || pixels[index + 1] < 245 || pixels[index + 2] < 245) {
        left = Math.min(left, x);
        top = Math.min(top, y);
        right = Math.max(right, x);
        bottom = Math.max(bottom, y);
      }
    }
  }

  return right < 0
    ? { x: 0, y: 0, width: image.width, height: image.height }
    : { x: left, y: top, width: right - left + 1, height: bottom - top + 1 };
}

export function drawReferenceMark(context, target, x, y, scale, color = '#1b2a20') {
  if (!MODIFIED_TARGETS.has(target)) return;

  context.strokeStyle = color;
  context.fillStyle = color;
  context.lineWidth = 8 * scale;
  context.lineCap = 'round';
  context.beginPath();
  if (DOT_TARGETS.has(target)) {
    context.arc(x, y, 8 * scale, 0, Math.PI * 2);
    context.fill();
    return;
  }

  const cancellation = CANCELLATION_TARGETS.has(target);
  context.moveTo(x - (cancellation ? 5 : 14) * scale, y - (cancellation ? 12 : 0) * scale);
  context.lineTo(x + (cancellation ? 5 : 14) * scale, y + (cancellation ? 12 : 0) * scale);
  context.stroke();
}

export function referenceMarkPosition(target, gridTop, gridHeight, canvasWidth) {
  return {
    x: canvasWidth / 2,
    y: ABOVE_TARGETS.has(target) ? gridTop / 2 : gridTop + gridHeight + gridTop / 2,
  };
}
