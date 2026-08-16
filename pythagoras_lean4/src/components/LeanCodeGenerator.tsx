import React, { useState } from 'react';
import { Copy, Check, Download, FileCode, Package } from 'lucide-react';
import { Card } from '../atoms/Card';
import { Button } from '../atoms/Button';
import { generateLeanProject } from '../engine/proofExporter';
import { GeometryParams } from '../types/proofState';

export const LeanCodeGenerator: React.FC<{ params: GeometryParams }> = ({ params }) => {
  const [tab, setTab] = useState<'source' | 'lakefile'>('source');
  const [copied, setCopied] = useState(false);
  const project = generateLeanProject(params);

  const activeCode = tab === 'source' ? project.leanSource : project.lakefile;

  const handleCopy = () => {
    navigator.clipboard.writeText(activeCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([project.leanSource], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Pythagoras_${params.a}_${params.b}.lean`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card
      title="Lean 4 Code Generator & Lakefile"
      subtitle="Exportable mathlib4-compatible formal certificate"
      action={
        <div className="flex gap-1.5">
          <Button variant="secondary" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="ml-1 text-xs">{copied ? 'Copied' : 'Copy'}</span>
          </Button>
          <Button variant="secondary" size="sm" onClick={handleDownload}>
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span className="ml-1 text-xs">Export</span>
          </Button>
        </div>
      }
    >
      <div className="flex gap-2 mb-2.5">
        <button
          onClick={() => setTab('source')}
          className={`px-3 py-1 rounded text-xs font-mono transition-colors flex items-center gap-1.5 ${
            tab === 'source' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40' : 'bg-slate-950 text-slate-400 border border-slate-800'
          }`}
        >
          <FileCode className="w-3 h-3" /> Pythagoras.lean
        </button>
        <button
          onClick={() => setTab('lakefile')}
          className={`px-3 py-1 rounded text-xs font-mono transition-colors flex items-center gap-1.5 ${
            tab === 'lakefile' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40' : 'bg-slate-950 text-slate-400 border border-slate-800'
          }`}
        >
          <Package className="w-3 h-3" /> lakefile.lean
        </button>
      </div>

      <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-64 scrollbar-thin leading-relaxed">
        <code>{activeCode}</code>
      </pre>
    </Card>
  );
};