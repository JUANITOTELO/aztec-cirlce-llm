import React, { useRef } from 'react';
import {
  RotateCcw,
  FlipHorizontal,
  Download,
  Upload,
  Camera,
  Move,
  Rotate3d,
  HelpCircle,
  Palette,
  SlidersHorizontal,
  ArrowDownToLine,
  Magnet,
  Database
} from 'lucide-react';
import { POSE_PRESETS } from '../engine/PresetLibrary';
import { GizmoMode, PoseData } from '../types/dummy13';

interface ToolbarProps {
  currentPoseId: string;
  gizmoMode: GizmoMode;
  onSelectPreset: (preset: PoseData) => void;
  onResetPose: () => void;
  onMirrorPose: (side: 'left' | 'right') => void;
  onSetGizmoMode: (mode: GizmoMode) => void;
  onExportPose: () => void;
  onImportPose: (pose: PoseData) => void;
  onCaptureScreenshot: () => void;
  onToggleThemeModal: () => void;
  onToggleInspector: () => void;
  onToggleHelpModal: () => void;
  isGravityEnabled: boolean;
  onToggleGravity?: () => void;
  onDropToFloor: () => void;
  isInspectorOpen: boolean;
  onOpenSavedPoses: () => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  currentPoseId,
  gizmoMode,
  onSelectPreset,
  onResetPose,
  onMirrorPose,
  onSetGizmoMode,
  onExportPose,
  onImportPose,
  onCaptureScreenshot,
  onToggleThemeModal,
  onToggleInspector,
  onToggleHelpModal,
  isGravityEnabled,
  onToggleGravity,
  onDropToFloor,
  isInspectorOpen,
  onOpenSavedPoses
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        if (json.joints && json.version) {
          onImportPose(json as PoseData);
        } else {
          alert('Invalid Dummy 13 Pose JSON structure.');
        }
      } catch (err) {
        alert('Failed to parse Pose JSON file.');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  return (
    <header className="absolute top-3 left-3 right-3 flex flex-wrap items-center justify-between gap-3 p-3 bg-dummyPanel/90 backdrop-blur-md rounded-xl border border-dummyBorder shadow-2xl z-30">
      {/* Left: Brand & Presets */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 pr-3 border-r border-dummyBorder">
          <div className="w-8 h-8 rounded-lg bg-dummyAccent flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
            13
          </div>
          <div>
            <h1 className="font-bold text-sm leading-tight text-white tracking-wide">DUMMY 13 / T13</h1>
            <p className="text-[10px] text-slate-400 font-mono">3D Mannequin Studio</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-medium hidden sm:inline-block">Pose:</label>
          <select
            value={currentPoseId}
            onChange={(e) => {
              const found = POSE_PRESETS.find((p) => p.id === e.target.value);
              if (found) onSelectPreset(found);
            }}
            className="bg-dummyDark text-xs text-slate-200 border border-dummyBorder rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-dummyAccent transition"
          >
            {POSE_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Center: Transform Tools */}
      <div className="flex items-center bg-dummyDark/80 rounded-lg p-1 border border-dummyBorder gap-1">
        <button
          onClick={() => onSetGizmoMode('rotate')}
          title="Rotate Joint Tool"
          className={`p-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
            gizmoMode === 'rotate' ? 'bg-dummyAccent text-white' : 'text-slate-400 hover:text-white'
          }`}
        >
          <Rotate3d className="w-4 h-4" />
          <span className="hidden md:inline">Rotate</span>
        </button>
        <button
          onClick={() => onSetGizmoMode('translate')}
          title="Translate Root/Pelvis"
          className={`p-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
            gizmoMode === 'translate' ? 'bg-dummyAccent text-white' : 'text-slate-400 hover:text-white'
          }`}
        >
          <Move className="w-4 h-4" />
          <span className="hidden md:inline">Translate</span>
        </button>
      </div>

      {/* Right: Actions, Customization & Export */}
      <div className="flex items-center gap-2">
        <button
          onClick={onResetPose}
          title="Reset to T-Pose (R)"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <button
          onClick={onToggleGravity}
          title={isGravityEnabled ? 'Gravity Simulation Active (G)' : 'Gravity Simulation Disabled (G)'}
          className={`p-2 rounded-lg border border-dummyBorder transition flex items-center gap-1 text-xs font-medium ${
            isGravityEnabled
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-sm'
              : 'bg-dummyDark hover:bg-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          <Magnet className="w-4 h-4" />
          <span className="hidden lg:inline">{isGravityEnabled ? 'Gravity ON' : 'Gravity OFF'}</span>
        </button>

        <button
          onClick={onDropToFloor}
          title="Rest Mannequin on Solid Floor (Y=0)"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <ArrowDownToLine className="w-4 h-4" />
        </button>

        <button
          onClick={() => onMirrorPose('left')}
          title="Mirror Left Arm/Leg to Right Side"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <FlipHorizontal className="w-4 h-4" />
        </button>
        <button
          onClick={onOpenSavedPoses}
          title="Saved Poses Library (IndexedDB)"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-dummyAccent hover:text-white border border-dummyBorder hover:border-dummyAccent/50 transition flex items-center gap-1.5 text-xs font-semibold shadow-sm"
        >
          <Database className="w-4 h-4 text-dummyAccent" />
          <span className="hidden sm:inline">Library</span>
        </button>

        <div className="h-5 w-[1px] bg-dummyBorder mx-1 hidden sm:block" />

        <button
          onClick={onExportPose}
          title="Export Pose JSON"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          title="Import Pose JSON"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <Upload className="w-4 h-4" />
        </button>
        <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={handleFileChange} />

        <button
          onClick={onCaptureScreenshot}
          title="Take Clean HD Snapshot"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <Camera className="w-4 h-4" />
        </button>

        <button
          onClick={onToggleThemeModal}
          title="Armor & Material Themes"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-300 hover:text-white border border-dummyBorder transition"
        >
          <Palette className="w-4 h-4" />
        </button>

        <button
          onClick={onToggleInspector}
          title="Toggle Joint Angle Inspector"
          className={`p-2 rounded-lg border border-dummyBorder transition ${
            isInspectorOpen ? 'bg-dummyAccent text-white' : 'bg-dummyDark hover:bg-slate-800 text-slate-300'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>

        <button
          onClick={onToggleHelpModal}
          title="Shortcuts & Help Guide"
          className="p-2 rounded-lg bg-dummyDark hover:bg-slate-800 text-slate-400 hover:text-white border border-dummyBorder transition"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
