import { useState, useEffect } from 'react';
import { PageLayout } from '../../components/layout/PageLayout';
import { ImportDropZone } from '../../components/ui/ImportDropZone';
import { DocumentRow } from '../../components/ui/DocumentRow';
import { Toast } from '../../components/ui/Toast';
import { useBackend } from '../../hooks/useBackend';
import { listDocuments, importFile, importUrl, deleteDocument } from '../../services/api';
import type { Document } from '../../services/api';


function isValidShareUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return (
      u.hostname.endsWith('chatgpt.com') ||
      u.hostname.endsWith('chat.openai.com') ||
      u.hostname.endsWith('claude.ai')
    );
  } catch {
    return false;
  }
}


export default function Import() {
  const { backendUrl } = useBackend();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [urlInput, setUrlInput] = useState('');

  const fetchDocuments = async () => {
    try {
      const docs = await listDocuments(backendUrl);
      setDocuments(docs);
    } catch {
      setToast({ message: 'Failed to load documents', type: 'error' });
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [backendUrl]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const result = await importFile(backendUrl, file);
      setToast({
        message: `Imported "${result.title}" (${result.chunks} chunks)`,
        type: 'success',
      });
      await fetchDocuments();
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : 'Import failed',
        type: 'error',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleUrlImport = async () => {
    const trimmed = urlInput.trim();
    if (!trimmed) return;
    if (!isValidShareUrl(trimmed)) {
      setToast({ message: 'Enter a valid ChatGPT or Claude share link', type: 'error' });
      return;
    }
    setIsUploading(true);
    try {
      const result = await importUrl(backendUrl, trimmed);
      setToast({
        message: `Imported "${result.title}" (${result.chunks} chunks)`,
        type: 'success',
      });
      setUrlInput('');
      await fetchDocuments();
    } catch (err) {
      setToast({
        message: err instanceof Error ? err.message : 'URL import failed',
        type: 'error',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    setIsDeleting(id);
    try {
      await deleteDocument(backendUrl, id);
      setToast({ message: 'Document deleted', type: 'success' });
      await fetchDocuments();
    } catch {
      setToast({ message: 'Failed to delete document', type: 'error' });
    } finally {
      setIsDeleting(null);
    }
  };

  return (
    <PageLayout>
      <div className="max-w-2xl mx-auto py-8">
        <h1 className="text-display font-display font-bold text-cream mb-2">Import</h1>
        <p className="text-body text-muted mb-8">
          Supported: .md .txt .pdf .json .png .jpg .gif .webp .bmp (ChatGPT/Claude), or paste a share link
        </p>

        <ImportDropZone onUpload={handleUpload} isUploading={isUploading} />

        <div className="mt-6 max-w-[480px] mx-auto">
          <p className="text-label font-label text-muted uppercase tracking-[0.2em] mb-3 text-center">
            or paste a share link
          </p>
          <div className="flex gap-2">
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleUrlImport(); }}
              placeholder="https://chatgpt.com/share/..."
              disabled={isUploading}
              className="flex-1 bg-surface border border-border focus:border-amber rounded-md px-4 py-3 text-body text-cream placeholder-dim outline-none transition-colors disabled:opacity-50"
            />
            <button
              onClick={handleUrlImport}
              disabled={isUploading || !urlInput.trim()}
              className="px-5 py-3 bg-amber text-canvas font-medium rounded-md hover:bg-amber/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              {isUploading ? '...' : 'Import'}
            </button>
          </div>
          <p className="text-body-sm text-dim mt-2 text-center">
            Paste a ChatGPT or Claude shared conversation link
          </p>
        </div>

        <div className="mt-12">
          <h2 className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">
            Your Library
          </h2>

          {documents.length === 0 ? (
            <div className="text-center py-12 text-muted text-body-sm">
              No documents yet. Drop a file above to get started.
            </div>
          ) : (
            <div>
              {documents.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  onDelete={handleDelete}
                  isDeleting={isDeleting === doc.id}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}
    </PageLayout>
  );
}