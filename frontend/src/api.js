const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseResponse(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : `Request failed (HTTP ${response.status})`;
    throw new Error(detail);
  }
  return body;
}

export async function getHealth() {
  return parseResponse(await fetch(`${apiBaseUrl}/health`));
}

export async function createCase(payload) {
  return parseResponse(await fetch(`${apiBaseUrl}/api/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }));
}

export async function uploadDocument(caseId, file) {
  const formData = new FormData();
  formData.append('file', file);
  return parseResponse(await fetch(`${apiBaseUrl}/api/cases/${caseId}/documents`, {
    method: 'POST',
    body: formData,
  }));
}

export async function getDocumentStatus(documentId) {
  return parseResponse(await fetch(`${apiBaseUrl}/api/documents/${documentId}/status`));
}

export async function createAssessment(caseId) {
  return parseResponse(await fetch(`${apiBaseUrl}/api/cases/${caseId}/assessments`, {
    method: 'POST',
  }));
}

export async function listAssessments(caseId) {
  return parseResponse(await fetch(`${apiBaseUrl}/api/cases/${caseId}/assessments`));
}

export async function sendCaseChat(caseId, message) {
  return parseResponse(await fetch(`${apiBaseUrl}/api/cases/${caseId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  }));
}

export async function listCaseMessages(caseId) {
  return parseResponse(await fetch(`${apiBaseUrl}/api/cases/${caseId}/messages`));
}

export async function sendCaseChatStream(caseId, message, onEvent) {
  const response = await fetch(`${apiBaseUrl}/api/cases/${caseId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : `Request failed (HTTP ${response.status})`;
    throw new Error(detail);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop();
    for (const part of parts) {
      const line = part.split('\n').find((candidate) => candidate.startsWith('data:'));
      if (line) onEvent(JSON.parse(line.slice(5).trim()));
    }
  }
}
