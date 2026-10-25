'use client';

import { useState } from 'react';

export default function DeveloperLogin() {
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState('Enter the local developer password.');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const response = await fetch('/api/developer-access', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) });
      if (!response.ok) throw new Error('Incorrect developer password.');
      window.location.assign('/developer');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  return <main>
    <p className="eyebrow">Restricted area</p>
    <h1>Developer access</h1>
    <p className="lead">This local prototype keeps research tools separate from learner practice.</p>
    <form className="library-form" onSubmit={submit}>
      <label htmlFor="developer-password">Password</label>
      <input id="developer-password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required />
      <div className="actions"><button className="primary" type="submit" disabled={busy}>Go to developer tools</button></div>
    </form>
    <p role="status" aria-live="polite">{status}</p>
  </main>;
}
