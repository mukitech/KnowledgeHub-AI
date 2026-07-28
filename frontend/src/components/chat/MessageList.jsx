import React, { useEffect, useRef } from 'react';
import { BookOpen, FileText, GitCompare, Layers, Zap, HelpCircle, Search } from 'lucide-react';
import MessageItem from './MessageItem';

/**
 * MessageList — Message stream + empty state.
 * Minimal hero. Calm prompt suggestion cards. Warm animated thinking indicator.
 */
export const MessageList = ({ messages = [], isThinking, onSelectCitation, onSelectPrompt }) => {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const PROMPTS = [
    { title: 'Summarize key research',   desc: 'Synthesize the main findings across all uploaded PDFs.',      q: 'Summarize the key findings and executive summary across all uploaded documents.', icon: BookOpen },
    { title: 'Compare perspectives',     desc: 'Contrast themes and conclusions between uploaded sources.',   q: 'Compare the core themes, arguments, and conclusions in the uploaded documents.',  icon: GitCompare },
    { title: 'Extract critical metrics', desc: 'Pull key statistics, dates, and quantitative data.',          q: 'Extract all important statistics, dates, and quantitative facts from the documents.',icon: Layers },
    { title: 'Identify action items',    desc: 'Generate recommendations and key takeaways.',                 q: 'What are the main action items, recommendations, and takeaways from these files?', icon: Zap },
    { title: 'Explain complex concepts', desc: 'Break down dense technical topics in plain language.',        q: 'Explain the most complex technical concepts or methodologies in simple terms.',    icon: HelpCircle },
    { title: 'Find contradictions',      desc: 'Uncover conflicting evidence or research gaps.',              q: 'Are there any contradictory findings or research gaps in the documents?',          icon: Search },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-3">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-center space-y-8 max-w-2xl mx-auto py-10 animate-fade-in">
          {/* Hero */}
          <div className="space-y-3">
            <div
              className="inline-flex p-3.5 rounded-2xl mx-auto"
              style={{ background: '#c2410c', boxShadow: '0 4px 20px rgba(194,65,12,0.25)' }}
            >
              <BookOpen className="w-8 h-8 text-white" strokeWidth={1.75} />
            </div>
            <h2 className="text-2xl font-bold tracking-tight" style={{ color: '#f0ede8' }}>
              KnowledgeHub AI
            </h2>
            <p className="text-sm leading-relaxed max-w-sm mx-auto" style={{ color: '#6e6055' }}>
              Enterprise knowledge assistant powered by Agentic RAG. Ask questions and receive grounded answers with exact source citations.
            </p>
          </div>

          {/* Prompt cards */}
          <div className="w-full space-y-2">
            <p className="text-[11px] font-mono font-semibold uppercase tracking-widest text-left mb-3" style={{ color: '#3c342c' }}>
              Suggested Explorations
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-left">
              {PROMPTS.map(({ title, desc, q, icon: Icon }) => (
                <button
                  key={title}
                  onClick={() => onSelectPrompt?.(q)}
                  className="flex items-start space-x-3 p-3.5 rounded-xl text-left transition-all duration-150 surface-card surface-card-hover group"
                >
                  <div
                    className="p-2 rounded-lg flex-shrink-0"
                    style={{ background: 'rgba(194,65,12,0.07)', border: '1px solid rgba(194,65,12,0.12)' }}
                  >
                    <Icon className="w-4 h-4" style={{ color: '#ea580c' }} strokeWidth={1.75} />
                  </div>
                  <div className="space-y-0.5 min-w-0 flex-1">
                    <h4 className="text-xs font-semibold" style={{ color: '#d6d3d1' }}>{title}</h4>
                    <p className="text-[11px] line-clamp-2" style={{ color: '#56524e' }}>{desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        messages.map((msg, i) => (
          <MessageItem key={i} message={msg} onSelectCitation={onSelectCitation} />
        ))
      )}

      {/* Thinking indicator */}
      {isThinking && (
        <div
          className="flex space-x-3.5 px-5 py-4 rounded-2xl"
          style={{ background: '#1a1713', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
            style={{ background: '#c2410c', boxShadow: '0 2px 8px rgba(194,65,12,0.20)' }}
          >
            <BookOpen className="w-3.5 h-3.5 text-white" strokeWidth={2} />
          </div>
          <div className="flex-1 space-y-2 py-0.5">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold" style={{ color: '#d6d3d1' }}>Agentic RAG in progress</span>
              <span
                className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(194,65,12,0.08)', color: '#fb923c', border: '1px solid rgba(194,65,12,0.16)' }}
              >
                Planner → Qdrant → Reflection → Groq
              </span>
            </div>
            <p className="text-xs font-mono" style={{ color: '#44403c' }}>
              Decomposing query · running hybrid vector search · reflecting on context coverage…
            </p>
            <div className="flex space-x-1.5 pt-1">
              {[0, 150, 300].map(d => (
                <div
                  key={d}
                  className="w-2 h-2 rounded-full animate-bounce"
                  style={{ background: '#c2410c', animationDelay: `${d}ms` }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
};

export default MessageList;
