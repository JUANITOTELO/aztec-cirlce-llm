import React from 'react';
import { ShieldCheck, Cpu, Code2, Terminal } from 'lucide-react';
import { Badge } from '../atoms/Badge';
import { LEAN_VERSION } from '../constants/leanPresets';

export const Header: React.FC<{ checksum: string }> = ({ checksum }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50 px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base text-slate-100 tracking-tight">Lean 4 Formal Pythagoras</h1>
              <Badge variant="success">KERNEL VERIFIED</Badge>
            </div>
            <p className="text-xs text-slate-400">Mathlib-Certified Geometric Dissection Proof System</p>
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