interface AnswerBlockProps {
  answer: string;
  duration: number | null;
  isStreaming?: boolean;
}

export function AnswerBlock({ answer, duration, isStreaming = false }: AnswerBlockProps) {
  if (!answer) return null;

  return (
    <div className="mt-12 max-w-[680px] w-full">
      <div className="flex justify-between items-center mb-2">
        <span className="text-label font-label text-amber uppercase tracking-[0.2em]">
          Answer
        </span>
        {duration !== null && (
          <span className="text-score font-mono text-muted">
            {duration.toFixed(0)}ms
          </span>
        )}
      </div>
      <div className="text-body text-cream leading-relaxed whitespace-pre-wrap">
        {answer}
        {isStreaming && (
          <span className="inline-block w-0.5 h-5 bg-amber animate-pulse ml-0.5 align-middle" />
        )}
      </div>
    </div>
  );
}