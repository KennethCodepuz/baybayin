'use client';

import { useEffect, useRef, useState } from 'react';
import { DrawingCapture } from '../../lib/capture.js';
import { catalogTargets, selectedTarget } from '../../lib/knowledge-graph.js';
import { apiRequest } from '../../lib/reference-library.js';
import Link from 'next/link';

const WIDTH = 800;
const HEIGHT = 600;
const GRID_LEFT = 100;
const GRID_TOP = 100;
const GRID_WIDTH = 600;
const GRID_HEIGHT = 400;

function resetCanvas(canvas) {
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = '#1b2a20';
  context.fillStyle = '#1b2a20';
  context.lineWidth = 6;
  context.lineCap = 'round';
  context.lineJoin = 'round';
}

function drawEvent(canvas, event, lastPoint) {
  const context = canvas.getContext('2d');
  if (event.type === 'down') {
    context.beginPath();
    context.arc(event.x, event.y, 3, 0, Math.PI * 2);
    context.fill();
    return { x: event.x, y: event.y };
  }
  if (!lastPoint) return lastPoint;
  context.beginPath();
  context.moveTo(lastPoint.x, lastPoint.y);
  context.lineTo(event.x, event.y);
  context.stroke();
  return event.type === 'up' ? null : { x: event.x, y: event.y };
}

function redraw(canvas, events) {
  resetCanvas(canvas);
  events.reduce((lastPoint, event) => drawEvent(canvas, event, lastPoint), null);
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

function guideAsset(target) {
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
    x: left, y: top, width: right - left + 1, height: bottom - top + 1,
  };
}

function drawGuide(canvas, target, visible) {
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  if (!visible || !target) return;
  const image = new Image();
  image.onload = () => {
    const bounds = referenceBounds(image);
    const aspectRatio = bounds.width / bounds.height;
    const width = Math.min(GRID_WIDTH, GRID_HEIGHT * aspectRatio);
    const height = width / aspectRatio;
    const left = (WIDTH - width) / 2;
    const top = (HEIGHT - height) / 2;
    context.globalAlpha = 0.18;
    context.drawImage(image, bounds.x, bounds.y, bounds.width, bounds.height, left, top, width, height);
    if (['be', 'bi', 'bo', 'bu', 'b', 'b_'].includes(target)) {
      const above = ['be', 'bi', 'b_'].includes(target);
      const x = WIDTH / 2;
      const y = above ? GRID_TOP / 2 : GRID_TOP + GRID_HEIGHT + GRID_TOP / 2;
      const scale = width / bounds.width;
      context.strokeStyle = '#1b2a20';
      context.fillStyle = '#1b2a20';
      context.lineWidth = 8 * scale;
      context.lineCap = 'round';
      context.beginPath();
      if (['bi', 'bu'].includes(target)) {
        context.arc(x, y, 8 * scale, 0, Math.PI * 2);
        context.fill();
      } else {
        const cancellation = ['b', 'b_'].includes(target);
        context.moveTo(x - (cancellation ? 5 : 14) * scale, y - (cancellation ? 12 : 0) * scale);
        context.lineTo(x + (cancellation ? 5 : 14) * scale, y + (cancellation ? 12 : 0) * scale);
        context.stroke();
      }
    }
    context.globalAlpha = 1;
  };
  image.src = `/reference-images/${encodeURIComponent(guideAsset(target))}.png`;
}

function feedbackText(item) {
  const labels = {
    wrong_stroke_count: 'Try using the same number of strokes as the reference.',
    wrong_stroke_order: 'Try drawing the strokes in the reference order.',
    wrong_stroke_direction: 'Try following the reference stroke direction.',
    misplaced_kudlit: 'Check the position of the kudlit.',
    missing_kudlit: 'Check whether the required kudlit is present.',
  };
  return labels[item] || 'Try again while following the visual guide.';
}

export default function LearnerPractice() {
  const canvasRef = useRef(null);
  const guideRef = useRef(null);
  // Match developer capture: the space outside the base grid is needed for kudlit marks.
  const captureRef = useRef(new DrawingCapture(WIDTH, HEIGHT));
  const pointerRef = useRef(null);
  const [catalog, setCatalog] = useState(null);
  const [target, setTarget] = useState('');
  const [guideVisible, setGuideVisible] = useState(false);
  const [status, setStatus] = useState('Choose a character, then draw it in the grid.');
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    resetCanvas(canvasRef.current);
    apiRequest('/knowledge-graph/catalog').then(setCatalog).catch(error => setStatus(error.message));
  }, []);

  useEffect(() => {
    if (guideRef.current) drawGuide(guideRef.current, target, guideVisible);
  }, [target, guideVisible]);

  function down(event) {
    if (busy || pointerRef.current !== null || event.button !== 0) return;
    event.preventDefault();
    pointerRef.current = event.pointerId;
    event.currentTarget.setPointerCapture(event.pointerId);
    const data = point(event.currentTarget, event);
    captureRef.current.start(data);
    drawEvent(event.currentTarget, { type: 'down', ...data }, null);
    setResult(null);
    setStatus('Drawing in progress.');
  }

  function move(event) {
    if (event.pointerId !== pointerRef.current) return;
    const data = point(event.currentTarget, event);
    captureRef.current.move(data);
    redraw(event.currentTarget, captureRef.current.events);
  }

  function up(event) {
    if (event.pointerId !== pointerRef.current) return;
    const data = point(event.currentTarget, event);
    captureRef.current.end(data);
    pointerRef.current = null;
    redraw(event.currentTarget, captureRef.current.events);
    setStatus(`${captureRef.current.strokeCount} stroke${captureRef.current.strokeCount === 1 ? '' : 's'} recorded. You can check your practice when ready.`);
  }

  function interrupt(event) {
    if (event.pointerId !== pointerRef.current) return;
    captureRef.current.cancel(point(event.currentTarget, event));
    pointerRef.current = null;
    setStatus('Drawing interrupted. Select Try again before checking it.');
  }

  function clear() {
    if (pointerRef.current !== null) return setStatus('Finish the current stroke first.');
    captureRef.current.clear();
    redraw(canvasRef.current, []);
    setResult(null);
    setStatus('Ready to try again.');
  }

  function undo() {
    if (!captureRef.current.undoStroke()) return setStatus('There is no completed stroke to undo.');
    redraw(canvasRef.current, captureRef.current.events);
    setResult(null);
    setStatus(`${captureRef.current.strokeCount} stroke${captureRef.current.strokeCount === 1 ? '' : 's'} remaining.`);
  }

  async function submit() {
    try {
      const chosen = selectedTarget(catalog, target);
      if (!chosen) throw new Error('Choose a character before checking your practice.');
      const sample = captureRef.current.sample(target, canvasRef.current.toDataURL('image/png'));
      setBusy(true);
      setStatus('Checking your practice…');
      const response = await apiRequest('/learner-validation', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sample),
      });
      setResult(response);
      setExplanation(null);
      setStatus(response.message);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function explain() {
    if (!result?.feedbackResultId) return;
    setBusy(true);
    try {
      const response = await apiRequest('/learner-feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resultId: result.feedbackResultId }) });
      setExplanation(response);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  const targets = catalogTargets(catalog);
  const chosen = selectedTarget(catalog, target);
  return <main>
    <header className="app-header">
      <div><p className="eyebrow">Baybayin practice</p><h1>Learn one stroke at a time.</h1></div>
      <Link className="quiet-link" href="/developer-login">Developer access</Link>
    </header>
    <p className="lead">Choose a character, follow the guide if you need it, and check your practice when you are ready. The space outside the grid is available for marks such as kudlit.</p>
    <ol className="practice-steps" aria-label="Practice steps"><li><span>1</span>Choose</li><li><span>2</span>Draw</li><li><span>3</span>Check</li></ol>
    <label htmlFor="learner-target">Character to practice</label>
    <select id="learner-target" value={target} onChange={event => { setTarget(event.target.value); clear(); }} disabled={busy || !targets.length}>
      <option value="">{targets.length ? 'Select a character' : 'Loading characters…'}</option>
      {targets.map(item => <option key={item.id} value={item.targetId}>{item.label}</option>)}
    </select>
    <p className="hint">{chosen ? `Source-backed guide · ${chosen.sourceRefs.join(', ')}` : 'The reference guide and grid are visual aids only.'}</p>
    <div className="canvas-wrap learner-canvas">
      <canvas ref={guideRef} className="reference-canvas" width={WIDTH} height={HEIGHT} aria-hidden="true" />
      <svg className="drawing-canvas-grid" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none" aria-hidden="true">
        <line x1={GRID_LEFT + GRID_WIDTH / 4} y1={GRID_TOP} x2={GRID_LEFT + GRID_WIDTH / 4} y2={GRID_TOP + GRID_HEIGHT} />
        <line x1={GRID_LEFT + GRID_WIDTH / 2} y1={GRID_TOP} x2={GRID_LEFT + GRID_WIDTH / 2} y2={GRID_TOP + GRID_HEIGHT} />
        <line x1={GRID_LEFT + GRID_WIDTH * 3 / 4} y1={GRID_TOP} x2={GRID_LEFT + GRID_WIDTH * 3 / 4} y2={GRID_TOP + GRID_HEIGHT} />
        <line x1={GRID_LEFT} y1={GRID_TOP + GRID_HEIGHT / 3} x2={GRID_LEFT + GRID_WIDTH} y2={GRID_TOP + GRID_HEIGHT / 3} />
        <line x1={GRID_LEFT} y1={GRID_TOP + GRID_HEIGHT * 2 / 3} x2={GRID_LEFT + GRID_WIDTH} y2={GRID_TOP + GRID_HEIGHT * 2 / 3} />
        <rect x={GRID_LEFT} y={GRID_TOP} width={GRID_WIDTH} height={GRID_HEIGHT} />
      </svg>
      <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} aria-label="Drawing area. Draw using a mouse, pen, or touch input." onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={interrupt} onLostPointerCapture={interrupt} />
    </div>
    <div className="actions learner-actions">
      <button type="button" onClick={() => setGuideVisible(value => !value)} disabled={!target || busy} aria-pressed={guideVisible}>{guideVisible ? 'Hide guide' : 'Show guide'}</button>
      <button type="button" onClick={undo} disabled={busy}>Undo stroke</button>
      <button type="button" onClick={clear} disabled={busy}>Try again</button>
      <button type="button" className="primary" onClick={submit} disabled={busy || !target}>Check my practice</button>
    </div>
    <p id="learner-status" role="status" aria-live="polite">{status}</p>
    {result && <section className={`review learner-result result-${result.state}`}>
      <p className="result-kicker">Your practice result</p>
      <h2>{result.state === 'unavailable' ? 'Practice comparison unavailable' : result.state === 'prototype_result' ? result.hybrid.state === 'pass' ? 'Prototype match' : 'Try that one again' : 'Practice comparison'}</h2>
      <p>{result.message}</p>
      {result.feedback.items.length > 0 && <ul>{result.feedback.items.map(item => <li key={item}>{feedbackText(item)}</li>)}</ul>}
      {result.feedbackResultId && <div className="actions"><button type="button" onClick={explain} disabled={busy}>{explanation ? 'Explanation ready' : 'Explain this feedback'}</button></div>}
      {explanation && <p className="ai-explanation">{explanation.message}</p>}
      {result.sourceRefs.length > 0 && <p className="hint">Source references: {result.sourceRefs.join(', ')}</p>}
    </section>}
  </main>;
}
