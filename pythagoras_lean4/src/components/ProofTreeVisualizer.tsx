import React from 'react';
import { CheckCircle, Circle, GitBranch } from 'lucide-react';
import { Card } from '../atoms/Card';
import { LeanTacticState } from '../types/lean';

interface ProofTreeProps {
  states: readonly LeanTacticState[];
  activeIndex: number;
  onSelectStep: (idx: number) => void;
}

export const ProofTreeVisualizer: React.FC<ProofTreeProps> = ({
  states,
  activeIndex,
  onSelectStep
}) => {
  return (
    <Card title="Proof Tactic Tree" subtitle="Interactive Merklized proof sequence">
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {states.map((st, idx) => {
          const isActive = idx === activeIndex;
          const isDone = st.status === 'PROVEN';

          return (
            <button
              key={st.stepIndex}
              onClick={() => onSelectStep(idx)}
              className={`w-full text-left p-2.5 rounded-lg border font-mono text-xs transition-all flex items-center justify-between ${
                isActive
                  ? 'bg-sky-950/50 border-sky-500/80 text-sky-200 shadow-sm'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-400'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                {isDone ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : (
                  <Circle className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-600'}`} />
                )}
                <span className="truncate font-semibold">{st.tacticApplied}</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono flex-shrink-0 ml-2">
                {st.merkleHash.slice(0, 8)}
              </span>
            </button>
          );
        })}
      </div>
    </Card>
  );
};