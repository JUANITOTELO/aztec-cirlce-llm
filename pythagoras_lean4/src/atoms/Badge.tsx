import React from 'react';

interface BadgeProps {
  variant?: 'success' | 'warning' | 'info' | 'purple' | 'neutral';
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'info', children }) => {
  const variants = {
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    info: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    neutral: 'bg-slate-800 text-slate-400 border-slate-700'
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${variants[variant]}`}>
      {children}
    </span>
  );
};