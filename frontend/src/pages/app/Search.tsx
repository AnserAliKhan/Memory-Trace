import { useState, useEffect } from 'react';
import { PageLayout } from '../../components/layout/PageLayout';
import { SearchInput } from '../../components/ui/SearchInput';
import { AnswerBlock } from '../../components/ui/AnswerBlock';
import { SourceCard } from '../../components/ui/SourceCard';
import { useBackend } from '../../hooks/useBackend';
import { useQueryState } from '../../hooks/useQueryState';
import { listDocuments, queryMemoryStreaming } from '../../services/api';
import { SplitText } from '../../components/ui/SplitText';
import { motion } from 'motion/react';

export default function Search() {
  const { backendUrl } = useBackend();
  const [docCount, setDocCount] = useState<number | null>(null);
  const [chunkCount, setChunkCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { state, setState, answer, setAnswer, sources, setSources, duration, setDuration, reset } =
    useQueryState();

  // Fetch document stats on mount
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const docs = await listDocuments(backendUrl);
        setDocCount(docs.length);
        const totalChunks = docs.reduce((sum, d) => sum + d.chunk_count, 0);
        setChunkCount(totalChunks);
      } catch {
        // Silently fail
      }
    };
    fetchStats();
  }, [backendUrl]);

  const handleSearch = async (query: string) => {
    // Reset previous state
    reset();
    setError(null);
    setState('loading');

    try {
      const stream = await queryMemoryStreaming(backendUrl, query, 5);
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      setState('streaming');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Split by newlines to process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          try {
            const data = JSON.parse(trimmed);

            if (data.token) {
              // Append token to answer
              setAnswer((prev) => prev + data.token);
            }

            if (data.sources) {
              // Final message with sources and duration
              setSources(data.sources);
              setDuration(data.duration_ms || 0);
              setState('done');
            }

            if (data.error) {
              setError(data.error);
              setState('done');
            }
          } catch (parseErr) {
            // If it's not JSON, treat as raw text token (fallback)
            setAnswer((prev) => prev + trimmed);
          }
        }
      }

      // If stream ended without a sources message, check if we have any answer
      if (state !== 'done' && answer) {
        setState('done');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
      setState('done');
    }
  };

  const isStreaming = state === 'loading' || state === 'streaming';

  return (
    <PageLayout>
      <div className="relative min-h-[calc(100vh-6rem)] flex flex-col items-center pt-16">
        {/* Stat row */}
        <div className="text-label text-dim font-label uppercase tracking-[0.2em] mb-6">
          {docCount !== null && chunkCount !== null
            ? `${docCount} documents · ${chunkCount} chunks`
            : 'Loading...'}
        </div>

        {/* Headline */}
        <h1 className="text-display font-display font-bold text-cream mb-8 text-center">
          <SplitText text="Ask anything." />
        </h1>

        {/* Search input */}
        <SearchInput
          onSearch={handleSearch}
          isLoading={isStreaming}
          placeholder="What did I write about..."
        />

        {/* Error message */}
        {error && (
          <div className="mt-4 text-error text-body-sm">{error}</div>
        )}

        {/* Empty state suggestions (show only when idle and no answer) */}
        {state === 'idle' && !answer && (
          <div className="mt-8 flex flex-col sm:flex-row gap-3 max-w-[600px] w-full">
            <button
              onClick={() => handleSearch('What did I write about AI?')}
              className="px-4 py-3 bg-raised border border-border rounded-md text-body-sm text-muted hover:text-cream hover:border-amber transition-colors text-left"
            >
              "What did I write about AI?"
            </button>
            <button
              onClick={() => handleSearch('Summarize my notes on machine learning')}
              className="px-4 py-3 bg-raised border border-border rounded-md text-body-sm text-muted hover:text-cream hover:border-amber transition-colors text-left"
            >
              "Summarize my notes on machine learning"
            </button>
            <button
              onClick={() => handleSearch('Find where I mentioned Docker')}
              className="px-4 py-3 bg-raised border border-border rounded-md text-body-sm text-muted hover:text-cream hover:border-amber transition-colors text-left"
            >
              "Find where I mentioned Docker"
            </button>
          </div>
        )}

        {/* Answer block */}
        {answer && (
          <AnswerBlock
            answer={answer}
            duration={duration}
            isStreaming={state === 'streaming'}
          />
        )}

        {/* Sources grid with stagger */}
{sources.length > 0 && (
  <motion.div
    className="mt-8 max-w-[680px] w-full"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ delay: 0.2 }}
  >
    <div className="grid grid-cols-1 gap-3">
      {sources.map((source, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.4,
            delay: 0.2 + idx * 0.08,
            ease: [0.0, 0.0, 0.2, 1.0],
          }}
        >
          <SourceCard source={source} />
        </motion.div>
      ))}
    </div>
  </motion.div>
)}
      </div>
    </PageLayout>
  );
}