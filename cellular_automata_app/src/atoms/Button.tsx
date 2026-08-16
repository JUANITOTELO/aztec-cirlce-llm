import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  isActive?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ children, isActive, ...props }) => {
  const baseClasses = 'px-3 py-2 rounded-md flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500';
  const activeClasses = isActive ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600';

  return (
    <button className={`${baseClasses} ${activeClasses}`} {...props}>
      {children}
    </button>
  );
};
