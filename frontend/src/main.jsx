import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
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
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode><App /></StrictMode>,
);
