import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createAssessment, createCase, getHealth, sendCaseChatStream, uploadDocument } from './api';
import './styles.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [caseData, setCaseData] = useState(null);
  const [caseForm, setCaseForm] = useState({
    case_type: 'commercial_dispute',
    description: '',
    current_stage: 'initial_review',
    lawyer_proposed_action: '',
  });
  const [caseState, setCaseState] = useState('idle');
  const [caseError, setCaseError] = useState('');
  const [documentState, setDocumentState] = useState('idle');
  const [documentData, setDocumentData] = useState(null);
  const [documentError, setDocumentError] = useState('');
  const [assessmentState, setAssessmentState] = useState('idle');
  const [assessment, setAssessment] = useState(null);
  const [assessmentError, setAssessmentError] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatState, setChatState] = useState('idle');
  const [chatError, setChatError] = useState('');

  useEffect(() => {
    getHealth().then(() => setBackendStatus('connected')).catch(() => setBackendStatus('unreachable'));
  }, []);

  function updateCaseField(event) {
    setCaseForm({ ...caseForm, [event.target.name]: event.target.value });
  }

  async function handleCaseSubmit(event) {
    event.preventDefault();
    setCaseState('loading');
    setCaseError('');
    setDocumentData(null);
    setDocumentState('idle');
    try {
      const createdCase = await createCase({
        ...caseForm,
        lawyer_proposed_action: caseForm.lawyer_proposed_action || null,
      });
      setCaseData(createdCase);
      setCaseState('success');
      setAssessment(null);
      setAssessmentState('idle');
      setAssessmentError('');
      setChatMessages([]);
      setChatInput('');
      setChatError('');
    } catch (error) {
      setCaseState('error');
      setCaseError(error.message);
    }
  }

  async function handleAssessmentGenerate() {
    if (!caseData) return;
    setAssessmentState('loading');
    setAssessmentError('');
    try {
      const generated = await createAssessment(caseData.id);
      setAssessment(generated);
      setAssessmentState('success');
    } catch (error) {
      setAssessmentState('error');
      setAssessmentError(error.message);
    }
  }

  async function handleChatSubmit(event) {
    event.preventDefault();
    if (!caseData || !chatInput.trim() || chatState === 'loading') return;
    const outgoing = chatInput.trim();
    const activeCaseId = caseData.id;
    const pendingId = `pending-${Date.now()}`;
    setChatInput('');
    setChatState('loading');
    setChatError('');
    try {
      await sendCaseChatStream(activeCaseId, outgoing, (streamEvent) => {
        if (streamEvent.type === 'user') {
          setChatMessages((previous) => [...previous, streamEvent.message]);
        } else if (streamEvent.type === 'delta') {
          setChatMessages((previous) => {
            const last = previous[previous.length - 1];
            if (last && last.id === pendingId) {
              return [...previous.slice(0, -1), { ...last, content: last.content + streamEvent.text }];
            }
            return [...previous, {
              id: pendingId,
              case_id: activeCaseId,
              role: 'assistant',
              content: streamEvent.text,
              citations: [],
              requires_human_review: true,
              created_at: new Date().toISOString(),
            }];
          });
        } else if (streamEvent.type === 'done') {
          setChatMessages((previous) => {
            const last = previous[previous.length - 1];
            if (last && last.id === pendingId) return [...previous.slice(0, -1), streamEvent.message];
            return [...previous, streamEvent.message];
          });
        } else if (streamEvent.type === 'error') {
          throw new Error(streamEvent.detail || 'Case chat is unavailable.');
        }
      });
      setChatState('idle');
    } catch (error) {
      setChatState('error');
      setChatError(error.message);
    }
  }

  async function handleDocumentUpload(event) {
    const file = event.target.files[0];
    if (!file || !caseData) return;
    if (file.size > 10 * 1024 * 1024) {
      setDocumentState('error');
      setDocumentError('This file exceeds the 10 MiB upload limit.');
      return;
    }
    setDocumentState('loading');
    setDocumentError('');
    try {
      const uploadedDocument = await uploadDocument(caseData.id, file);
      setDocumentData(uploadedDocument);
      setDocumentState('success');
    } catch (error) {
      setDocumentState('error');
      setDocumentError(error.message);
    }
  }

  return (
    <main className="shell">
      <nav className="topbar">
        <strong className="brand">MAWTHOOQ</strong>
        <span className="environment">Development environment</span>
      </nav>
      <section className="welcome">
        <p className="eyebrow">Case intelligence for businesses</p>
        <h1>Build the case record.</h1>
        <p className="intro">
          Create a case, attach its first source document, and keep every next step
          grounded in evidence.
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
        <div className="workspace">
          <div className="section-heading">
            <p className="eyebrow">01 / Case intake</p>
            <h2>Start with the facts.</h2>
          </div>
          <form className="case-form" onSubmit={handleCaseSubmit}>
            <label>Case type
              <select name="case_type" value={caseForm.case_type} onChange={updateCaseField}>
                <option value="commercial_dispute">Commercial dispute</option>
                <option value="employment">Employment</option>
                <option value="contract">Contract</option>
                <option value="debt">Debt</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>Current stage
              <select name="current_stage" value={caseForm.current_stage} onChange={updateCaseField}>
                <option value="complaint">Complaint</option>
                <option value="initial_review">Initial review</option>
                <option value="evidence">Evidence</option>
                <option value="hearing">Hearing</option>
                <option value="judgment">Judgment</option>
                <option value="appeal">Appeal</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="wide">Case description
              <textarea name="description" minLength="10" maxLength="5000" required value={caseForm.description} onChange={updateCaseField} placeholder="Describe what happened and what is currently known." />
            </label>
            <label className="wide">Proposed lawyer action <span className="optional">Optional</span>
              <textarea name="lawyer_proposed_action" maxLength="2000" value={caseForm.lawyer_proposed_action} onChange={updateCaseField} placeholder="What action is being considered?" />
            </label>
            <button type="submit" disabled={caseState === 'loading'}>
              {caseState === 'loading' ? 'Saving case...' : 'Save case'}
            </button>
            {caseState === 'error' && <p className="form-error" role="alert">{caseError}</p>}
          </form>
          {caseData && <section className="result-panel">
            <div className="result-header"><span className="tag">Case created</span><span className="case-status">{caseData.status}</span></div>
            <h2>{caseData.case_type.replace('_', ' ')}</h2>
            <p>{caseData.description}</p>
            <dl><div><dt>Stage</dt><dd>{caseData.current_stage.replace('_', ' ')}</dd></div><div><dt>Case ID</dt><dd>{caseData.id}</dd></div></dl>
          </section>}
          {caseData && <section className="upload-panel">
            <div className="section-heading"><p className="eyebrow">02 / Evidence</p><h2>Attach a source document.</h2></div>
            <p className="muted">PDF, DOCX, JPG, PNG, WebP, or GIF. Maximum 10 MiB.</p>
            <input type="file" accept=".pdf,.docx,image/jpeg,image/png,image/webp,image/gif" onChange={handleDocumentUpload} disabled={documentState === 'loading'} />
            {documentState === 'loading' && <p className="notice">Uploading and checking the file...</p>}
            {documentState === 'error' && <p className="form-error" role="alert">{documentError}</p>}
            {documentData && <div className="document-result"><span className="tag">Uploaded</span><strong>{documentData.filename}</strong><span>{Math.ceil(documentData.size_bytes / 1024)} KB · {documentData.processing_status}</span><small>Extraction will be added in the next processing step.</small></div>}
          </section>}
          {caseData && <section className="intelligence-panel">
            <div className="section-heading"><p className="eyebrow">03 / AI intelligence</p><h2>Assessment and case chat.</h2></div>
            <p className="disclaimer">AI decision support only — requires human lawyer review. It never replaces a lawyer or predicts a court outcome.</p>
            <button type="button" onClick={handleAssessmentGenerate} disabled={assessmentState === 'loading'}>
              {assessmentState === 'loading' ? 'Generating assessment...' : 'Generate legal assessment'}
            </button>
            {assessmentState === 'error' && <p className="form-error" role="alert">{assessmentError}</p>}
            {assessment && <article className="assessment-result">
              <span className="tag">Assessment · {assessment.provider}/{assessment.model}</span>
              <p className="assessment-summary">{assessment.summary}</p>
              <h3>What happens next</h3>
              <ul>{assessment.what_happens_next.map((item, index) => <li key={index}>{typeof item === 'string' ? item : item.text}</li>)}</ul>
              <h3>Risks</h3>
              <ul>{assessment.risks.map((risk, index) => <li key={index}>{typeof risk === 'string' ? risk : JSON.stringify(risk)}</li>)}</ul>
              <h3>Questions for your lawyer</h3>
              <ul>{assessment.recommended_lawyer_questions.map((question, index) => <li key={index}>{typeof question === 'string' ? question : JSON.stringify(question)}</li>)}</ul>
              <h3>Citations</h3>
              <ul className="citation-list">{assessment.citations.map((citation, index) => <li key={index}>{typeof citation === 'string' ? citation : `${citation.source_id || ''} ${citation.location || ''}`.trim()}</li>)}</ul>
            </article>}
            <div className="chat-panel">
              <h3>Ask about this case</h3>
              <div className="chat-log">
                {chatMessages.length === 0 && <p className="muted">No messages yet. Ask a follow-up question about the case.</p>}
                {chatMessages.map((entry) => (
                  <div key={entry.id} className={`chat-message ${entry.role}`}>
                    <strong>{entry.role === 'user' ? 'You' : 'Case agent'}</strong>
                    <p>{entry.content}</p>
                  </div>
                ))}
              </div>
              <form className="chat-form" onSubmit={handleChatSubmit}>
                <input type="text" value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Ask about procedure, risks, or next steps..." maxLength={2000} disabled={chatState === 'loading'} />
                <button type="submit" disabled={chatState === 'loading' || !chatInput.trim()}>{chatState === 'loading' ? 'Thinking...' : 'Send'}</button>
              </form>
              {chatState === 'error' && <p className="form-error" role="alert">{chatError}</p>}
            </div>
          </section>}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode><App /></StrictMode>,
);
