import React, { useState } from 'react';
import { Download, Copy, Check, FileCode } from 'lucide-react';
import { Card } from '../atoms/Card';
import { Button } from '../atoms/Button';
import { GeometryParams, TheoremType } from '../types/proofState';
import { generateLeanProject } from '../engine/proofExporter';

export const LeanCodeGenerator: React.FC<{ params: GeometryParams; theorem: TheoremType }> = ({ params, theorem }) => {
  const [copied, setCopied] = useState(false);
  const project = generateLeanProject(params, theorem);

  const handleCopy = () => {
    navigator.clipboard.writeText(project.leanSource);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadZip = () => {
    const blob = new Blob([project.leanSource], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = theorem === 'binomial' ? 'BinomialDissection.lean' : 'PythagorasDissection.lean';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card
      title="Lean 4 Formal Specification"
      subtitle="Lake Project Package Source (lakefile.lean + Dissection.lean)"
      action={
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400 mr-1" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
          <Button variant="secondary" size="sm" onClick={handleDownloadZip}>
            <Download className="w-3.5 h-3.5 mr-1" /> Export .lean
          </Button>
        </div>
      }
    >
      <div className="relative rounded-lg bg-slate-950 p-3 font-mono text-xs text-slate-300 border border-slate-800 overflow-x-auto">
        <div className="flex items-center gap-2 text-slate-500 pb-2 mb-2 border-b border-slate-900">
          <FileCode className="w-4 h-4 text-sky-400" />
          <span>Dissection.lean</span>
        </div>
        <pre className="text-sky-300 leading-relaxed font-mono whitespace-pre-wrap">{project.leanSource}</pre>
      </div>
    </Card>
  );
};
