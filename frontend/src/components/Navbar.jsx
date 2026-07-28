import React, { useState } from 'react';
import { BookOpen, RefreshCw, Settings, Database, Activity, X, Info, ChevronRight, Layers } from 'lucide-react';

/**
 * Navbar — Top navigation bar.
 * Warm graphite surface, copper accent logo mark, minimal status badges.
 * Linear/Vercel aesthetic: calm, restrained, purposeful.
 */
export const Navbar = ({ vectorCount = 0, isLoading = false, onRefresh, onToggleSidebar }) => {
  const [showSpec, setShowSpec] = useState(false);

  return (
    <>
      <header
        className="h-12 flex items-center justify-between px-5 flex-shrink-0 select-none"
        style={{
          background: '#0c0a07',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        {/* ── Left: Brand ── */}
        <div className="flex items-center space-x-4">
          {/* Mobile sidebar toggle */}
          <button
            onClick={onToggleSidebar}
            className="lg:hidden btn-ghost p-1.5"
            aria-label="Toggle sidebar"
          >
            <Layers className="w-4 h-4" />
          </button>

          {/* Logo mark */}
          <div className="flex items-center space-x-2.5">
            <div
              className="flex items-center justify-center w-7 h-7 rounded-lg"
              style={{ background: '#c2410c', boxShadow: '0 1px 4px rgba(194,65,12,0.35)' }}
            >
              <BookOpen className="w-4 h-4 text-white" strokeWidth={2} />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold tracking-tight" style={{ color: '#e8e2da' }}>
                KnowledgeHub
              </span>
              <span
                className="text-xs font-mono font-medium px-1.5 py-0.5 rounded"
                style={{
                  color: '#fb923c',
                  background: 'rgba(194,65,12,0.10)',
                  border: '1px solid rgba(194,65,12,0.18)',
                }}
              >
                AI
              </span>
            </div>
          </div>

          <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.08)' }} className="hidden md:block" />

          {/* Pipeline status — subdued, not badges everywhere */}
          <div className="hidden md:flex items-center space-x-1.5 text-xs font-mono" style={{ color: '#78716c' }}>
            <span>Agentic RAG</span>
            <span>·</span>
            <span>Groq Llama-3.3-70b</span>
          </div>
        </div>

        {/* ── Right: Metrics + Controls ── */}
        <div className="flex items-center space-x-2">
          {/* Vector count — minimal, no badge color explosion */}
          <div
            className="hidden sm:flex items-center space-x-1.5 text-xs font-mono px-3 py-1 rounded-lg"
            style={{
              background: '#171410',
              border: '1px solid rgba(255,255,255,0.07)',
              color: '#a8a29e',
            }}
          >
            <Database className="w-3.5 h-3.5" style={{ color: '#ea580c' }} />
            <span style={{ color: '#d6d3d1' }}>{vectorCount.toLocaleString()}</span>
            <span>vectors</span>
          </div>

          {/* Ready dot — minimal live indicator */}
          <div
            className="hidden xl:flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-lg"
            style={{
              background: '#171410',
              border: '1px solid rgba(255,255,255,0.07)',
              color: '#78716c',
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#4ade80', boxShadow: '0 0 4px #4ade80' }} />
            <span>Ready</span>
          </div>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="btn-ghost p-2"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} style={isLoading ? { color: '#ea580c' } : {}} />
          </button>

          <button
            onClick={() => setShowSpec(true)}
            className="btn-ghost p-2"
            title="System Specification"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* ── System Spec Modal ── */}
      {showSpec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in" style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)' }}>
          <div
            className="relative w-full max-w-md rounded-2xl shadow-lift-lg space-y-5 p-6"
            style={{ background: '#1a1713', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            <div className="flex items-center justify-between pb-4 divider">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg" style={{ background: 'rgba(194,65,12,0.10)', border: '1px solid rgba(194,65,12,0.18)' }}>
                  <BookOpen className="w-4 h-4" style={{ color: '#ea580c' }} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold" style={{ color: '#e8e2da' }}>KnowledgeHub AI — System Stack</h3>
                  <p className="text-xs" style={{ color: '#78716c' }}>Agentic RAG Architecture</p>
                </div>
              </div>
              <button onClick={() => setShowSpec(false)} className="btn-ghost p-1.5">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs font-mono" style={{ color: '#a8a29e' }}>
              {[
                ['Orchestration', 'Planner → Retriever → Reflection'],
                ['LLM', 'Groq  ·  Llama-3.3-70b-versatile'],
                ['Vector Store', 'Qdrant'],
                ['Embeddings', 'all-MiniLM-L6-v2 (384-dim)'],
                ['Hybrid Search', 'Dense cosine  +  Sparse BM25'],
                ['Max Iterations', '2 reflection passes'],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between px-3 py-2 rounded-xl"
                  style={{ background: '#12100d', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  <span style={{ color: '#78716c' }}>{label}</span>
                  <span style={{ color: '#d6d3d1' }}>{value}</span>
                </div>
              ))}
            </div>

            <div
              className="flex items-start space-x-2.5 p-3 rounded-xl text-xs"
              style={{ background: 'rgba(194,65,12,0.07)', border: '1px solid rgba(194,65,12,0.14)', color: '#fdba74' }}
            >
              <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#ea580c' }} />
              <p>Reflection Agent evaluates context coverage before finalizing answers. Triggers a second retrieval pass if coverage falls below threshold.</p>
            </div>

            <div className="flex justify-end pt-1">
              <button onClick={() => setShowSpec(false)} className="btn-primary text-xs px-4 py-2">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Navbar;
