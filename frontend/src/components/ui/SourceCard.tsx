interface SourceCardProps {
  source: {
    source: string;
    filename: string;
    score: number;
    excerpt: string;
  };
}

export function SourceCard({ source }: SourceCardProps) {
  return (
    <div className="bg-surface border border-border rounded-md px-4 py-3 hover:border-amber hover:-translate-y-0.5 transition-all duration-200">
      <div className="flex items-center justify-between gap-3">
        <span className="text-body-sm text-cream truncate">{source.filename}</span>
        <span className="text-score font-mono text-amber bg-amber-dim px-2 py-0.5 rounded-sm shrink-0">
          {(source.score * 100).toFixed(0)}%
        </span>
      </div>
      <div className="text-body-sm text-muted mt-1 line-clamp-2">{source.excerpt}</div>
    </div>
  );
}