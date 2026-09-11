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
