import React from 'react';
import { CheckCircle2, ChevronRight, Hash, Layers } from 'lucide-react';
import { Card } from '../atoms/Card';
import { Badge } from '../atoms/Badge';
import { Toggle } from '../atoms/Toggle';
import { LeanTacticState } from '../types/lean';

interface TacticExplorerProps {
  currentState: LeanTacticState;
  showImplicits: boolean;
  onToggleImplicits: (v: boolean) => void;
}

export const TacticStateExplorer: React.FC<TacticExplorerProps> = ({
  currentState,
  showImplicits,
  onToggleImplicits
}) => {
  const visibleHyps = showImplicits
    ? currentState.hypotheses
    : currentState.hypotheses.filter(h => !h.isImplicit);

  return (
    <Card
      title="Lean 4 Tactic State Explorer"
      subtitle="Live kernel goal inspection and local context"
      action={
        <Toggle
          label="Explicit Implicits"
          checked={showImplicits}
          onChange={onToggleImplicits}
        />
      }
    >
      <div className="space-y-3">
        {/* Tactic applied banner */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-xs">
          <div className="text-slate-400 text-[10px] uppercase font-semibold mb-1 flex items-center justify-between">
            <span className="flex items-center gap-1"><ChevronRight className="w-3 h-3 text-sky-400" /> Tactic Applied</span>
            <span className="text-slate-500">Clock #{currentState.logicalClock}</span>
          </div>
          <div className="text-sky-300 font-bold">{currentState.tacticApplied}</div>
          <div className="text-slate-400 text-xs mt-1 font-sans">{currentState.explanation}</div>
        </div>

        {/* Hypotheses Local Context */}
        <div>
          <div className="text-xs font-mono text-slate-400 mb-1.5 flex items-center gap-1">
            <Layers className="w-3 h-3 text-purple-400" /> Local Hypotheses ({visibleHyps.length}):
          </div>
          <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
            {visibleHyps.map((h) => (
              <div
                key={h.id}
                className="bg-slate-950/80 px-2.5 py-1.5 rounded border border-slate-800/80 font-mono text-xs flex justify-between items-center"
              >
                <span className="text-purple-300 font-semibold">{h.name} :</span>
                <span className="text-slate-300">{h.type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Goals */}
        <div>
          <div className="text-xs font-mono text-slate-400 mb-1.5 flex items-center gap-1">
            <Hash className="w-3 h-3 text-emerald-400" /> Open Goals ({currentState.goals.length}):
          </div>
          <div className="space-y-1.5">
            {currentState.goals.map((g, idx) => (
              <div
                key={idx}
                className={`p-2.5 rounded-lg font-mono text-xs border ${
                  currentState.status === 'PROVEN'
                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-amber-300'
                }`}
              >
                {g}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};