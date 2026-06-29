import { useState } from 'react';
import type { Document } from '../../services/api';

interface DocumentRowProps {
  doc: Document;
  onDelete: (id: number) => void;
  isDeleting?: boolean;
}

export function DocumentRow({ doc, onDelete, isDeleting = false }: DocumentRowProps) {
  const [isHovered, setIsHovered] = useState(false);

  const formattedDate = new Date(doc.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  return (
    <div
      className="flex items-center justify-between py-3 border-b border-border-dim hover:bg-raised/30 px-2 -mx-2 rounded transition-colors"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex-1 min-w-0">
        <p className="text-body text-cream truncate">{doc.filename}</p>
        <div className="flex flex-wrap items-center gap-3 text-body-sm text-muted">
          <span>{doc.chunk_count} chunks</span>
          <span>·</span>
          <span className="uppercase text-label text-[10px]">{doc.source_type}</span>
          <span>·</span>
          <span>{formattedDate}</span>
          {doc.status === 'indexed' && (
            <span className="text-success text-label text-[10px] uppercase font-medium">
              ✓ Indexed
            </span>
          )}
        </div>
      </div>
      {isHovered && !isDeleting && (
        <button
          onClick={() => onDelete(doc.id)}
          className="text-muted hover:text-error transition-colors px-3 py-1 text-sm"
          aria-label="Delete document"
        >
          ✕
        </button>
      )}
    </div>
  );
}