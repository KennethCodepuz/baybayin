'use client';

import { useEffect, useRef, useState } from 'react';
import { apiRequest, createCandidatePayload } from '../../lib/reference-library.js';
import { drawRecordingEvent, eventsDue, fitRecording, loadRecording } from '../../lib/review.js';

const initialMetadata = {
  pages: '', convention: 'pinagyamang-baybayin', inputMethod: 'pen',
  reviewerCode: 'pending', notes: 'Awaiting expert review.', dataClass: 'reference',
};

function renderRecording(canvas, sample) {
  const context = canvas.getContext('2d');
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.fillStyle = 'white';
  context.fillRect(0, 0, canvas.width, canvas.height);
  const fit = fitRecording(sample.canvas.width, sample.canvas.height, canvas.width, canvas.height);
  context.setTransform(fit.scale, 0, 0, fit.scale, fit.x, fit.y);
  context.strokeStyle = '#1b2a20';
  context.fillStyle = '#1b2a20';
  context.lineWidth = 4;
  context.lineCap = 'round';
  context.lineJoin = 'round';
  return context;
}

function RecordingPreview({ sample }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [playing, setPlaying] = useState(false);

  function stop() {
    if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    animationRef.current = null;
    setPlaying(false);
    const context = renderRecording(canvasRef.current, sample);
    sample.events.forEach(event => drawRecordingEvent(context, event));
  }

  useEffect(() => {
    stop();
    return () => {
      if (animationRef.current !== null) cancelAnimationFrame(animationRef.current);
    };
  }, [sample]);

  function replay() {
    if (playing) {
      stop();
      return;
    }
    const context = renderRecording(canvasRef.current, sample);
    const started = performance.now();
    let index = 0;
    setPlaying(true);
    function step(now) {
      const due = eventsDue(sample.events, index, now - started);
      while (index < due) drawRecordingEvent(context, sample.events[index++]);
      if (index < sample.events.length) animationRef.current = requestAnimationFrame(step);
      else {
        animationRef.current = null;
        setPlaying(false);
      }
    }
    animationRef.current = requestAnimationFrame(step);
  }

  return <>
    <div className="canvas-wrap"><canvas ref={canvasRef} width={640} height={400} aria-label="Reference recording replay" /></div>
    <div className="actions"><button type="button" onClick={replay}>{playing ? 'Stop replay' : 'Replay recording'}</button></div>
  </>;
}

export default function ReferenceLibrary() {
  const [candidate, setCandidate] = useState(null);
  const [metadata, setMetadata] = useState(initialMetadata);
  const [records, setRecords] = useState([]);
  const [specifications, setSpecifications] = useState([]);
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState('Load a saved JSON drawing to create a candidate reference.');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [recordResult, specificationResult] = await Promise.all([
      apiRequest('/references'), apiRequest('/specifications'),
    ]);
    setRecords(recordResult.records);
    setSpecifications(specificationResult.specifications);
  }

  useEffect(() => { refresh().catch(error => setStatus(error.message)); }, []);

  function changeMetadata(event) {
    setMetadata(current => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function chooseFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setBusy(true);
    try {
      const sample = await loadRecording(file);
      if (!['ba', 'ka'].includes(sample.target)) throw new Error('The developer pilot currently supports only samples labelled ba or ka.');
      setCandidate(sample);
      setSelected(null);
      setMetadata(current => ({ ...current, pages: sample.target === 'ba' ? '7' : '15' }));
      setStatus('Sample checked. Complete the candidate metadata before saving it.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function saveCandidate(event) {
    event.preventDefault();
    if (!candidate) return;
    setBusy(true);
    try {
      const result = await apiRequest('/references', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createCandidatePayload(candidate, metadata)),
      });
      setCandidate(null);
      setSelected(result.record);
      setStatus(`Saved ${result.record.id} as a candidate reference.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function transition(record, nextStatus) {
    const reviewerCode = window.prompt('Reviewer code');
    if (!reviewerCode) return;
    const notes = window.prompt('Decision notes');
    if (!notes) return;
    let specificationVersion;
    if (nextStatus === 'approved') {
      specificationVersion = window.prompt(`Approved ${record.target} specification version`);
      if (!specificationVersion) return;
    }
    setBusy(true);
    try {
      const result = await apiRequest(`/references/${record.id}/review`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus, reviewerCode, notes, decisionDate: new Date().toISOString().slice(0, 10), specificationVersion }),
      });
      setSelected(result.record);
      setStatus(`Record ${result.record.id} is now ${result.record.status}.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function createSpecification() {
    const target = window.prompt('Target character: ba or ka');
    const version = window.prompt('Specification version, for example ba-1.0');
    const reviewerCode = window.prompt('Reviewer code');
    if (!target || !version || !reviewerCode) return;
    setBusy(true);
    try {
      await apiRequest('/specifications', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target, version, status: 'approved', reviewerCode, decisionDate: new Date().toISOString().slice(0, 10),
          source: { title: 'Pagsulat ng Baybayin', pages: [target === 'ba' ? '7' : '15'], convention: 'pinagyamang-baybayin' },
        }),
      });
      setStatus(`Saved approved ${target} specification ${version}.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  const shown = selected || candidate;
  return <main>
    <p className="eyebrow">Developer-only · Reference library</p>
    <h1>Baybayin reference library</h1>
    <p>Curate expert-reviewed recordings for validator development. A candidate recording is not ground truth until it is linked to an approved specification.</p>
    <label htmlFor="reference-file">Load checked drawing sample</label>
    <input id="reference-file" type="file" accept=".json,application/json" onChange={chooseFile} disabled={busy} />
    <p id="reference-status" role="status" aria-live="polite">{status}</p>

    {candidate && <form className="library-form" onSubmit={saveCandidate}>
      <h2>Candidate metadata: {candidate.target}</h2>
      <label htmlFor="pages">Source page or pages</label><input id="pages" name="pages" value={metadata.pages} onChange={changeMetadata} required />
      <label htmlFor="convention">Writing convention</label><input id="convention" name="convention" value={metadata.convention} onChange={changeMetadata} required />
      <label htmlFor="input-method">Input method</label><input id="input-method" name="inputMethod" value={metadata.inputMethod} onChange={changeMetadata} required />
      <label htmlFor="reviewer-code">Reviewer code</label><input id="reviewer-code" name="reviewerCode" value={metadata.reviewerCode} onChange={changeMetadata} required />
      <label htmlFor="review-notes">Review notes</label><input id="review-notes" name="notes" value={metadata.notes} onChange={changeMetadata} required />
      <label htmlFor="data-class">Data class</label><select id="data-class" name="dataClass" value={metadata.dataClass} onChange={changeMetadata}><option value="reference">Reference candidate</option><option value="test">Test fixture</option></select>
      <div className="actions"><button className="primary" type="submit" disabled={busy}>Save candidate reference</button></div>
    </form>}

    {shown && <section className="review"><h2>{selected ? `Record ${selected.id}` : 'Candidate preview'}</h2>
      <p><strong>Status:</strong> {selected?.status || 'unsaved candidate'} · <strong>Target:</strong> {shown.target}</p>
      <RecordingPreview sample={shown.sample || shown} />
      {selected?.status === 'candidate' && <div className="actions">
        <button type="button" disabled={busy} onClick={() => transition(selected, 'approved')}>Approve with specification</button>
        <button type="button" disabled={busy} onClick={() => transition(selected, 'rejected')}>Mark rejected</button>
      </div>}
    </section>}

    <section className="review"><h2>Stored records</h2>
      <div className="actions"><button type="button" onClick={createSpecification} disabled={busy}>Add approved specification</button><button type="button" onClick={() => refresh().catch(error => setStatus(error.message))} disabled={busy}>Refresh library</button></div>
      <p className="hint">Approved specifications: {specifications.map(specification => `${specification.target} ${specification.version}`).join(', ') || 'none yet'}.</p>
      {records.length ? <ul className="record-list">{records.map(record => <li key={record.id}><button type="button" onClick={() => setSelected(record)}>{record.target} - {record.status} - {record.id.slice(0, 12)}</button></li>)}</ul> : <p>No stored records yet.</p>}
    </section>
  </main>;
}
