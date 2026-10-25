import Link from 'next/link';

export default function DeveloperPage() {
  return <main>
    <header className="app-header"><div><p className="eyebrow">Developer area</p><h1>Research workspace</h1></div><Link className="quiet-link" href="/">Learner home</Link></header>
    <p className="lead">Manage expert references, collect calibration samples, and inspect the deterministic validation pipeline.</p>
    <div className="actions developer-actions">
      <Link className="button-link" href="/developer/capture">Record calibration sample</Link>
      <Link className="button-link primary" href="/developer-reference-library">Reference library</Link>
      <Link className="button-link" href="/developer-validation">Validation inspector</Link>
      <Link className="button-link" href="/">Learner home</Link>
    </div>
  </main>;
}
