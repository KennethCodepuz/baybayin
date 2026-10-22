export const API_ROOT = 'http://127.0.0.1:8000/api';

export function createCandidatePayload(sample, metadata) {
  const pages = metadata.pages.split(',').map(page => page.trim()).filter(Boolean);
  if (!pages.length) throw new Error('Add at least one source page.');
  if (!metadata.convention.trim() || !metadata.inputMethod.trim() || !metadata.reviewerCode.trim() || !metadata.notes.trim()) {
    throw new Error('Complete the convention, input method, reviewer code, and notes.');
  }
  return {
    sample,
    dataClass: metadata.dataClass,
    source: { title: metadata.sourceTitle || 'Pinagyamang Baybáyin (Lopez 2025)', pages, convention: metadata.convention.trim() },
    capture: { inputMethod: metadata.inputMethod.trim() },
    review: { reviewerCode: metadata.reviewerCode.trim(), notes: metadata.notes.trim() },
  };
}

export async function readApiError(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') return body.detail;
  } catch {}
  return 'The local backend could not complete this request.';
}

export async function apiRequest(path, options = {}, request = fetch) {
  let response;
  try {
    response = await request(`${API_ROOT}${path}`, options);
  } catch {
    throw new Error('Cannot reach the backend. Make sure FastAPI is running on port 8000.');
  }
  if (!response.ok) throw new Error(await readApiError(response));
  return response.json();
}
