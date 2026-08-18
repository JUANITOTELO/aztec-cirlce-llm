import React from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, subtitle, action, children, className = '' }) => {
  return (
    <div className={`bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur-sm ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/80">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};