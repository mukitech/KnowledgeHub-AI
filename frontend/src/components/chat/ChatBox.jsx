import React, { useState } from 'react';
import { MessageSquare, Trash2, Download } from 'lucide-react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import PdfViewerModal from './PdfViewerModal';

/**
 * ChatBox — AI Chat Workspace (70% desktop width).
 * Warm graphite surface. Minimal workspace header. Clean session controls.
 */
export const ChatBox = ({ messages, isThinking, onSend, onClear }) => {
  const [activeCitation, setActiveCitation] = useState(null);
  const [initialQuery,   setInitialQuery]   = useState('');

  const handleExport = () => {
    if (!messages?.length) return;
    const text = messages.map(m => `[${m.role.toUpperCase()}]\n${m.content}`).join('\n\n---\n\n');
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([text], { type: 'text/plain' })),
      download: `KnowledgeHub_${new Date().toISOString().slice(0, 10)}.txt`,
    });
    a.click();
  };

  return (
    <div
      className="flex-1 min-w-0 h-full flex flex-col overflow-hidden"
      style={{ background: '#0f0d0a' }}
    >
      {/* Workspace header */}
      <div
        className="h-12 px-6 flex items-center justify-between flex-shrink-0 select-none"
        style={{ background: '#0c0a07', borderBottom: '1px solid rgba(255,255,255,0.05)' }}
      >
        <div className="flex items-center space-x-2.5">
          <MessageSquare className="w-4 h-4" style={{ color: '#44403c' }} strokeWidth={1.75} />
          <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#56524e' }}>AI Workspace</h2>
          <span
            className="hidden sm:inline text-[10px] font-mono px-1.5 py-0.5 rounded"
            style={{ background: 'rgba(194,65,12,0.06)', color: '#6e6055', border: '1px solid rgba(194,65,12,0.12)' }}
          >
            Agentic RAG Active
          </span>
        </div>

        {messages.length > 0 && (
          <div className="flex items-center space-x-1.5">
            <button onClick={handleExport} className="btn-ghost flex items-center space-x-1.5 text-xs px-3 py-1.5">
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export</span>
            </button>
            <button onClick={onClear} className="btn-ghost flex items-center space-x-1.5 text-xs px-3 py-1.5">
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          </div>
        )}
      </div>

      {/* Messages */}
      <MessageList
        messages={messages}
        isThinking={isThinking}
        onSelectCitation={setActiveCitation}
        onSelectPrompt={setInitialQuery}
      />

      {/* Input */}
      <ChatInput
        onSend={onSend}
        isThinking={isThinking}
        onClear={onClear}
        hasMessages={messages.length > 0}
        initialQuery={initialQuery}
      />

      {/* PDF slide-over drawer */}
      {activeCitation && (
        <PdfViewerModal
          citation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      )}
    </div>
  );
};

export default ChatBox;
