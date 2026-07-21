import { useRef, useState } from 'react';

interface ImportDropZoneProps {
  onUpload: (file: File) => void;
  isUploading?: boolean;
}

export function ImportDropZone({ onUpload, isUploading = false }: ImportDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onUpload(files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onUpload(files[0]);
    }
    e.target.value = ''; // Reset so the same file can be re-uploaded
  };

  const borderStyle = isDragOver
    ? 'border-amber border-2 border-dashed'
    : 'border-border border-2 border-dashed';

  return (
    <div
      className={`w-full max-w-[480px] mx-auto p-12 bg-surface/50 ${borderStyle} rounded-lg cursor-pointer text-center transition-colors ${isDragOver ? 'bg-amber-glow' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".md,.txt,.pdf,.json"
        onChange={handleFileChange}
        className="hidden"
      />
      <div className="text-4xl text-muted mb-3">📄</div>
      <p className="text-body text-cream">
        {isUploading ? 'Uploading...' : 'Drop your file here, or click to browse'}
      </p>
      <p className="text-body-sm text-muted mt-2">
        .md .txt .pdf .json (ChatGPT/Claude export)
      </p>
    </div>
  );
}