import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, ExternalLink, Layers, Hash } from 'lucide-react';

/**
 * CitationList — Grounded passage source cards.
 * Warm graphite surface. Copper relevance badge. Paper-like card aesthetic.
 */
export const CitationList = ({ sources = [], onSelectCitation }) => {
  const [open, setOpen] = useState(true);
  if (!sources?.length) return null;

  return (
    <div className="mt-3.5 pt-3.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
      {/* Section toggle */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center space-x-2 text-xs font-semibold mb-2.5 transition-opacity hover:opacity-80"
        style={{ color: '#78716c' }}
      >
        <span>Grounded Sources ({sources.length})</span>
        {open ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {open && (
        <div className="space-y-2 animate-fade-up">
          {sources.map((src, idx) => {
            const raw      = src.score ?? src.similarity_score ?? 0;
            const pct      = Math.round(raw * 100);
            const name     = src.filename || (src.document_id ? `Document #${src.document_id}` : `Source ${idx + 1}`);
            const page     = src.page_number || 1;
            const chunk    = src.chunk_index ?? idx;
            const snippet  = (src.snippet || src.chunk_text || '').slice(0, 220);
            const snip     = snippet.length === 220 ? snippet + '…' : snippet;

            return (
              <div
                key={`${src.document_id ?? idx}-${chunk}-${idx}`}
                className="rounded-xl p-3.5 space-y-2.5 surface-card surface-card-hover"
              >
                {/* Source header */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <FileText className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#ea580c' }} strokeWidth={1.75} />
                    <span className="text-xs font-semibold truncate" style={{ color: '#d6d3d1' }} title={name}>{name}</span>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <span
                      className="text-[10px] font-mono font-bold px-2 py-0.5 rounded"
                      style={{ background: 'rgba(194,65,12,0.10)', color: '#fb923c', border: '1px solid rgba(194,65,12,0.18)' }}
                    >
                      {pct}% match
                    </span>
                    {src.document_id && (
                      <button
                        onClick={() => onSelectCitation?.(src)}
                        className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-1 rounded-lg btn-primary"
                      >
                        <span>View PDF</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Badges */}
                <div className="flex items-center gap-1.5 text-[10px] font-mono">
                  {[
                    { icon: Layers, label: `Page ${page}` },
                    { icon: Hash,   label: `Chunk #${chunk}` },
                  ].map(({ icon: Icon, label }) => (
                    <span
                      key={label}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded"
                      style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.05)', color: '#6e6055' }}
                    >
                      <Icon className="w-3 h-3" strokeWidth={1.75} />
                      {label}
                    </span>
                  ))}
                </div>

                {/* Snippet excerpt */}
                {snip && (
                  <blockquote
                    className="text-[11px] leading-relaxed px-3 py-2 rounded-lg font-serif italic"
                    style={{
                      background: '#12100d',
                      borderLeft: '2px solid rgba(194,65,12,0.40)',
                      color: '#78716c',
                    }}
                  >
                    "{snip}"
                  </blockquote>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CitationList;
