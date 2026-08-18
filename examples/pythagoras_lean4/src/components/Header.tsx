import React from 'react';
import { ShieldCheck, Cpu, Terminal } from 'lucide-react';
import { Badge } from '../atoms/Badge';
import { LEAN_VERSION } from '../constants/leanPresets';
import { TheoremType } from '../types/proofState';

interface HeaderProps {
  checksum: string;
  theorem: TheoremType;
}

export const Header: React.FC<HeaderProps> = ({ checksum, theorem }) => {
  const THEOREM_METADATA: Record<TheoremType, { title: string; subtitle: string }> = {
    pythagoras: {
      title: 'Lean 4 Formal Pythagoras',
      subtitle: 'Mathlib-Certified Geometric Dissection Proof (a² + b² = c²)'
    },
    binomial: {
      title: 'Lean 4 Formal Binomial Expansion (Euclid II.4)',
      subtitle: 'Mathlib-Certified Geometric Dissection Proof ((a + b)² = a² + 2ab + b²)'
    },
    gougu: {
      title: 'Lean 4 Formal Gougu Theorem (Base & Altitude Theorem)',
      subtitle: 'Zhoubi Suanjing Zhao Shuang Hypotenuse Diagram Dissection Proof'
    }
  };

  const { title, subtitle } = THEOREM_METADATA[theorem];

  return (
    <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md px-6 py-3.5 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base text-slate-100 tracking-tight">{title}</h1>
              <Badge variant="success">KERNEL VERIFIED</Badge>
            </div>
            <p className="text-xs text-slate-400">{subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-md">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>Toolchain:</span>
            <span className="text-slate-200">{LEAN_VERSION}</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-md">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            <span>Merkle:</span>
            <span className="text-sky-400">{checksum.slice(0, 8)}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
