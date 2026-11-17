import React, { useEffect, useRef, useState } from 'react';
import { BookOpen, ExternalLink, Network, X } from 'lucide-react';
import { ExplainPanel } from './ExplainPanel';

export type ArchitectureMode = 'current' | 'target';

interface ArchitectureViewProps {
  mode: ArchitectureMode;
  onModeChange: (mode: ArchitectureMode) => void;
  onClose: () => void;
  /** Width reserved on the right for the docked Urvi agent, so the agent stays usable (voice: "show target"). */
  rightInset?: number | string;
}

const MODES: { id: ArchitectureMode; label: string; hint: string }[] = [
  { id: 'current', label: 'Current · V 1.0', hint: 'As built and running on Cloud Run today' },
  { id: 'target', label: 'Target · production', hint: 'Production path: SSO, autoscaling, Vertex AI training + Search' },
];

/**
 * BL-8: Architecture tab. Shows the generated diagrams (frontend/public/architecture/{current,target}.html,
 * built by scripts/build_architecture.py with the architecture-diagram skill + official Google Cloud icons;
 * `-light.html` variants follow Google Cloud light styling for decks).
 * Opened from the header button or by asking Urvi (ui_control architecture open|current|target|close).
 * Hover any component in the diagram for a short explanation. Esc closes it.
 */
export const ArchitectureView: React.FC<ArchitectureViewProps> = ({ mode, onModeChange, onClose, rightInset = 0 }) => {
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const frameRef = useRef<HTMLIFrameElement>(null);
  // Explanation panel: plain-English commentary for the diagram shown (Explain button).
  const [explainOpen, setExplainOpen] = useState<boolean>(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      e.stopImmediatePropagation();
      closeRef.current();
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, []);

  // Esc also works while the pointer / focus is inside the diagram.
  const onFrameLoad = () => {
    frameRef.current?.contentWindow?.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeRef.current();
    });
  };

  const src = `/architecture/${mode}.html`;
  return (
    <div
      className="fixed left-0 bottom-0 top-16 z-[1000] flex flex-col bg-[#020617] border-t border-border"
      style={{ right: rightInset }}
      role="dialog"
      aria-label="Urvi architecture"
      data-testid="architecture-view"
    >
      <div className="flex items-center gap-3 px-4 py-2 bg-[#0d1117] border-b border-border shrink-0">
        <Network className="w-4 h-4 text-accent" />
        <span className="text-sm font-semibold text-white">Architecture</span>
        <div className="flex items-center gap-1 bg-[#020617] border border-border rounded-lg p-0.5 ml-2" role="tablist">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              role="tab"
              aria-selected={mode === m.id}
              title={m.hint}
              onClick={() => onModeChange(m.id)}
              className={`px-3 py-1 rounded-md text-xs transition-colors ${
                mode === m.id ? 'bg-accent/80 text-white font-semibold' : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <span className="hidden lg:inline text-[11px] text-textMuted">Hover any component for details</span>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={() => setExplainOpen((v) => !v)}
            aria-pressed={explainOpen}
            data-testid="architecture-explain"
            title="Plain-English explanation of this diagram, step by step"
            className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded border transition-colors ${
              explainOpen ? 'bg-accent/80 border-accent text-white font-semibold' : 'border-accent/60 text-accent hover:bg-accent/20'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" /> Explain
          </button>
          <a
            href={`/architecture/${mode}-light.html`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded border border-border text-textMuted hover:text-white hover:bg-surface"
            title="Light Google Cloud style version for slides and documents (opens in a new tab)"
          >
            <ExternalLink className="w-3.5 h-3.5" /> Light version
          </a>
          <a
            href={src}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded border border-border text-textMuted hover:text-white hover:bg-surface"
            title="Open this diagram in a new browser tab"
          >
            <ExternalLink className="w-3.5 h-3.5" /> New tab
          </a>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded text-textMuted hover:text-white hover:bg-surface"
            title="Close (Esc)"
            aria-label="Close architecture"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="px-4 py-1.5 bg-[#0f172a]/95 border-b border-cyan-500/30 text-[11px] text-slate-200 flex items-center gap-2 shrink-0">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
        <span>
          <strong className="text-cyan-300 font-semibold">Single-Agent, Multi-Tool Hybrid Architecture:</strong>{' '}
          Natural spoken &amp; typed language in (Gemini ADK / Live) → deterministic engineering physics, ML models &amp; numeric-grounding guards underneath — best of both worlds with minimal hallucination.
        </span>
      </div>
      <div className="flex-1 min-h-0 flex">
        <iframe
          key={mode}
          ref={frameRef}
          title={`Urvi architecture · ${mode}`}
          src={src}
          onLoad={onFrameLoad}
          className="flex-1 min-w-0 h-full border-0 bg-[#020617]"
        />
        {explainOpen && <ExplainPanel mode={mode} onClose={() => setExplainOpen(false)} />}
      </div>
    </div>
  );
};

export default ArchitectureView;
