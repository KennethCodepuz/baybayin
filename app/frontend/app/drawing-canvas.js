'use client';

import { useEffect, useRef, useState } from 'react';
import { DrawingCapture } from '../lib/capture.js';
import { catalogTargets, selectedTarget } from '../lib/knowledge-graph.js';
import { apiRequest } from '../lib/reference-library.js';
import RecordingReview from './recording-review.js';

const apiUrl = 'http://127.0.0.1:8000';
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const GRID_LEFT = 100;
const GRID_TOP = 100;
const GRID_WIDTH = 600;
const GRID_HEIGHT = 400;

function blankCanvas(canvas) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#1b2a20';
  ctx.fillStyle = '#1b2a20';
  ctx.lineWidth = 6;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
}

function blankReferenceCanvas(canvas) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function referenceAssetName(target) {
  if (['be', 'bi', 'bo', 'bu', 'b', 'b_'].includes(target)) return 'ba';
  return ['a', 'e', 'i', 'o', 'u'].includes(target) ? target.toUpperCase() : target;
}

function referenceBounds(image) {
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
  return right < 0 ? { x: 0, y: 0, width: image.width, height: image.height } : {
    x: left,
    y: top,
    width: right - left + 1,
    height: bottom - top + 1,
  };
}

function drawReference(canvas, target, setGridLayout) {
  blankReferenceCanvas(canvas);
  if (!target) {
    setGridLayout({ left: GRID_LEFT, top: GRID_TOP, width: GRID_WIDTH, height: GRID_HEIGHT });
    return;
  }
  const image = new Image();
  image.onload = () => {
    const ctx = canvas.getContext('2d');
    const bounds = referenceBounds(image);
    const aspectRatio = bounds.width / bounds.height;
    const width = Math.min(GRID_WIDTH, GRID_HEIGHT * aspectRatio);
    const height = width / aspectRatio;
    const layout = {
      left: (CANVAS_WIDTH - width) / 2,
      top: (CANVAS_HEIGHT - height) / 2,
      width,
      height,
    };
    setGridLayout(layout);
    const scale = width / bounds.width;
    ctx.globalAlpha = 0.2;
    ctx.drawImage(image, bounds.x, bounds.y, bounds.width, bounds.height,
      layout.left, layout.top, layout.width, layout.height);
    if (['be', 'bi', 'bo', 'bu', 'b', 'b_'].includes(target)) {
      const x = canvas.width / 2;
      const above = ['be', 'bi', 'b_'].includes(target);
      const y = above ? GRID_TOP / 2 : GRID_TOP + GRID_HEIGHT + GRID_TOP / 2;
      ctx.strokeStyle = 'black';
      ctx.fillStyle = 'black';
      ctx.lineWidth = 8 * scale;
      ctx.lineCap = 'round';
      ctx.beginPath();
      if (['bi', 'bu'].includes(target)) {
        ctx.arc(x, y, 8 * scale, 0, Math.PI * 2);
        ctx.fill();
      } else {
        const cancellation = ['b', 'b_'].includes(target);
        ctx.moveTo(x - (cancellation ? 5 : 14) * scale, y - (cancellation ? 12 : 0) * scale);
        ctx.lineTo(x + (cancellation ? 5 : 14) * scale, y + (cancellation ? 12 : 0) * scale);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  };
  image.src = `/reference-images/${encodeURIComponent(referenceAssetName(target))}.png`;
}

function sampleFileName(target) {
  const safeTarget = target.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '-').trim();
  return `baybayin-${safeTarget}-drawing-sample.json`;
}

let lastPoint = null;

const NIB_ANGLE = (-40 * Math.PI) / 180;
const NIB_LENGTH = 14;

function drawEvent(canvas, event) {
  const ctx = canvas.getContext('2d');
  if (event.type === 'down') {
    lastPoint = { x: event.x, y: event.y };
    ctx.beginPath();
    ctx.arc(event.x, event.y, 3, 0, Math.PI * 2);
    ctx.fill();
  } else if ((event.type === 'move' || event.type === 'up') && lastPoint) {
    const hx = Math.cos(NIB_ANGLE) * NIB_LENGTH / 2;
    const hy = Math.sin(NIB_ANGLE) * NIB_LENGTH / 2;
    ctx.beginPath();
    ctx.moveTo(lastPoint.x + hx, lastPoint.y + hy);
    ctx.lineTo(event.x + hx, event.y + hy);
    ctx.lineTo(event.x - hx, event.y - hy);
    ctx.lineTo(lastPoint.x - hx, lastPoint.y - hy);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(lastPoint.x, lastPoint.y);
    ctx.lineTo(event.x, event.y);
    ctx.stroke();
    lastPoint = event.type === 'up' ? null : { x: event.x, y: event.y };
  }
}

function point(canvas, event) {
  const bounds = canvas.getBoundingClientRect();
  return {
    x: (event.clientX - bounds.left) * canvas.width / bounds.width,
    y: (event.clientY - bounds.top) * canvas.height / bounds.height,
    timestamp: event.timeStamp,
    pointerType: event.pointerType,
  };
}

export default function DrawingCanvas() {
  const canvasRef = useRef(null);
  const referenceCanvasRef = useRef(null);
  const captureRef = useRef(null);
  const pointerRef = useRef(null);
  const animationRef = useRef(null);
  const busyRef = useRef(false);
  const [target, setTarget] = useState('');
  const [catalog, setCatalog] = useState(null);
  const [status, setStatus] = useState('Ready to draw.');
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [referenceVisible, setReferenceVisible] = useState(false);
  const [gridLayout, setGridLayout] = useState({
    left: GRID_LEFT,
    top: GRID_TOP,
    width: GRID_WIDTH,
    height: GRID_HEIGHT,
  });

  useEffect(() => {
    if (!captureRef.current) captureRef.current = new DrawingCapture(CANVAS_WIDTH, CANVAS_HEIGHT);
    blankCanvas(canvasRef.current);
    blankReferenceCanvas(referenceCanvasRef.current);
    return () => {
      if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  useEffect(() => {
    if (referenceCanvasRef.current) {
      drawReference(referenceCanvasRef.current, referenceVisible ? target : '', setGridLayout);
    }
  }, [referenceVisible, target]);

  useEffect(() => {
    apiRequest('/knowledge-graph/catalog')
      .then(result => setCatalog(result))
      .catch(error => setStatus(`Cannot load writing targets. ${error.message}`));
  }, []);

  function down(event) {
    if (pointerRef.current !== null || event.button !== 0 || animationRef.current !== null || busyRef.current) return;
    event.preventDefault();
    pointerRef.current = event.pointerId;
    event.currentTarget.setPointerCapture(event.pointerId);
    const data = point(event.currentTarget, event);
    captureRef.current.start(data);
    drawEvent(event.currentTarget, { type: 'down', ...data });
    setStatus('Drawing in progress.');
  }

  function move(event) {
    if (event.pointerId !== pointerRef.current) return;
    const data = point(event.currentTarget, event);
    captureRef.current.move(data);
    drawEvent(event.currentTarget, { type: 'move', ...data });
  }

  function up(event) {
    if (event.pointerId !== pointerRef.current) return;
    const data = point(event.currentTarget, event);
    captureRef.current.end(data);
    drawEvent(event.currentTarget, { type: 'up', ...data });
    pointerRef.current = null;
    const count = captureRef.current.strokeCount;
    setStatus(`${count} stroke${count === 1 ? '' : 's'} recorded.`);
  }

  function interrupt(event) {
    if (event.pointerId !== pointerRef.current) return;
    captureRef.current.cancel(point(event.currentTarget, event));
    pointerRef.current = null;
    setStatus('Drawing interrupted. Clear it and try again.');
  }

  function stopReplay() {
    if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    animationRef.current = null;
    setPlaying(false);
    blankCanvas(canvasRef.current);
    captureRef.current.events.forEach(event => drawEvent(canvasRef.current, event));
  }

  function clear() {
    if (pointerRef.current !== null) {
      setStatus('Finish the current stroke first.');
      return;
    }
    stopReplay();
    captureRef.current.clear();
    blankCanvas(canvasRef.current);
    setStatus('Drawing cleared.');
  }

  function replay() {
    if (animationRef.current !== null) {
      stopReplay();
      setStatus('Replay stopped.');
      return;
    }
    const capture = captureRef.current;
    if (!capture.events.length || capture.active || capture.interrupted) {
      setStatus('Finish a complete drawing before replaying.');
      return;
    }
    blankCanvas(canvasRef.current);
    setPlaying(true);
    setStatus('Replaying strokes.');
    let index = 0;
    const firstTime = capture.events[0].timestamp;
    const start = performance.now();
    function step(now) {
      while (index < capture.events.length && capture.events[index].timestamp - firstTime <= now - start) {
        drawEvent(canvasRef.current, capture.events[index++]);
      }
      if (index < capture.events.length) animationRef.current = requestAnimationFrame(step);
      else {
        animationRef.current = null;
        setPlaying(false);
        setStatus('Replay complete.');
      }
    }
    animationRef.current = requestAnimationFrame(step);
  }

  async function download() {
    if (busyRef.current) return;
    try {
      if (animationRef.current !== null) throw new Error('Stop the replay before downloading.');
      if (!selectedTarget(catalog, target)) throw new Error('Select a source-backed character before downloading.');
      const sample = captureRef.current.sample(target, canvasRef.current.toDataURL('image/png'));
      busyRef.current = true;
      setBusy(true);
      setStatus('Checking the sample format with the local backend…');
      let response;
      try {
        response = await fetch(`${apiUrl}/api/samples/check`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sample),
        });
      } catch {
        throw new Error('Cannot reach the backend. Make sure FastAPI is running on port 8000.');
      }
      if (!response.ok) throw new Error('The backend could not accept this sample. Check the drawing and try again.');
      const result = await response.json();
      const url = URL.createObjectURL(new Blob([JSON.stringify(result.sample, null, 2)], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = sampleFileName(target);
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setStatus('Sample downloaded. Its format was checked; the writing was not validated.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  const targets = catalogTargets(catalog);
  const selected = selectedTarget(catalog, target);

  return (
    <main>
      <p className="eyebrow">Research prototype · Capture pilot</p>
      <h1>Baybayin drawing capture</h1>
      <p>Record a drawing and its stroke sequence for later review. This prototype does not yet validate character forms or writing rules.</p>
      <label htmlFor="target">Character you intend to draw</label>
      <select id="target" value={target} onChange={event => setTarget(event.target.value)} disabled={busy || !targets.length}>
        <option value="">{targets.length ? 'Select a character' : 'Loading source-backed characters…'}</option>
        {targets.map(item => <option key={item.id} value={item.targetId}>{item.label}{item.phoneme ? ` (${item.phoneme})` : ''}</option>)}
      </select>
      <p className="hint">{selected ? `${selected.label} is from ${selected.sourceRefs.join(', ')}. Its writing is not scored yet.` : 'Select a source-backed character to identify the sample. Do not enter a participant’s name.'}</p>
      <div className="canvas-wrap">
        <canvas ref={referenceCanvasRef} className="reference-canvas" width={CANVAS_WIDTH} height={CANVAS_HEIGHT}
          aria-hidden="true" />
        <svg className="drawing-canvas-grid" viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`} preserveAspectRatio="none" aria-hidden="true">
          <line x1={gridLayout.left + gridLayout.width / 4} y1={gridLayout.top}
            x2={gridLayout.left + gridLayout.width / 4} y2={gridLayout.top + gridLayout.height} />
          <line x1={gridLayout.left + gridLayout.width / 2} y1={gridLayout.top}
            x2={gridLayout.left + gridLayout.width / 2} y2={gridLayout.top + gridLayout.height} />
          <line x1={gridLayout.left + gridLayout.width * 3 / 4} y1={gridLayout.top}
            x2={gridLayout.left + gridLayout.width * 3 / 4} y2={gridLayout.top + gridLayout.height} />
          <line x1={gridLayout.left} y1={gridLayout.top + gridLayout.height / 3}
            x2={gridLayout.left + gridLayout.width} y2={gridLayout.top + gridLayout.height / 3} />
          <line x1={gridLayout.left} y1={gridLayout.top + gridLayout.height * 2 / 3}
            x2={gridLayout.left + gridLayout.width} y2={gridLayout.top + gridLayout.height * 2 / 3} />
          <rect x={gridLayout.left} y={gridLayout.top} width={gridLayout.width} height={gridLayout.height} />
        </svg>
        <canvas ref={canvasRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} aria-label="Drawing area. Draw using a mouse, pen, or touch input."
          onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={interrupt} onLostPointerCapture={interrupt} />
      </div>
      <div className="actions">
        <button type="button" onClick={() => setReferenceVisible(visible => !visible)}
          disabled={busy || !target} aria-pressed={referenceVisible}>
          {referenceVisible ? 'Hide image reference' : 'Show image reference'}
        </button>
        <button type="button" onClick={clear} disabled={busy}>Clear drawing</button>
        <button type="button" onClick={replay} disabled={busy}>{playing ? 'Stop replay' : 'Replay strokes'}</button>
        <button className="primary" type="button" onClick={download} disabled={busy}>Download sample</button>
      </div>
      <p id="status" role="status" aria-live="polite">{status}</p>
      <p className="hint">The downloaded JSON contains the drawing image, coordinates, timestamps, and input type. Keep research samples in an approved location.</p>
      <RecordingReview />
    </main>
  );
}
