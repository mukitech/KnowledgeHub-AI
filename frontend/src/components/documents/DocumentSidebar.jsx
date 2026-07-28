import React, { useState, useMemo } from 'react';
import { Database, Search, FolderOpen, RefreshCw, AlertCircle, X } from 'lucide-react';
import PdfUploader from './PdfUploader';
import DocumentItem from './DocumentItem';
import StatsBar from './StatsBar';

/**
 * DocumentSidebar — Knowledge Explorer (30% desktop width).
 * Calm warm-graphite sidebar. Single-panel layout: stats → upload → search → list.
 */
export const DocumentSidebar = ({
  documents = [], stats = null, isLoading, vectorCount,
  onUpload, isUploading, uploadProgress, onDelete, onRefresh, onOpenPdf, error,
}) => {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    if (!query.trim()) return documents;
    const q = query.toLowerCase();
    return documents.filter(d =>
      [d.title, d.filename, d.author, d.topics, d.keywords, d.summary, d.language]
        .some(v => v?.toLowerCase().includes(q))
    );
  }, [documents, query]);

  return (
    <aside
      className="w-full h-full flex flex-col flex-shrink-0 overflow-hidden"
      style={{ background: '#0e0c09', borderRight: '1px solid rgba(255,255,255,0.05)' }}
    >
      {/* Header */}
      <div
        className="h-12 px-4 flex items-center justify-between flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: '#0c0a07' }}
      >
        <div className="flex items-center space-x-2.5">
          <div
            className="p-1.5 rounded-lg"
            style={{ background: 'rgba(194,65,12,0.08)', border: '1px solid rgba(194,65,12,0.14)' }}
          >
            <Database className="w-3.5 h-3.5" style={{ color: '#ea580c' }} strokeWidth={1.75} />
          </div>
          <div>
            <h2 className="text-xs font-semibold" style={{ color: '#d6d3d1' }}>Knowledge Explorer</h2>
            <p className="text-[10px] font-mono" style={{ color: '#44403c' }}>PDF Ingestion · Qdrant Index</p>
          </div>
        </div>
        <button onClick={onRefresh} className="btn-ghost p-1.5" title="Refresh">
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} style={isLoading ? { color: '#ea580c' } : {}} />
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div
          className="px-4 py-2 text-xs flex items-center space-x-2 flex-shrink-0"
          style={{ background: 'rgba(239,68,68,0.06)', borderBottom: '1px solid rgba(239,68,68,0.12)', color: '#fca5a5' }}
        >
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#f87171' }} />
          <span className="truncate">{error}</span>
        </div>
      )}

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {/* Stats */}
        <StatsBar stats={stats} />

        {/* Upload */}
        <div className="p-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <p className="text-[10px] font-mono font-semibold uppercase tracking-widest mb-2.5" style={{ color: '#44403c' }}>
            Ingest Document
          </p>
          <PdfUploader
            onUpload={onUpload}
            isUploading={isUploading}
            progress={uploadProgress}
            existingDocuments={documents}
          />
        </div>

        {/* Search + list */}
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-mono font-semibold uppercase tracking-widest" style={{ color: '#44403c' }}>
              Indexed Documents ({filtered.length})
            </p>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search
              className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: '#44403c' }}
            />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search title, author, topic…"
              className="w-full pl-8 pr-8 py-2 rounded-xl text-xs outline-none surface-input"
              style={{ color: '#d6d3d1' }}
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 btn-text"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Document list */}
          <div className="space-y-2.5">
            {filtered.length === 0 ? (
              <div
                className="py-10 rounded-xl text-center flex flex-col items-center space-y-2"
                style={{ background: '#12100d', border: '1px dashed rgba(255,255,255,0.06)' }}
              >
                <FolderOpen className="w-7 h-7" style={{ color: '#2a2420' }} strokeWidth={1.5} />
                <div className="space-y-0.5">
                  <p className="text-xs font-medium" style={{ color: '#44403c' }}>
                    {query ? 'No matches found' : 'No indexed PDFs yet'}
                  </p>
                  <p className="text-[11px]" style={{ color: '#292520' }}>
                    {query ? `Try clearing the search.` : 'Upload a PDF above to start.'}
                  </p>
                </div>
              </div>
            ) : (
              filtered.map(doc => (
                <DocumentItem
                  key={doc.id}
                  document={doc}
                  onDelete={onDelete}
                  onOpenPdf={onOpenPdf}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};

export default DocumentSidebar;
