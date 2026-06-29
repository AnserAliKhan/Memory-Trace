import { useState, useEffect } from 'react';
import { PageLayout } from '../../components/layout/PageLayout';
import { useBackend } from '../../hooks/useBackend';
import { getHistory, type QueryHistoryItem } from '../../services/api';
import { motion, AnimatePresence } from 'motion/react';

export default function History() {
  const { backendUrl } = useBackend();
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setIsLoading(true);
        const data = await getHistory(backendUrl);
        setHistory(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, [backendUrl]);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <PageLayout>
      <div className="max-w-3xl mx-auto py-8">
        {/* Page header */}
        <h1 className="text-display font-display font-bold text-cream mb-2">History</h1>
        <p className="text-body text-muted mb-8">
          {history.length} {history.length === 1 ? 'query' : 'queries'}
        </p>

        {/* Loading state */}
        {isLoading && (
          <div className="text-center py-12 text-muted text-body-sm">
            Loading history...
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="text-center py-12 text-error text-body-sm">
            {error}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && history.length === 0 && (
          <div className="text-center py-12 text-muted text-body-sm">
            No queries yet. Start searching.
          </div>
        )}

        {/* History list */}
        {!isLoading && !error && history.length > 0 && (
          <div className="space-y-2">
            {history.map((item) => {
              const isExpanded = expandedId === item.id;
              // Truncate answer to 120 chars for excerpt
              const excerpt =
                item.answer.length > 120
                  ? item.answer.slice(0, 120) + '…'
                  : item.answer;

              // Parse sources if they're stored as JSON string
              let sources: any[] = [];
              try {
                sources = typeof item.sources === 'string' 
                  ? JSON.parse(item.sources) 
                  : item.sources || [];
              } catch {
                sources = [];
              }

              return (
                <div
                  key={item.id}
                  className="bg-surface border border-border rounded-md overflow-hidden transition-colors"
                >
                  {/* Query row - always visible */}
                  <button
                    onClick={() => toggleExpand(item.id)}
                    className="w-full text-left px-4 py-3 hover:bg-raised/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-body text-cream truncate">{item.query}</p>
                        <div className="flex flex-wrap items-center gap-3 text-body-sm text-muted mt-1">
                          <span className="text-mono text-score">{item.duration_ms.toFixed(0)}ms</span>
                          <span>·</span>
                          <span>{formatDate(item.created_at)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-body-sm text-muted line-clamp-1 max-w-[200px] hidden sm:block">
                          {excerpt}
                        </span>
                        <span className="text-muted text-sm">
                          {isExpanded ? '▾' : '▸'}
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Expanded content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: [0.0, 0.0, 0.2, 1.0] }}
                        className="overflow-hidden"
                      >
                        <div className="px-4 pb-4 pt-1 border-t border-border-dim">
                          <div className="text-body text-cream whitespace-pre-wrap mb-3">
                            {item.answer}
                          </div>

                          {/* Sources */}
                          {sources.length > 0 && (
                            <div>
                              <p className="text-label font-label text-muted uppercase tracking-[0.2em] text-[10px] mb-2">
                                Sources
                              </p>
                              <div className="space-y-1.5">
                                {sources.map((source, idx) => (
                                  <div
                                    key={idx}
                                    className="bg-raised/30 border border-border/50 rounded px-3 py-1.5"
                                  >
                                    <div className="flex items-center justify-between gap-2">
                                      <span className="text-body-sm text-cream truncate">
                                        {source.filename || source.source || 'Unknown'}
                                      </span>
                                      <span className="text-score font-mono text-amber bg-amber-dim px-2 py-0.5 rounded-sm text-[10px] shrink-0">
                                        {(source.score * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                    {source.excerpt && (
                                      <p className="text-body-sm text-muted mt-1 line-clamp-2">
                                        {source.excerpt}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageLayout>
  );
}