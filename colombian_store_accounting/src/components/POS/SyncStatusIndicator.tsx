import React from 'react';
import { useSyncStore } from '../../store/syncStore';

const statusStyles: Record<string, string> = {
  online: '#28a745', // green
  offline: '#6c757d', // gray
  syncing: '#007bff', // blue
  error: '#dc3545', // red
};

const SyncStatusIndicator: React.FC = () => {
  const { status, queueSize } = useSyncStore();

  const getTitle = () => {
    switch (status) {
      case 'online':
        return 'Online and synced';
      case 'offline':
        return `Offline - ${queueSize} transaction(s) pending`;
      case 'syncing':
        return `Syncing ${queueSize} transaction(s)...`;
      case 'error':
        return 'Sync error - check console';
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className="sync-indicator" title={getTitle()}>
      <span
        className="sync-dot"
        style={{ backgroundColor: statusStyles[status] || '#6c757d' }}
      />
      <span className="sync-text">
        {status.charAt(0).toUpperCase() + status.slice(1)}
        {queueSize > 0 && ` (${queueSize})`}
      </span>
    </div>
  );
};

export default SyncStatusIndicator;
