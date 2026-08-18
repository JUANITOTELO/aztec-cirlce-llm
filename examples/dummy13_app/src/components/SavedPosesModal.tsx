import React, { useState, useEffect } from 'react';
import { X, Trash2, Download, Play, Search, Database, Star, Clock, Plus, HardDriveDownload, HardDriveUpload } from 'lucide-react';
import { SavedPoseRecord } from '../types/dummy13';
import { dbService } from '../services/db';

interface SavedPosesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyPose: (pose: SavedPoseRecord) => void;
  onSaveCurrentPose: (name: string) => Promise<void>;
}

export const SavedPosesModal: React.FC<SavedPosesModalProps> = ({
  isOpen,
  onClose,
  onApplyPose,
  onSaveCurrentPose
}) => {
  const [poses, setPoses] = useState<SavedPoseRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [newPoseName, setNewPoseName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadPoses = async () => {
    try {
      const list = await dbService.getAllPoses();
      setPoses(list);
    } catch (err) {
      console.error('Failed to load poses from IndexedDB', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadPoses();
      setNewPoseName('');
      setStatusMessage(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newPoseName.trim();
    if (!trimmed) return;
    setIsSaving(true);
    try {
      await onSaveCurrentPose(trimmed);
      setNewPoseName('');
      await loadPoses();
      setStatusMessage('Pose saved to IndexedDB!');
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      console.error('Error saving pose:', err);
      setStatusMessage('Failed to save pose.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this saved pose from IndexedDB?')) return;
    try {
      await dbService.deletePose(id);
      await loadPoses();
    } catch (err) {
      console.error('Failed to delete pose', err);
    }
  };

  const handleToggleFavorite = async (pose: SavedPoseRecord, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated: SavedPoseRecord = {
      ...pose,
      isFavorite: !pose.isFavorite
    };
    await dbService.savePose(updated);
    await loadPoses();
  };

  const handleDownloadPose = (pose: SavedPoseRecord, e: React.MouseEvent) => {
    e.stopPropagation();
    const blob = new Blob([JSON.stringify(pose, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${pose.name.replace(/\s+/g, '_').toLowerCase() || 'pose'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportDB = async () => {
    try {
      const json = await dbService.exportAllData();
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dummy13_indexeddb_backup_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export database.');
    }
  };

  const handleImportDB = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async (evt) => {
        try {
          const text = evt.target?.result as string;
          const res = await dbService.importAllData(text);
          await loadPoses();
          alert(`Successfully restored ${res.posesCount} poses to IndexedDB!`);
        } catch (err) {
          alert('Failed to import database backup.');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  const filteredPoses = poses.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-2xl bg-dummyPanel border border-dummyBorder rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dummyBorder bg-dummyDark/50">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-dummyAccent/20 border border-dummyAccent/40 flex items-center justify-center text-dummyAccent">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white leading-none">IndexedDB Pose Library</h2>
              <p className="text-xs text-slate-400 mt-1 font-mono">Persistent browser storage</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Save Bar */}
        <div className="p-4 border-b border-dummyBorder bg-dummyDark/30">
          <form onSubmit={handleSave} className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Enter pose name to save current state..."
              value={newPoseName}
              onChange={(e) => setNewPoseName(e.target.value)}
              className="flex-1 bg-dummyDark text-sm text-slate-200 border border-dummyBorder rounded-xl px-3.5 py-2 focus:outline-none focus:border-dummyAccent transition placeholder:text-slate-500"
            />
            <button
              type="submit"
              disabled={!newPoseName.trim() || isSaving}
              className="px-4 py-2 bg-dummyAccent hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition shadow-lg shadow-sky-500/20 whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              Save to DB
            </button>
          </form>
          {statusMessage && (
            <p className="text-xs text-emerald-400 mt-2 animate-in fade-in">{statusMessage}</p>
          )}
        </div>

        {/* Search & DB Action Bar */}
        <div className="px-4 py-2.5 bg-dummyDark/40 flex items-center justify-between gap-3 border-b border-dummyBorder">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search saved poses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-dummyDark text-xs text-slate-200 border border-dummyBorder rounded-lg pl-9 pr-3 py-1.5 focus:outline-none focus:border-dummyAccent transition placeholder:text-slate-500"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleExportDB}
              title="Backup entire IndexedDB to file"
              className="px-2.5 py-1.5 bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder rounded-lg text-xs flex items-center gap-1 transition"
            >
              <HardDriveDownload className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Backup DB</span>
            </button>
            <button
              onClick={handleImportDB}
              title="Restore IndexedDB from backup file"
              className="px-2.5 py-1.5 bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder rounded-lg text-xs flex items-center gap-1 transition"
            >
              <HardDriveUpload className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Restore DB</span>
            </button>
          </div>
        </div>

        {/* Poses List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5 custom-scrollbar min-h-[220px]">
          {filteredPoses.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-center text-slate-500">
              <Database className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">No saved poses in IndexedDB</p>
              <p className="text-xs text-slate-600 mt-1">
                Type a name above and click &quot;Save to DB&quot; to store custom poses in your browser.
              </p>
            </div>
          ) : (
            filteredPoses.map((pose) => (
              <div
                key={pose.id}
                onClick={() => onApplyPose(pose)}
                className="group flex items-center justify-between p-3 rounded-xl bg-dummyDark/70 hover:bg-dummyDark border border-dummyBorder/80 hover:border-dummyAccent/60 transition cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  {pose.thumbnail ? (
                    <img
                      src={pose.thumbnail}
                      alt={pose.name}
                      className="w-12 h-12 rounded-lg object-cover bg-slate-900 border border-dummyBorder"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-slate-800/80 border border-dummyBorder flex items-center justify-center text-slate-400 font-bold text-xs">
                      13
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-sm text-slate-200 group-hover:text-white transition">
                        {pose.name}
                      </h4>
                      {pose.isFavorite && (
                        <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500 font-mono">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(pose.timestamp).toLocaleDateString()} {new Date(pose.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition">
                  <button
                    onClick={(e) => handleToggleFavorite(pose, e)}
                    title={pose.isFavorite ? 'Remove Favorite' : 'Mark Favorite'}
                    className={`p-1.5 rounded-lg border border-dummyBorder transition ${
                      pose.isFavorite
                        ? 'bg-amber-400/10 text-amber-400 border-amber-400/30'
                        : 'bg-dummyPanel hover:bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <Star className={`w-3.5 h-3.5 ${pose.isFavorite ? 'fill-amber-400' : ''}`} />
                  </button>

                  <button
                    onClick={(e) => handleDownloadPose(pose, e)}
                    title="Export pose as JSON file"
                    className="p-1.5 rounded-lg bg-dummyPanel hover:bg-slate-800 text-slate-400 hover:text-white border border-dummyBorder transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={(e) => handleDelete(pose.id, e)}
                    title="Delete pose from IndexedDB"
                    className="p-1.5 rounded-lg bg-dummyPanel hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-dummyBorder hover:border-red-500/30 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => onApplyPose(pose)}
                    title="Apply Pose to Mannequin"
                    className="px-3 py-1.5 rounded-lg bg-dummyAccent/20 hover:bg-dummyAccent text-dummyAccent hover:text-white border border-dummyAccent/40 transition text-xs font-medium flex items-center gap-1"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    Apply
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
