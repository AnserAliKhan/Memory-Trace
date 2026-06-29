import { useState } from 'react';
import { useBackend } from '../../hooks/useBackend';

interface BackendModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnected: () => void; // Will navigate to /app/search
}

export function BackendModal({ isOpen, onClose, onConnected }: BackendModalProps) {
  const { connect, isLoading, error, backendUrl } = useBackend();
  const [url, setUrl] = useState(backendUrl);

  const handleConnect = async () => {
    const success = await connect(url);
    if (success) {
      onConnected();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    // Overlay
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 backdrop-blur-sm">
      {/* Panel */}
      <div className="w-full max-w-md bg-surface rounded-lg border border-border p-6 shadow-lg">
        <h2 className="text-heading-sm font-display font-bold text-cream mb-2">
          Connect your backend
        </h2>
        <p className="text-body-sm text-muted mb-6">
          Enter the URL where your local ReFound backend is running.
        </p>

        <label htmlFor="backend-url" className="text-label text-muted block mb-1">
          Backend URL
        </label>
        <input
          id="backend-url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="http://localhost:8000"
          className="w-full bg-canvas text-cream border border-border rounded-md px-4 py-2 mb-4 focus:outline-none focus:border-amber transition-colors"
        />

        {error && (
          <p className="text-error text-body-sm mb-4">
            ⚠️ {error}
          </p>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-muted hover:text-cream transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={isLoading}
            className="px-6 py-2 bg-amber text-canvas font-bold rounded-md hover:brightness-110 transition-all disabled:opacity-50"
          >
            {isLoading ? 'Connecting…' : 'Connect'}
          </button>
        </div>
      </div>
    </div>
  );
}