import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    fetch(`${apiBaseUrl}/health`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then(() => setBackendStatus('connected'))
      .catch(() => setBackendStatus('unreachable'));
  }, [apiBaseUrl]);

  return (
    <main className="shell">
      <nav className="topbar">
        <strong className="brand">MAWTHOOQ</strong>
        <span className="environment">Development environment</span>
      </nav>
      <section className="welcome">
        <p className="eyebrow">Case intelligence for businesses</p>
        <h1>See the case clearly.</h1>
        <p className="intro">
          Understand what happened, what comes next, and what should be verified
          before making a legal decision.
        </p>
        <div className="status-row">
          <span className="status-dot" />
          <span>Frontend is running</span>
        </div>
        <div className={`status-row backend-status ${backendStatus}`}>
          <span className="status-dot" />
          <span>
            Backend: {backendStatus === 'checking' ? 'checking connection...' : backendStatus}
          </span>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode><App /></StrictMode>,
);
