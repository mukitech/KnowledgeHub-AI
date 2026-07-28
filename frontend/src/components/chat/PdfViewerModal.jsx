import React, { useState } from 'react';
import { X, FileText, ExternalLink, BookOpen, Layers, Hash } from 'lucide-react';
import documentApi from '../../api/documentApi';

/**
 * PdfViewerModal — Right slide-over drawer.
 * Deep graphite drawer. Copper passage highlight. Clean framing.
 */
export const PdfViewerModal = ({ citation, onClose }) => {
  if (!citation?.document_id) return null;

  const url        = documentApi.getDocumentFileUrl(citation.document_id);
  const page       = citation.page_number || 1;
  const pageUrl    = `${url}#page=${page}`;
  const raw        = citation.score || citation.similarity_score || 0;
  const pct        = Math.round(raw * 100);
  const name       = citation.filename || `Document #${citation.document_id}`;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end animate-fade-in"
      style={{ background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)' }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Drawer */}
      <div
        className="relative w-full max-w-3xl h-full flex flex-col z-10 animate-slide-left shadow-lift-lg"
        style={{ background: '#0e0c09', borderLeft: '1px solid rgba(255,255,255,0.07)' }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 flex-shrink-0"
          style={{ background: '#0c0a07', borderBottom: '1px solid rgba(255,255,255,0.06)' }}
        >
          <div className="flex items-center space-x-3 min-w-0">
            <div
              className="p-2 rounded-lg flex-shrink-0"
              style={{ background: 'rgba(194,65,12,0.08)', border: '1px solid rgba(194,65,12,0.16)' }}
            >
              <FileText className="w-4 h-4" style={{ color: '#ea580c' }} strokeWidth={1.75} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-semibold truncate" style={{ color: '#e8e2da' }}>{name}</h3>
                <span
                  className="text-[10px] font-mono px-2 py-0.5 rounded flex-shrink-0"
                  style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.07)', color: '#6e6055' }}
                >
                  Page {page}
                </span>
              </div>
              <p className="text-xs font-mono mt-0.5" style={{ color: '#44403c' }}>
                Match: <span style={{ color: '#fb923c' }}>{pct}%</span>
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 flex-shrink-0">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost flex items-center space-x-1.5 text-xs px-3 py-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Open tab</span>
            </a>
            <button onClick={onClose} className="btn-ghost p-2">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Passage banner */}
        {citation.snippet && (
          <div
            className="px-6 py-3.5 flex items-start space-x-3 flex-shrink-0"
            style={{ background: 'rgba(194,65,12,0.06)', borderBottom: '1px solid rgba(194,65,12,0.12)' }}
          >
            <div
              className="p-1.5 rounded flex-shrink-0 mt-0.5"
              style={{ background: 'rgba(194,65,12,0.10)', border: '1px solid rgba(194,65,12,0.16)' }}
            >
              <BookOpen className="w-3.5 h-3.5" style={{ color: '#ea580c' }} strokeWidth={1.75} />
            </div>
            <div className="flex-1 text-xs space-y-1.5">
              <div className="flex items-center justify-between font-mono" style={{ color: '#6e6055' }}>
                <span className="font-semibold" style={{ color: '#fb923c' }}>Grounding Passage</span>
                <div className="flex items-center gap-1.5">
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.05)', color: '#56524e' }}>
                    <Layers className="w-3 h-3" strokeWidth={1.75} /> Page {page}
                  </span>
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.05)', color: '#56524e' }}>
                    <Hash className="w-3 h-3" strokeWidth={1.75} /> Chunk #{citation.chunk_index ?? 0}
                  </span>
                </div>
              </div>
              <blockquote
                className="text-xs font-serif italic leading-relaxed px-3 py-2 rounded-lg"
                style={{ background: '#12100d', borderLeft: '2px solid rgba(194,65,12,0.40)', color: '#78716c' }}
              >
                "{citation.snippet}"
              </blockquote>
            </div>
          </div>
        )}

        {/* PDF iframe */}
        <div className="flex-1 overflow-hidden" style={{ background: '#0c0a07' }}>
          <iframe
            src={pageUrl}
            title={`PDF ${citation.document_id}`}
            className="w-full h-full border-0"
          />
        </div>

        {/* Footer */}
        <div
          className="px-6 py-2.5 flex items-center justify-between text-[10px] font-mono flex-shrink-0"
          style={{ background: '#0c0a07', borderTop: '1px solid rgba(255,255,255,0.05)', color: '#2a2420' }}
        >
          <span>Targeting page {page} · Grounded vector search</span>
          <span>KnowledgeHub AI</span>
        </div>
      </div>
    </div>
  );
};

export default PdfViewerModal;
