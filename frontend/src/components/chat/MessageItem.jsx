import React, { useState } from 'react';
import { User, BookOpen, Copy, Check, ThumbsUp, ThumbsDown, Bookmark } from 'lucide-react';
import CitationList from './CitationList';
import AgenticTimeline from './AgenticTimeline';

/**
 * MessageItem — Individual conversation message.
 * Warm graphite backgrounds. Copper assistant avatar. Clean typography hierarchy.
 */
export const MessageItem = ({ message, onSelectCitation }) => {
  const isUser = message.role === 'user';
  const [copied,     setCopied]     = useState(false);
  const [feedback,   setFeedback]   = useState(null);
  const [bookmarked, setBookmarked] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="flex w-full space-x-3.5 px-5 py-4 rounded-2xl transition-all duration-150"
      style={{
        background: isUser ? '#171410' : '#1a1713',
        border: `1px solid ${isUser ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.06)'}`,
      }}
    >
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{
          background: isUser ? 'rgba(255,255,255,0.06)' : '#c2410c',
          border: `1px solid ${isUser ? 'rgba(255,255,255,0.08)' : 'rgba(194,65,12,0.50)'}`,
          boxShadow: isUser ? 'none' : '0 2px 8px rgba(194,65,12,0.20)',
        }}
      >
        {isUser
          ? <User className="w-3.5 h-3.5" style={{ color: '#a8a29e' }} strokeWidth={1.75} />
          : <BookOpen className="w-3.5 h-3.5 text-white" strokeWidth={2} />
        }
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <span className="text-xs font-semibold" style={{ color: '#d6d3d1' }}>
              {isUser ? 'You' : 'KnowledgeHub AI'}
            </span>
            {!isUser && (
              <span
                className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(194,65,12,0.08)', color: '#fb923c', border: '1px solid rgba(194,65,12,0.16)' }}
              >
                Agentic RAG
              </span>
            )}
          </div>

          {!isUser && (
            <div className="flex items-center space-x-0.5">
              <button onClick={handleCopy} className="btn-ghost p-1.5" title="Copy">
                {copied
                  ? <Check className="w-3.5 h-3.5" style={{ color: '#4ade80' }} />
                  : <Copy className="w-3.5 h-3.5" />
                }
              </button>
              <button
                onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
                className="btn-ghost p-1.5"
                style={feedback === 'up' ? { color: '#4ade80' } : {}}
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
                className="btn-ghost p-1.5"
                style={feedback === 'down' ? { color: '#f87171' } : {}}
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setBookmarked(!bookmarked)}
                className="btn-ghost p-1.5"
                style={bookmarked ? { color: '#fb923c' } : {}}
              >
                <Bookmark className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Body text */}
        <div
          className="text-sm leading-7 whitespace-pre-wrap"
          style={{ color: isUser ? '#a8a29e' : '#d6d3d1', letterSpacing: '0.005em' }}
        >
          {message.content}
        </div>

        {/* Agentic timeline + citations */}
        {!isUser && message.sources && <AgenticTimeline sources={message.sources} />}
        {!isUser && message.sources?.length > 0 && (
          <CitationList sources={message.sources} onSelectCitation={onSelectCitation} />
        )}
      </div>
    </div>
  );
};

export default MessageItem;
