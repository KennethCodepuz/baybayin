'use client';

import { useEffect, useRef, useState } from 'react';
import { drawRecordingEvent, eventsDue, fitRecording, loadRecording } from '../lib/review.js';

function prepareCanvas(canvas, sample) {
  const ctx = canvas.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const fit = fitRecording(sample.canvas.width, sample.canvas.height, canvas.width, canvas.height);
  ctx.setTransform(fit.scale, 0, 0, fit.scale, fit.x, fit.y);
  ctx.strokeStyle = '#1b2a20';
  ctx.fillStyle = '#1b2a20';
  ctx.lineWidth = 4;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  return ctx;
}

function showFullRecording(canvas, sample) {
  const ctx = prepareCanvas(canvas, sample);
  sample.events.forEach(event => drawRecordingEvent(ctx, event));
}

export default function RecordingReview() {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const loadingRef = useRef(false);
  const [sample, setSample] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Choose a saved JSON sample to review.');

  function cancelReplay() {
    if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    animationRef.current = null;
    setPlaying(false);
  }

  useEffect(() => {
    if (sample) showFullRecording(canvasRef.current, sample);
    return () => {
      if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    };
  }, [sample]);

  async function selectFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || loadingRef.current) return;
    cancelReplay();
    if (sample) showFullRecording(canvasRef.current, sample);
    loadingRef.current = true;
    setLoading(true);
    setStatus('Checking the saved sample…');
    try {
      const imported = await loadRecording(file);
      setSample(imported);
      setStatus('Sample opened. The writing has not been validated.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }

  function replay() {
    if (animationRef.current !== null) {
      cancelReplay();
      showFullRecording(canvasRef.current, sample);
      setStatus('Replay stopped.');
      return;
    }
    const ctx = prepareCanvas(canvasRef.current, sample);
    const start = performance.now();
    let index = 0;
    setPlaying(true);
    setStatus('Replaying the saved strokes.');
    function step(now) {
      const end = eventsDue(sample.events, index, now - start);
      while (index < end) drawRecordingEvent(ctx, sample.events[index++]);
      if (index < sample.events.length) animationRef.current = requestAnimationFrame(step);
      else {
        animationRef.current = null;
        setPlaying(false);
        setStatus('Replay complete.');
      }
    }
    animationRef.current = requestAnimationFrame(step);
  }

  function close() {
    cancelReplay();
    setSample(null);
    setStatus('Sample closed. Choose a saved JSON sample to review.');
  }

  return (
    <section className="review" aria-labelledby="review-heading">
      <h2 id="review-heading">Review a saved sample</h2>
      <p>Open a JSON recording to inspect and replay its strokes. Your current drawing will stay separate.</p>
      <label htmlFor="sample-file">Open saved sample</label>
      <input id="sample-file" type="file" accept=".json,application/json" onChange={selectFile} disabled={loading} />
      <p className="hint">Version 1 JSON, up to 32 MiB. The sample is checked by the local backend and is not saved by the app.</p>
      <p className="review-status" role="status" aria-live="polite">{status}</p>
      {sample && <>
        <dl className="sample-details">
          <div><dt>Character label</dt><dd>{sample.target}</dd></div>
          <div><dt>Recorded</dt><dd>{sample.createdAt}</dd></div>
          <div><dt>Canvas</dt><dd>{sample.canvas.width} × {sample.canvas.height}</dd></div>
          <div><dt>Pen contacts</dt><dd>{sample.events.filter(event => event.type === 'down').length}</dd></div>
        </dl>
        <div className="canvas-wrap">
          <canvas ref={canvasRef} width={640} height={400} aria-label="Saved sample stroke replay" />
        </div>
        <div className="actions">
          <button type="button" onClick={replay} disabled={loading}>{playing ? 'Stop replay' : 'Replay saved strokes'}</button>
          <button type="button" onClick={close} disabled={loading}>Close sample</button>
        </div>
        <p className="hint">Pen contacts count recorded pen-down events, not confirmed correct strokes.</p>
      </>}
    </section>
  );
}
