import React from 'react';
import { Files, Layers, BookOpen, Calculator, Database, Clock, HardDrive } from 'lucide-react';

/**
 * StatsBar — Dashboard metric cards.
 * Neutral graphite surfaces + large warm-white typography.
 * ONE copper accent per card (indicator dot + icon). No rainbow gradients.
 */
export const StatsBar = ({ stats }) => {
  if (!stats) return null;

  const formattedLastUpload = stats.last_upload_at
    ? new Date(stats.last_upload_at).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : '—';

  const estMb = (((stats.total_chunks || 0) * 12) / 1024 || 0.1).toFixed(1);

  const items = [
    { label: 'Indexed PDFs',    value: (stats.total_documents ?? 0).toLocaleString(), icon: Files },
    { label: 'Qdrant Vectors',  value: (stats.total_vectors   ?? 0).toLocaleString(), icon: Database },
    { label: 'Stored Chunks',   value: (stats.total_chunks    ?? 0).toLocaleString(), icon: Layers },
    { label: 'Total Pages',     value: (stats.total_pages     ?? 0).toLocaleString(), icon: BookOpen },
    { label: 'Avg Chunks / PDF',value: String(stats.avg_chunks_per_document ?? 0),    icon: Calculator },
    { label: 'Index Size',      value: `${estMb} MB`,                                 icon: HardDrive },
  ];

  return (
    <div className="p-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
      {/* Section header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: '#56524e' }}>
          Knowledge Metrics
        </span>
        {stats.last_upload_at && (
          <span className="text-[10px] font-mono flex items-center space-x-1" style={{ color: '#56524e' }}>
            <Clock className="w-3 h-3" />
            <span>{formattedLastUpload}</span>
          </span>
        )}
      </div>

      {/* Stat card grid */}
      <div className="grid grid-cols-2 gap-2">
        {items.map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="relative px-3 py-3 rounded-xl overflow-hidden surface-card surface-card-hover"
          >
            {/* Copper indicator line at top */}
            <div
              className="absolute top-0 left-0 right-0 h-px"
              style={{ background: 'rgba(234,88,12,0.35)' }}
            />

            <div className="flex items-center justify-between mb-2">
              <Icon className="w-3.5 h-3.5" style={{ color: '#ea580c' }} strokeWidth={1.75} />
            </div>

            {/* Large metric number */}
            <div
              className="text-xl font-bold tracking-tight leading-none font-mono"
              style={{ color: '#f0ede8' }}
            >
              {value}
            </div>
            <div
              className="text-[11px] mt-1 font-medium"
              style={{ color: '#6e6055' }}
            >
              {label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatsBar;
