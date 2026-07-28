import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2, BookOpen } from 'lucide-react';

/**
 * ChatInput — Floating warm-charcoal prompt bar.
 * Copper solid send button. Ghost clear button. Clean kbd hints.
 */
export const ChatInput = ({ onSend, isThinking, onClear, hasMessages, initialQuery = '' }) => {
  const [input, setInput] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    if (!initialQuery) return;
    setInput(initialQuery);
    if (ref.current) {
      ref.current.style.height = 'auto';
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 180)}px`;
      ref.current.focus();
    }
  }, [initialQuery]);

  const submit = () => {
    const t = input.trim();
    if (!t || isThinking) return;
    onSend(t);
    setInput('');
    if (ref.current) ref.current.style.height = 'auto';
  };

  const onKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  const onInput = e => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  return (
    <div
      className="px-6 py-4 flex-shrink-0"
      style={{ background: '#0e0c09', borderTop: '1px solid rgba(255,255,255,0.05)' }}
    >
      <div className="max-w-3xl mx-auto space-y-2">
        {/* Input container */}
        <div
          className="flex items-end space-x-3 px-4 py-3 rounded-2xl surface-input"
        >
          <textarea
            ref={ref}
            value={input}
            onChange={onInput}
            onKeyDown={onKey}
            placeholder="Ask anything about your knowledge base…"
            rows={1}
            disabled={isThinking}
            className="flex-1 resize-none bg-transparent text-sm outline-none leading-7 max-h-44"
            style={{ color: '#d6d3d1', caretColor: '#ea580c' }}
          />

          <div className="flex items-center space-x-2 pb-0.5">
            {hasMessages && (
              <button onClick={onClear} className="btn-ghost p-2" title="Clear session">
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={submit}
              disabled={!input.trim() || isThinking}
              className="btn-primary p-2.5"
            >
              {isThinking
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Send className="w-4 h-4" />
              }
            </button>
          </div>
        </div>

        {/* Hints */}
        <div
          className="flex items-center justify-between px-1 text-[10px] font-mono"
          style={{ color: '#3c342c' }}
        >
          <div className="flex items-center space-x-2">
            <span>
              <kbd className="px-1.5 py-0.5 rounded text-[9px]" style={{ background: '#171410', border: '1px solid rgba(255,255,255,0.07)', color: '#56524e' }}>Enter</kbd>
              {' '}to send
            </span>
            <span>·</span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded text-[9px]" style={{ background: '#171410', border: '1px solid rgba(255,255,255,0.07)', color: '#56524e' }}>Shift+Enter</kbd>
              {' '}for new line
            </span>
          </div>
          <span className="hidden sm:inline" style={{ color: '#2a2420' }}>Hybrid Search · Qdrant + BM25</span>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
