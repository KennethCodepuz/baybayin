'use client';

import { useEffect, useRef, useState } from 'react';
import { catalogTargets, selectedTarget } from '../../lib/knowledge-graph.js';
import { apiRequest, createCandidatePayload } from '../../lib/reference-library.js';
import { drawRecordingEvent, eventsDue, fitRecording, loadRecording } from '../../lib/review.js';

const initialMetadata = {
  pages: '', convention: 'pinagyamang-baybayin', inputMethod: 'pen',
  reviewerCode: 'pending', notes: 'Awaiting expert review.', dataClass: 'reference',
  sourceTitle: 'Pinagyamang Baybáyin (Lopez 2025)',
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
  const [bundles, setBundles] = useState([]);
  const [batchReport, setBatchReport] = useState(null);
  const [coverage, setCoverage] = useState([]);
  const [catalog, setCatalog] = useState(null);
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState('Load a saved JSON drawing to create a candidate reference.');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [recordResult, specificationResult, bundleResult, coverageResult] = await Promise.all([
      apiRequest('/references'), apiRequest('/specifications'), apiRequest('/reference-bundles'), apiRequest('/reference-batches/expert-2026-10-24/coverage'),
    ]);
    setRecords(recordResult.records);
    setSpecifications(specificationResult.specifications);
    setBundles(bundleResult.bundles);
    setCoverage(coverageResult.targets);
  }

  useEffect(() => {
    const token = window.sessionStorage.getItem('baybayin-reference-token') || window.prompt('Enter the local reference-library token');
    if (token) window.sessionStorage.setItem('baybayin-reference-token', token);
    Promise.all([refresh(), apiRequest('/knowledge-graph/catalog')])
      .then(([, graph]) => setCatalog(graph))
      .catch(error => setStatus(error.message));
  }, []);

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
      const graphTarget = selectedTarget(catalog, sample.target);
      if (!graphTarget) throw new Error('This sample target is not part of the current core knowledge-graph release.');
      setCandidate(sample);
      setSelected(null);
      setMetadata(current => ({ ...current, pages: graphTarget.sourceRefs.join(', ') }));
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

  async function preflightExpertBatch() {
    setBusy(true);
    try {
      const result = await apiRequest('/reference-batches/expert-2026-10-24/preflight');
      setBatchReport(result);
      setStatus(result.ready ? `Expert batch preflight passed for ${result.entries.length} recordings. Review the file list, then import candidates.` : 'Expert batch preflight is blocked. Review the listed file errors.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function importExpertBatch() {
    const importerCode = window.prompt('Developer/importer code for this audit entry');
    if (!importerCode) return;
    setBusy(true);
    try {
      const result = await apiRequest('/reference-batches/expert-2026-10-24/import', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ importerCode }),
      });
      setBatchReport(result);
      setStatus(result.ready ? `Imported ${result.imported} expert candidates; ${result.duplicates} were already present. They still require reviewer approval and bundle activation.` : 'Import was blocked because the expert batch did not pass preflight.');
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

  async function createBundle(record) {
    setBusy(true);
    try {
      const result = await apiRequest('/reference-bundles', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ referenceRecordId: record.id }),
      });
      setStatus(`Created multimodal bundle ${result.bundle.id}. An expert reviewer must activate it before preview can use it.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function activateBundle(bundle) {
    const reviewerCode = window.prompt('Expert reviewer code for activation');
    if (!reviewerCode) return;
    const reason = window.prompt('Reason for selecting this bundle');
    if (!reason) return;
    setBusy(true);
    try {
      await apiRequest(`/reference-bundles/${bundle.id}/activate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewerCode, decisionDate: new Date().toISOString().slice(0, 10), reason }),
      });
      setStatus(`Activated ${bundle.id}. Preview may now show provisional measurements, never a learner score.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function createSpecification() {
    const target = window.prompt(`Target character: ${targets.map(item => item.targetId).join(', ')}`);
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
  const targets = catalogTargets(catalog);
  const shownTarget = shown ? selectedTarget(catalog, shown.target) : null;
  return <main>
    <p className="eyebrow">Developer-only · Reference library</p>
    <h1>Baybayin reference library</h1>
    <p>Curate expert-reviewed recordings for validator development. A candidate recording is not ground truth until it is linked to an approved specification.</p>
    <label htmlFor="reference-file">Load checked drawing sample</label>
    <input id="reference-file" type="file" accept=".json,application/json" onChange={chooseFile} disabled={busy || !targets.length} />
    <p id="reference-status" role="status" aria-live="polite">{status}</p>

    {candidate && <form className="library-form" onSubmit={saveCandidate}>
      <h2>Candidate metadata: {candidate.target}</h2>
      <p className="hint">Current release status: {selectedTarget(catalog, candidate.target)?.readiness}. Candidate recordings are not validator ground truth.</p>
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
      {shownTarget && <p className="hint"><strong>Source references:</strong> {shownTarget.sourceRefs.join(', ')}{shownTarget.markForm ? ` · Kudlit: ${shownTarget.markForm.replaceAll('_', ' ')} (${shownTarget.markPosition})` : ''}.</p>}
      {selected?.provenance?.expertBatchId && <p className="hint"><strong>Expert batch:</strong> {selected.provenance.expertBatchId} · {selected.provenance.sourceFile} · SHA-256 {selected.provenance.sourceFileSha256.slice(0, 12)}… · collected {selected.provenance.collectionDate}. This provenance is immutable; approving this record is a separate reviewer decision.</p>}
      <RecordingPreview sample={shown.sample || shown} />
      {selected?.status === 'candidate' && <div className="actions">
        <button type="button" disabled={busy} onClick={() => transition(selected, 'approved')}>Approve with specification</button>
        <button type="button" disabled={busy} onClick={() => transition(selected, 'rejected')}>Mark rejected</button>
      </div>}
      {selected?.status === 'approved' && <div className="actions">
        <button type="button" disabled={busy} onClick={() => createBundle(selected)}>Create multimodal reference bundle</button>
        {bundles.filter(bundle => bundle.referenceRecordId === selected.id).map(bundle => <button key={bundle.id} type="button" disabled={busy} onClick={() => activateBundle(bundle)}>Activate {bundle.id.slice(0, 18)}</button>)}
      </div>}
    </section>}

    <section className="review"><h2>Verified expert batch</h2>
      <p>Checks the private originals against the reviewed manifest before creating candidate copies. Importing does not approve, bundle, activate, or score any recording.</p>
      <div className="actions"><button type="button" onClick={preflightExpertBatch} disabled={busy}>Preflight 12 expert recordings</button><button type="button" className="primary" onClick={importExpertBatch} disabled={busy || !batchReport?.ready}>Import verified candidates</button></div>
      {batchReport && <ul className="record-list">{batchReport.entries.map(entry => <li key={entry.file}><strong>{entry.target || 'unknown'}</strong> · {entry.file || 'unknown file'} · {entry.status}{entry.detail ? ` — ${entry.detail}` : ''}</li>)}</ul>}
      <p className="hint">Coverage: {coverage.map(item => `${item.target}: ${item.status}`).join(' · ') || 'loading…'}</p>
    </section>

    <section className="review"><h2>Stored records</h2>
      <div className="actions"><button type="button" onClick={createSpecification} disabled={busy}>Add approved specification</button><button type="button" onClick={() => refresh().catch(error => setStatus(error.message))} disabled={busy}>Refresh library</button></div>
      <p className="hint">Approved specifications: {specifications.map(specification => `${specification.target} ${specification.version}`).join(', ') || 'none yet'}.</p>
      {records.length ? <ul className="record-list">{records.map(record => <li key={record.id}><button type="button" onClick={() => setSelected(record)}>{record.target} - {record.status} - {record.id.slice(0, 12)}{record.provenance?.expertBatchId ? ' - verified expert batch' : ''}</button></li>)}</ul> : <p>No stored records yet.</p>}
    </section>
  </main>;
}
