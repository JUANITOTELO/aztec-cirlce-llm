import React from 'react';
import { Tag } from 'lucide-react';
import { sanitizeCategoryText } from '../engine/categoryConstraints';

interface CategoryBadgeProps {
  name: string;
  color?: string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

export function CategoryBadge({ name, color = '#2563EB', size = 'sm', showIcon = true }: CategoryBadgeProps) {
  const safeName = sanitizeCategoryText(name) || 'Sin categoría';
  const isSmall = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full border ${
        isSmall ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm'
      }`}
      style={{
        backgroundColor: `${color}15`,
        borderColor: `${color}40`,
        color: color,
      }}
      title={`Categoría: ${safeName}`}
    >
      {showIcon && <Tag className={isSmall ? 'w-3 h-3' : 'w-3.5 h-3.5'} />}
      <span>{safeName}</span>
    </span>
  );
}