import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, FileText, Cpu, Database, Layers, Check } from 'lucide-react';

/**
 * PdfUploader — Drag-and-drop upload zone.
 * Paper-like surface. Copper accent progress. No neon glow.
 * Multi-stage indexing progress with calm step indicators.
 */
export const PdfUploader = ({ onUpload, isUploading, progress, existingDocuments = [] }) => {
  const [isDragOver,    setIsDragOver]    = useState(false);
  const [errorMessage,  setErrorMessage]  = useState('');
  const [successMessage,setSuccessMessage]= useState('');
  const [activeStage,   setActiveStage]   = useState(0);
  const fileInputRef = useRef(null);

  const STAGES = [
    'Uploading PDF',
    'Extracting Text',
    'Creating Chunks',
    'Generating Embeddings',
    'Building Vector Index',
  ];

  useEffect(() => {
    if (!isUploading) { setActiveStage(0); return; }
    setActiveStage(1);
    const t1 = setTimeout(() => setActiveStage(2), 900);
    const t2 = setTimeout(() => setActiveStage(3), 2100);
    const t3 = setTimeout(() => setActiveStage(4), 3400);
    const t4 = setTimeout(() => setActiveStage(5), 5000);
    return () => [t1,t2,t3,t4].forEach(clearTimeout);
  }, [isUploading]);

  useEffect(() => {
    if (!successMessage) return;
    const t = setTimeout(() => setSuccessMessage(''), 5000);
    return () => clearTimeout(t);
  }, [successMessage]);

  const handleFile = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMessage('Only PDF documents (.pdf) are accepted.');
      setSuccessMessage('');
      return;
    }
    const isDuplicate = existingDocuments.some(
      d => (d.filename || d.original_filename || '').toLowerCase() === file.name.toLowerCase()
    );
    if (isDuplicate) {
      setErrorMessage(`"${file.name}" is already indexed.`);
      setSuccessMessage('');
      return;
    }
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const result = await onUpload(file);
      setSuccessMessage(`Indexed "${file.name}" — ${result?.chunks_stored ?? '?'} chunks stored.`);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setErrorMessage(err.message || 'Failed to index PDF.');
    }
  };

  const handleDrop = e => {
    e.preventDefault();
    setIsDragOver(false);
    if (!isUploading && e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  };

  const pct = progress || Math.min(activeStage * 20, 95);

  return (
    <div className="w-full space-y-2.5">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); if (!isUploading) setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className="relative cursor-pointer p-5 rounded-xl text-center transition-all duration-200"
        style={{
          background: isDragOver ? 'rgba(194,65,12,0.06)' : '#171410',
          border: `2px dashed ${isDragOver ? 'rgba(234,88,12,0.60)' : isUploading ? 'rgba(234,88,12,0.30)' : 'rgba(255,255,255,0.09)'}`,
          transform: isDragOver ? 'scale(0.99)' : 'scale(1)',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          disabled={isUploading}
          className="hidden"
          onChange={e => e.target.files && handleFile(e.target.files[0])}
        />

        <div className="flex flex-col items-center space-y-2.5">
          {/* Icon */}
          <div
            className="p-3 rounded-xl"
            style={{
              background: isUploading
                ? 'rgba(194,65,12,0.10)'
                : successMessage
                ? 'rgba(34,197,94,0.08)'
                : 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            {isUploading
              ? <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#ea580c' }} />
              : successMessage
              ? <CheckCircle2 className="w-6 h-6" style={{ color: '#4ade80' }} />
              : <UploadCloud className="w-6 h-6" style={{ color: '#6e6055' }} />
            }
          </div>

          <div>
            <p className="text-sm font-semibold" style={{ color: '#d6d3d1' }}>
              {isUploading ? 'Processing document…' : successMessage ? 'Document indexed' : 'Drop PDF or click to upload'}
            </p>
            <p className="text-xs mt-0.5" style={{ color: '#56524e' }}>
              {isUploading
                ? 'Extracting text, chunking & generating 384-D vectors'
                : 'PDF only · Metadata extracted automatically'}
            </p>
          </div>
        </div>

        {/* Progress */}
        {isUploading && (
          <div className="mt-4 pt-3.5 space-y-2.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-center justify-between text-xs font-mono" style={{ color: '#a8a29e' }}>
              <span>{STAGES[Math.min(activeStage - 1, 4)] ?? 'Starting…'}</span>
              <span style={{ color: '#ea580c' }}>{pct}%</span>
            </div>
            <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.max(pct, 8)}%`, background: '#c2410c' }}
              />
            </div>
            {/* Step chips */}
            <div className="grid grid-cols-5 gap-1">
              {STAGES.map((s, i) => {
                const n = i + 1;
                const done = activeStage > n;
                const cur  = activeStage === n;
                return (
                  <div
                    key={s}
                    title={s}
                    className="flex items-center justify-center py-1 rounded text-[9px] font-mono"
                    style={{
                      background: done ? 'rgba(34,197,94,0.08)' : cur ? 'rgba(194,65,12,0.12)' : 'rgba(255,255,255,0.03)',
                      border: `1px solid ${done ? 'rgba(74,222,128,0.15)' : cur ? 'rgba(194,65,12,0.30)' : 'rgba(255,255,255,0.05)'}`,
                      color: done ? '#4ade80' : cur ? '#ea580c' : '#44403c',
                    }}
                  >
                    {done ? <Check className="w-3 h-3" /> : n}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {successMessage && (
        <div
          className="flex items-center space-x-2 px-3 py-2.5 rounded-xl text-xs animate-fade-up"
          style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(74,222,128,0.12)', color: '#86efac' }}
        >
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" style={{ color: '#4ade80' }} />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div
          className="flex items-center space-x-2 px-3 py-2.5 rounded-xl text-xs animate-fade-up"
          style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.14)', color: '#fca5a5' }}
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" style={{ color: '#f87171' }} />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};

export default PdfUploader;
