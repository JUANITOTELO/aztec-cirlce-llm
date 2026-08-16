import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', size = 'md', children, className = '', ...props }) => {
  const base = 'inline-flex items-center justify-center font-medium rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed';
  const sizes = { sm: 'px-2.5 py-1 text-xs', md: 'px-3.5 py-2 text-sm', lg: 'px-5 py-2.5 text-base' };
  const variants = {
    primary: 'bg-emerald-600 hover:bg-emerald-500 text-white focus:ring-emerald-500 shadow-sm shadow-emerald-900/30',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-200 focus:ring-slate-600 border border-slate-700',
    danger: 'bg-rose-600 hover:bg-rose-500 text-white focus:ring-rose-500',
    outline: 'border border-slate-600 hover:bg-slate-800/60 text-slate-300 focus:ring-slate-500',
  };
  return (
    <button className={`${base} ${sizes[size]} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
};