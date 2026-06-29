import { useState, useCallback } from 'react';

export type QueryState = 'idle' | 'loading' | 'streaming' | 'done';

export function useQueryState() {
  const [state, setState] = useState<QueryState>('idle');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<any[]>([]);
  const [duration, setDuration] = useState<number | null>(null);

  const reset = useCallback(() => {
    setState('idle');
    setAnswer('');
    setSources([]);
    setDuration(null);
  }, []);

  return {
    state,
    setState,
    answer,
    setAnswer,
    sources,
    setSources,
    duration,
    setDuration,
    reset,
  };
}