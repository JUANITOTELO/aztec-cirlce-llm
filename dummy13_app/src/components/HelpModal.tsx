import React from 'react';
import { X, MousePointer, Move3d, RotateCw, Save } from 'lucide-react';

interface HelpModalProps {
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-dummyPanel rounded-2xl border border-dummyBorder p-6 shadow-2xl text-slate-100">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-dummyBorder">
          <h2 className="text-lg font-bold">Dummy 13 Studio Controls & Guide</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 text-xs text-slate-300 mb-6">
          <div className="flex gap-3 items-start bg-dummyDark p-3 rounded-xl border border-dummyBorder">
            <MousePointer className="w-5 h-5 text-dummyAccent shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-white mb-0.5">Selecting Joints</h4>
              <p>Click on any spherical joint handle directly on the 3D model. The Transform Gizmo will lock to that joint's rotational pivot.</p>
            </div>
          </div>

          <div className="flex gap-3 items-start bg-dummyDark p-3 rounded-xl border border-dummyBorder">
            <RotateCw className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-white mb-0.5">Rotating Limbs (Physical Limits)</h4>
              <p>Drag the Red/Green/Blue rings on the Gizmo. The engine enforces authentic Dummy 13 ball socket and hinge clamps via swing-twist quaternion constraints to prevent hyper-extension.</p>
            </div>
          </div>

          <div className="flex gap-3 items-start bg-dummyDark p-3 rounded-xl border border-dummyBorder">
            <Move3d className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-white mb-0.5">Camera Navigation</h4>
              <p><strong className="text-white">Left Drag on background:</strong> Orbit 360° around figure.<br /><strong className="text-white">Right Drag:</strong> Pan camera position.<br /><strong className="text-white">Scroll Wheel:</strong> Zoom in / out.</p>
            </div>
          </div>

          <div className="flex gap-3 items-start bg-dummyDark p-3 rounded-xl border border-dummyBorder">
            <Save className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-white mb-0.5">Pose Sharing & Export</h4>
              <p>Export your handcrafted poses to lightweight JSON files or capture studio HD transparent PNG renders with one click.</p>
            </div>
          </div>

          <div className="flex gap-3 items-start bg-dummyDark p-3 rounded-xl border border-dummyBorder">
            <div className="flex items-center justify-center w-5 h-5 font-mono text-[11px] font-bold bg-dummyAccent/20 text-dummyAccent border border-dummyAccent/40 rounded shrink-0 mt-0.5">
              ⌨
            </div>
            <div>
              <h4 className="font-semibold text-white mb-0.5">Keyboard Shortcuts</h4>
              <p><strong className="text-white">R:</strong> Reset pose to default (T-Pose)<br /><strong className="text-white">W:</strong> Toggle gizmo wireframe balls</p>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 bg-dummyAccent hover:bg-dummyAccentHover text-white rounded-xl font-semibold text-sm transition"
        >
          Got It
        </button>
      </div>
    </div>
  );
};
