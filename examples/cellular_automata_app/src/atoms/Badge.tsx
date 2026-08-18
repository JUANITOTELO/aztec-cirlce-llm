import React from 'react';

interface BadgeProps {
  label: string;
  value: string | number;
}

export const Badge: React.FC<BadgeProps> = ({ label, value }) => {
  return (
    <div className="flex items-center space-x-2 text-xs">
      <span className="text-gray-400">{label}</span>
      <span className="font-mono bg-gray-700 px-2 py-0.5 rounded">
        {value}
      </span>
    </div>
  );
};
