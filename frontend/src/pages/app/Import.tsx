import { useState, useEffect } from 'react';
import { PageLayout } from '../../components/layout/PageLayout';
import { ImportDropZone } from '../../components/ui/ImportDropZone';
import { DocumentRow } from '../../components/ui/DocumentRow';
import { Toast } from '../../components/ui/Toast';
import { useBackend } from '../../hooks/useBackend';
import { listDocuments, importFile, deleteDocument } from '../../services/api';
import type { Document } from '../../services/api';


export default function Import() {
  const { backendUrl } = useBackend();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

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
        {/* Page header */}
        <h1 className="text-display font-display font-bold text-cream mb-2">Import</h1>
        <p className="text-body text-muted mb-8">
          Supported formats: .md .txt .pdf .json (ChatGPT export)
        </p>

        {/* Drop zone */}
        <ImportDropZone onUpload={handleUpload} isUploading={isUploading} />

        {/* Library section */}
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

      {/* Toast */}
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