import React from 'react';
import { Badge } from '../atoms/Badge';
import { SimulationMetrics } from '../types/simulation';

interface MetricsBarProps {
  metrics: SimulationMetrics;
}

export const MetricsBar: React.FC<MetricsBarProps> = ({ metrics }) => {
  return (
    <footer className="bg-gray-900/80 border-t border-gray-700 px-4 py-2 flex items-center justify-end space-x-6">
      <Badge label="Generation" value={metrics.generation} />
      <Badge label="Population" value={metrics.population} />
    </footer>
  );
};
