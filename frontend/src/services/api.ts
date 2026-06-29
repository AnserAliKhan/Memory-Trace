/**
 * ReFound API Service
 * All endpoints call the backend at the provided URL.
 * The URL is always passed in – never hardcoded.
 */

// ─── Types ───────────────────────────────────────────────

export interface Document {
  id: number;
  filename: string;
  source_type: string;
  title: string;
  created_at: string;
  chunk_count: number;
  status: 'indexed' | 'failed';
  error_message: string | null;
}

export interface QueryResponse {
  answer: string;
  sources: {
    source: string;
    filename: string;
    score: number;
    excerpt: string;
  }[];
  similar_problems: any[];
  duration_ms: number;
}

export interface QueryHistoryItem {
  id: number;
  query: string;
  answer: string;
  sources: any;
  created_at: string;
  duration_ms: number;
}

export interface ImportResponse {
  status: 'ok' | 'error';
  document_id: number;
  title: string;
  source_type: string;
  chunks: number;
  error?: string;
}

// ─── API Functions ──────────────────────────────────────

/**
 * Check if the backend is reachable.
 * GET /api/health
 */
export async function healthCheck(baseUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${baseUrl}/api/health`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}

/**
 * Import a file (multipart/form-data).
 * POST /api/documents/import
 */
export async function importFile(
  baseUrl: string,
  file: File
): Promise<ImportResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${baseUrl}/api/documents/import`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || 'Import failed');
  }

  return res.json();
}

/**
 * List all imported documents.
 * GET /api/documents/
 */
export async function listDocuments(baseUrl: string): Promise<Document[]> {
  const res = await fetch(`${baseUrl}/api/documents/`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

/**
 * Delete a document by ID.
 * DELETE /api/documents/{id}
 */
export async function deleteDocument(baseUrl: string, id: number): Promise<void> {
  const res = await fetch(`${baseUrl}/api/documents/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
}

/**
 * Submit a query – streaming response.
 * POST /api/query/
 * 
 * Returns a ReadableStream that yields text chunks as they arrive.
 */
export async function queryMemoryStreaming(
  baseUrl: string,
  query: string,
  topK: number = 5
): Promise<ReadableStream<Uint8Array>> {
  const res = await fetch(`${baseUrl}/api/query/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || 'Query failed');
  }

  if (!res.body) {
    throw new Error('No response body');
  }

  return res.body;
}

/**
 * Get query history.
 * GET /api/query/history
 */
export async function getHistory(baseUrl: string): Promise<QueryHistoryItem[]> {
  const res = await fetch(`${baseUrl}/api/query/history`);
  if (!res.ok) throw new Error('Failed to fetch history');
  return res.json();
}