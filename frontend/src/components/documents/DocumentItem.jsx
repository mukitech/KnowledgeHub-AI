import React, { useState } from 'react';
import {
  FileText, Trash2, Calendar, Loader2, User, BookOpen,
  Layers, ChevronDown, ChevronUp, Copy, Check, ExternalLink, Hash, Tag,
} from 'lucide-react';
import documentApi from '../../api/documentApi';

/**
 * DocumentItem — Premium research notebook card.
 * Soft borders, slight elevation, metadata hierarchy.
 * Warm graphite card with copper selection state.
 * NO colorful cards. NO gradient boxes.
 */
export const DocumentItem = ({ document, onDelete, onOpenPdf }) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [expanded,   setExpanded]   = useState(false);
  const [copied,     setCopied]     = useState(false);

  const handleDelete = async e => {
    e.stopPropagation();
    const label = document.title || document.filename;
    if (!window.confirm(`Remove "${label}" and erase all Qdrant vectors?`)) return;
    setIsDeleting(true);
    try { await onDelete(document.id); }
    catch { setIsDeleting(false); }
  };

  const handleCopy = e => {
    e.stopPropagation();
    const text = [
      `Title: ${document.title || document.filename}`,
      `Author: ${document.author || '—'}`,
      `Pages: ${document.total_pages || 1}`,
      `Chunks: ${document.total_chunks || '—'}`,
      `Summary: ${document.summary || '—'}`,
    ].join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenPdf = e => {
    e.stopPropagation();
    if (onOpenPdf) {
      onOpenPdf({ document_id: document.id, filename: document.filename || document.title, page_number: 1, score: 1 });
    } else {
      window.open(documentApi.getDocumentFileUrl(document.id), '_blank');
    }
  };

  const date = document.uploaded_at
    ? new Date(document.uploaded_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Recently';

  const hasAI      = Boolean(document.title || document.author || document.summary);
  const title      = document.title || document.filename;

  return (
    <div
      className="rounded-xl overflow-hidden surface-card surface-card-hover"
      style={{ boxShadow: '0 1px 4px rgba(0,0,0,0.35)' }}
    >
      {/* ── Collapsed Header ── */}
      <div className="p-3.5 space-y-2.5">

        {/* Row 1: Icon + Title + Actions */}
        <div className="flex items-start gap-2.5">
          {/* Document icon */}
          <div
            className="mt-0.5 p-2 rounded-lg flex-shrink-0"
            style={{ background: 'rgba(194,65,12,0.08)', border: '1px solid rgba(194,65,12,0.14)' }}
          >
            <FileText className="w-3.5 h-3.5" style={{ color: '#ea580c' }} strokeWidth={1.75} />
          </div>

          {/* Title / author */}
          <div
            className="flex-1 min-w-0 cursor-pointer"
            onClick={() => setExpanded(v => !v)}
          >
            <div className="flex items-center gap-1.5 flex-wrap">
              <h4
                className="text-xs font-semibold leading-snug truncate"
                style={{ color: '#e8e2da' }}
                title={title}
              >
                {title}
              </h4>
              {hasAI && (
                <span
                  className="text-[9px] font-mono px-1.5 py-0.5 rounded flex-shrink-0"
                  style={{ background: 'rgba(194,65,12,0.08)', color: '#fb923c', border: '1px solid rgba(194,65,12,0.16)' }}
                >
                  AI
                </span>
              )}
            </div>
            {document.author && (
              <div className="flex items-center gap-1 mt-0.5">
                <User className="w-3 h-3" style={{ color: '#56524e' }} />
                <span className="text-[11px] truncate" style={{ color: '#78716c' }}>{document.author}</span>
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div className="flex items-center space-x-0.5 flex-shrink-0">
            <button onClick={handleOpenPdf} className="btn-ghost p-1.5" title="Open PDF">
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
            <button onClick={handleDelete} disabled={isDeleting} className="btn-ghost p-1.5" title="Delete">
              {isDeleting
                ? <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#f87171' }} />
                : <Trash2 className="w-3.5 h-3.5" />
              }
            </button>
          </div>
        </div>

        {/* Row 2: Structural badges — Pages, Chunks, ID */}
        <div className="flex items-center gap-1.5 text-[10px] font-mono flex-wrap">
          {[
            { icon: BookOpen, label: `${document.total_pages || 1} pages` },
            { icon: Layers,   label: `${document.total_chunks || '?'} chunks` },
            { icon: Hash,     label: `#${document.id}` },
          ].map(({ icon: Icon, label }) => (
            <span
              key={label}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded"
              style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.06)', color: '#78716c' }}
            >
              <Icon className="w-3 h-3" strokeWidth={1.75} />
              {label}
            </span>
          ))}
          {document.language && (
            <span
              className="uppercase px-1.5 py-0.5 rounded"
              style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.05)', color: '#56524e' }}
            >
              {document.language}
            </span>
          )}
        </div>

        {/* Row 3: Summary preview */}
        {document.summary && (
          <p
            className={`text-xs leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}
            style={{ color: '#78716c' }}
          >
            {document.summary}
          </p>
        )}

        {/* Row 4: Footer actions */}
        <div
          className="flex items-center justify-between text-[11px] pt-1"
          style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}
        >
          <button
            onClick={() => setExpanded(v => !v)}
            className="flex items-center gap-1 btn-text"
          >
            <span>{expanded ? 'Collapse' : 'Topics & Keywords'}</span>
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          <div className="flex items-center gap-2.5" style={{ color: '#44403c' }}>
            <span className="text-[10px] font-mono">{date}</span>
            <button onClick={handleCopy} className="btn-text flex items-center gap-1">
              {copied
                ? <><Check className="w-3 h-3" style={{ color: '#4ade80' }} /><span style={{ color: '#4ade80' }}>Copied</span></>
                : <><Copy className="w-3 h-3" /><span>Copy</span></>
              }
            </button>
          </div>
        </div>
      </div>

      {/* ── Expanded: Topics + Keywords ── */}
      {expanded && (document.topics || document.keywords) && (
        <div
          className="px-3.5 pb-3.5 pt-2.5 space-y-2.5 animate-fade-up"
          style={{ background: '#12100d', borderTop: '1px solid rgba(255,255,255,0.05)' }}
        >
          {document.topics && (
            <div>
              <p className="text-[10px] font-mono font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1.5" style={{ color: '#44403c' }}>
                <Tag className="w-3 h-3" style={{ color: '#ea580c' }} />
                Topics
              </p>
              <div className="flex flex-wrap gap-1">
                {document.topics.split(',').map(t => t.trim()).filter(Boolean).map(t => (
                  <span
                    key={t}
                    className="text-[10px] font-medium px-2 py-0.5 rounded"
                    style={{ background: 'rgba(194,65,12,0.07)', border: '1px solid rgba(194,65,12,0.14)', color: '#fdba74' }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {document.keywords && (
            <div>
              <p className="text-[10px] font-mono font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1.5" style={{ color: '#44403c' }}>
                <Hash className="w-3 h-3" style={{ color: '#56524e' }} />
                Concepts
              </p>
              <div className="flex flex-wrap gap-1">
                {document.keywords.split(',').map(k => k.trim()).filter(Boolean).map(k => (
                  <span
                    key={k}
                    className="text-[10px] font-mono px-2 py-0.5 rounded"
                    style={{ background: '#171410', border: '1px solid rgba(255,255,255,0.06)', color: '#6e6055' }}
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentItem;
