import React, { useEffect, useState } from 'react';
import { BookOpen, X } from 'lucide-react';
import type { ArchitectureMode } from './ArchitectureView';

/** Content shape written by frontend/scripts/build_architecture.py (source: scripts/architecture_explain.py). */
interface ExplainSection {
  heading: string;
  body?: string[];
  steps?: [string, string, string][]; // [badge, title, text]
  table?: { cols: string[]; rows: string[][] };
}
interface ExplainContent {
  title: string;
  intro: string;
  sections: ExplainSection[];
}

const GLYPH: Record<string, string> = {
  '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
};

/** Badge styled like the diagram: number = typed path, letter = voice path, D# = data path. */
const Badge: React.FC<{ b: string }> = ({ b }) => {
  if (b.startsWith('D'))
    return (
      <span className="inline-flex items-center justify-center h-5 min-w-[1.75rem] px-1.5 rounded-full bg-violet-500 text-white text-[10px] font-bold shrink-0">
        {b}
      </span>
    );
  if (/^[A-Z]$/.test(b))
    return (
      <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-cyan-400 text-[#020617] text-[10px] font-bold shrink-0">
        {b}
      </span>
    );
  return (
    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-100 text-[#020617] text-[10px] font-bold shrink-0 ring-1 ring-slate-400">
      {GLYPH[b] ?? b}
    </span>
  );
};

/**
 * BL-8 follow-up: plain-English commentary next to the architecture diagram ("Explain" button).
 * Same text as docs/how_urvi_works.md (both generated from scripts/architecture_explain.py).
 */
export const ExplainPanel: React.FC<{ mode: ArchitectureMode; onClose: () => void }> = ({ mode, onClose }) => {
  const [content, setContent] = useState<ExplainContent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setContent(null);
    setError(null);
    fetch(`/architecture/explain-${mode}.json`)
      .then((r) => (r.ok ? (r.json() as Promise<ExplainContent>) : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((c) => !cancelled && setContent(c))
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      cancelled = true;
    };
  }, [mode]);

  return (
    <aside
      className="w-[440px] max-w-[45%] h-full shrink-0 border-l border-border bg-[#0b1220] flex flex-col"
      aria-label="Architecture explanation"
      data-testid="architecture-explain-panel"
    >
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border shrink-0">
        <BookOpen className="w-4 h-4 text-accent" />
        <span className="text-sm font-semibold text-white">Explanation</span>
        <span className="text-[11px] text-textMuted">{mode === 'current' ? 'Current · V 1.0' : 'Target · production'}</span>
        <button
          type="button"
          onClick={onClose}
          className="ml-auto p-1 rounded text-textMuted hover:text-white hover:bg-surface"
          aria-label="Close explanation"
          title="Close explanation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 text-[12.5px] leading-relaxed text-slate-300 font-sans">
        {error && <p className="text-red-300">Explanation unavailable ({error}).</p>}
        {!content && !error && <p className="text-textMuted">Loading…</p>}
        {content && (
          <>
            <h2 className="text-[15px] font-semibold text-white mb-1.5">{content.title}</h2>
            <p className="mb-4 text-slate-200">{content.intro}</p>
            {content.sections.map((sec) => (
              <section key={sec.heading} className="mb-5">
                <h3 className="text-[12px] uppercase tracking-wide font-semibold text-accent mb-2">{sec.heading}</h3>
                {sec.body?.map((p, i) => (
                  <p key={i} className="mb-2">
                    {p}
                  </p>
                ))}
                {sec.steps && (
                  <ol className="space-y-2.5">
                    {sec.steps.map(([b, t, txt]) => (
                      <li key={b} className="flex gap-2.5">
                        <Badge b={b} />
                        <div>
                          <span className="font-semibold text-white">{t}. </span>
                          {txt}
                        </div>
                      </li>
                    ))}
                  </ol>
                )}
                {sec.table && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-[11.5px] border-collapse">
                      <thead>
                        <tr>
                          {sec.table.cols.map((c) => (
                            <th key={c} className="text-left font-semibold text-white border-b border-border py-1.5 pr-2 align-bottom">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sec.table.rows.map((r, i) => (
                          <tr key={i} className="border-b border-border/50">
                            {r.map((cell, j) => (
                              <td key={j} className="py-1.5 pr-2 align-top">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            ))}
            <p className="text-[11px] text-textMuted border-t border-border pt-3">
              Also available as a document: docs/how_urvi_works.md
            </p>
          </>
        )}
      </div>
    </aside>
  );
};

export default ExplainPanel;
