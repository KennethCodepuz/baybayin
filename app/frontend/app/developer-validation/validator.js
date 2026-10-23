'use client';

import { useState } from 'react';
import { apiRequest } from '../../lib/reference-library.js';
import { loadRecording } from '../../lib/review.js';
import { imagePreviewSource, provisionalMeasurements } from '../../lib/validation-preview.js';

export default function DeveloperValidation() {
  const [sample, setSample] = useState(null);
  const [result, setResult] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [status, setStatus] = useState('Load a captured JSON sample to inspect the future hybrid-validator contract.');
  const [busy, setBusy] = useState(false);

  async function chooseFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setBusy(true);
    try {
      const checked = await loadRecording(file);
      const preview = await apiRequest('/validation/preview', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(checked),
      });
      setSample(checked);
      setResult(preview);
      setFeedback(null);
      setStatus('The separate form and stroke branches are ready for approved templates and thresholds. No handwriting score has been produced.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function explain() {
    if (!result || !sample) return;
    setBusy(true);
    try {
      const response = await apiRequest('/feedback', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetId: sample.target, form: { errors: result.form.errors }, stroke: { errors: result.stroke.errors } }),
      });
      setFeedback(response);
      setStatus('Source-grounded fallback feedback generated. An AI provider can later use this same constrained contract.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  return <main>
    <p className="eyebrow">Developer-only · Multimodal validator</p>
    <h1>Hybrid validation inspector</h1>
    <p>Inspect the separate image-form and JSON-stroke validation contracts. This route never returns a learner pass/fail until expert templates and thresholds are approved.</p>
    <label htmlFor="validation-file">Load checked drawing sample</label>
    <input id="validation-file" type="file" accept=".json,application/json" onChange={chooseFile} disabled={busy} />
    <p id="validation-status" role="status" aria-live="polite">{status}</p>
    {result && <section className="review">
      <h2>{sample.target} validation preview</h2>
      {imagePreviewSource(sample) && <figure className="image-preview">
        <img src={imagePreviewSource(sample)} alt={`Recorded ${sample.target} drawing`} />
        <figcaption>Recorded final PNG. This is the image the future form branch compares after normalization.</figcaption>
      </figure>}
      <dl className="sample-details">
        <div><dt>Form branch</dt><dd>{result.form.available ? 'available' : result.form.evidence[0]?.code}</dd></div>
        <div><dt>Stroke branch</dt><dd>{result.stroke.available ? 'available' : result.stroke.evidence[0]?.code}</dd></div>
        <div><dt>Hybrid result</dt><dd>{result.overall.available ? String(result.overall.passed) : 'scoring unavailable'}</dd></div>
        <div><dt>Policy</dt><dd>{result.overall.policyVersion}</dd></div>
      </dl>
      {provisionalMeasurements(result.form) && <p className="hint">Provisional form evidence: mask overlap {provisionalMeasurements(result.form).maskIou?.toFixed(3)}. This is a measurement, not a correctness score.</p>}
      {provisionalMeasurements(result.stroke) && <p className="hint">Provisional stroke evidence: {provisionalMeasurements(result.stroke).comparisons?.length || 0} matched stroke path(s). This is a measurement, not a correctness score.</p>}
      <div className="actions"><button type="button" onClick={explain} disabled={busy}>Generate grounded feedback preview</button></div>
    </section>}
    {feedback && <section className="review">
      <h2>Feedback preview</h2>
      <p>{feedback.message}</p>
      <p className="hint">Sources: {feedback.sourceRefs.join(', ') || 'No applicable approved source yet'}.</p>
    </section>}
  </main>;
}
