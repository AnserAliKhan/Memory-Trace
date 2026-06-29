import { useState, useRef } from 'react';

interface SearchInputProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export function SearchInput({
  onSearch,
  isLoading = false,
  placeholder = 'Ask anything...',
}: SearchInputProps) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed && !isLoading) {
      onSearch(trimmed);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative max-w-[600px] w-full">
      <div className="relative">
        {/* Glow effect - will be activated when processing */}
        <div
          className={`absolute -inset-4 pointer-events-none transition-opacity duration-500 ${isLoading ? 'search-glow-active' : 'opacity-0'
            }`}
          style={{
            background: 'radial-gradient(circle, var(--color-amber-glow) 0%, transparent 70%)',
          }}
        />

        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          disabled={isLoading}
          className="w-full bg-surface border border-border focus:border-amber rounded-md px-5 py-4 pr-24 text-body text-cream placeholder-dim outline-none transition-colors disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-amber text-canvas font-bold rounded-sm text-label disabled:opacity-40 transition-all hover:brightness-110"
        >
          {isLoading ? (
            <span className="tracking-widest">···</span>
          ) : (
            'Search ↵'
          )}
        </button>
      </div>
    </form>
  );
}