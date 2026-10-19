'use client';

import { useEffect, useRef, useState } from 'react';
import { DrawingCapture } from '../lib/capture.js';
import RecordingReview from './recording-review.js';

const apiUrl = 'http://127.0.0.1:8000';

function blankCanvas(canvas) {
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#1b2a20';
  ctx.fillStyle = '#1b2a20';
  ctx.lineWidth = 4;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
}

function drawEvent(canvas, event) {
  const ctx = canvas.getContext('2d');
  if (event.type === 'down') {
    ctx.beginPath();
    ctx.arc(event.x, event.y, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(event.x, event.y);
  } else if (event.type === 'move' || event.type === 'up') {
    ctx.lineTo(event.x, event.y);
    ctx.stroke();
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
  const captureRef = useRef(null);
  const pointerRef = useRef(null);
  const animationRef = useRef(null);
  const busyRef = useRef(false);
  const [target, setTarget] = useState('');
  const [status, setStatus] = useState('Ready to draw.');
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!captureRef.current) captureRef.current = new DrawingCapture(640, 400);
    blankCanvas(canvasRef.current);
    return () => {
      if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    };
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
      link.download = 'baybayin-drawing-sample.json';
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

  return (
    <main>
      <p className="eyebrow">Research prototype · Capture pilot</p>
      <h1>Baybayin drawing capture</h1>
      <p>Record a drawing and its stroke sequence for later review. This prototype does not yet validate character forms or writing rules.</p>
      <label htmlFor="target">Character you intend to draw</label>
      <input id="target" value={target} onChange={event => setTarget(event.target.value)} maxLength={100} placeholder="For example: ka" autoComplete="off" disabled={busy} />
      <p className="hint">Enter the character’s name to identify your sample. You can draw before filling this in. Do not enter a participant’s name.</p>
      <div className="canvas-wrap">
        <canvas ref={canvasRef} width={640} height={400} aria-label="Drawing area. Draw using a mouse, pen, or touch input."
          onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={interrupt} onLostPointerCapture={interrupt} />
      </div>
      <div className="actions">
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
