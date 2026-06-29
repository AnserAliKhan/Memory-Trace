import { useState, useEffect } from 'react';
import { PageLayout } from '../../components/layout/PageLayout';
import { useBackend } from '../../hooks/useBackend';
import { useTheme } from '../../hooks/useTheme';
import { Toast } from '../../components/ui/Toast';

const TOP_K_KEY = 'refound_top_k';

export default function Settings() {
  const { theme, toggle } = useTheme();
  const { backendUrl, setBackendUrl, isConnected, ping } = useBackend();
  const [urlInput, setUrlInput] = useState(backendUrl);
  const [isTesting, setIsTesting] = useState(false);
  const [topK, setTopK] = useState(() => {
    const stored = localStorage.getItem(TOP_K_KEY);
    return stored ? parseInt(stored, 10) : 5;
  });
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Save top_k to localStorage when changed
  useEffect(() => {
    localStorage.setItem(TOP_K_KEY, String(topK));
  }, [topK]);

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      const success = await ping(urlInput);
      if (success) {
        setToast({ message: `Connected to ${urlInput}`, type: 'success' });
      } else {
        setToast({ message: 'Failed to connect', type: 'error' });
      }
    } catch {
      setToast({ message: 'Failed to connect', type: 'error' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveUrl = async () => {
    setBackendUrl(urlInput);
    const success = await ping(urlInput);
    if (success) {
      setToast({ message: `Connected to ${urlInput}`, type: 'success' });
    } else {
      setToast({ message: 'Could not reach backend', type: 'error' });
    }
  };

  return (
    <PageLayout>
      <div className="max-w-2xl mx-auto py-8">
        <h1 className="text-display font-display font-bold text-cream mb-8">Settings</h1>

        {/* ── Appearance ── */}
        <div className="mb-10 border-b border-border-dim pb-8">
          <h2 className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">Appearance</h2>
          <div className="flex gap-3">
            <button
              onClick={toggle}
              className={`px-6 py-2 rounded-md border transition-colors ${
                theme === 'dark'
                  ? 'bg-amber text-canvas border-amber'
                  : 'bg-raised text-muted border-border hover:text-cream hover:border-amber'
              }`}
            >
              Dark
            </button>
            <button
              onClick={toggle}
              className={`px-6 py-2 rounded-md border transition-colors ${
                theme === 'light'
                  ? 'bg-amber text-canvas border-amber'
                  : 'bg-raised text-muted border-border hover:text-cream hover:border-amber'
              }`}
            >
              Light
            </button>
            <button
              onClick={() => {
                // Reset to system preference
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (prefersDark && theme !== 'dark') toggle();
                if (!prefersDark && theme !== 'light') toggle();
              }}
              className="px-6 py-2 rounded-md border border-border text-muted hover:text-cream hover:border-amber transition-colors"
            >
              System
            </button>
          </div>
        </div>

        {/* ── Backend ── */}
        <div className="mb-10 border-b border-border-dim pb-8">
          <h2 className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">Backend</h2>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-body-sm text-muted">Status:</span>
            <span className={`text-body-sm font-medium ${isConnected ? 'text-success' : 'text-error'}`}>
              {isConnected ? '● Connected' : '○ Offline'}
            </span>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="http://localhost:8000"
              className="flex-1 bg-canvas text-cream border border-border rounded-md px-4 py-2 focus:outline-none focus:border-amber transition-colors"
            />
            <button
              onClick={handleTestConnection}
              disabled={isTesting}
              className="px-6 py-2 border border-border text-muted hover:text-cream hover:border-amber rounded-md transition-colors disabled:opacity-50"
            >
              {isTesting ? 'Testing…' : 'Test'}
            </button>
            <button
              onClick={handleSaveUrl}
              className="px-6 py-2 bg-amber text-canvas font-bold rounded-md hover:brightness-110 transition-colors"
            >
              Connect
            </button>
          </div>
        </div>

        {/* ── Search ── */}
        <div className="mb-10 border-b border-border-dim pb-8">
          <h2 className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">Search</h2>
          <div className="flex items-center gap-6">
            <label htmlFor="top_k" className="text-body-sm text-cream">
              Results per query: <span className="text-amber font-bold">{topK}</span>
            </label>
            <input
              id="top_k"
              type="range"
              min={1}
              max={10}
              step={1}
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              className="flex-1 max-w-xs appearance-none bg-border h-1 rounded-full outline-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-amber"
            />
          </div>
        </div>

        {/* ── About ── */}
        <div>
          <h2 className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">About</h2>
          <p className="text-body text-muted mb-2">ReFound — v0.1.0</p>
          <p className="text-body text-muted mb-4">
            This runs entirely on your machine. No cloud, no tracking, no telemetry.
          </p>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-body-sm text-amber hover:text-cream transition-colors"
          >
            View on GitHub →
          </a>
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