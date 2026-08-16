import React from 'react';
import * as THREE from 'three';
import { JointId } from '../types/dummy13';
import { JOINT_DEFINITIONS } from '../engine/Dummy13Rig';
import { X, ShieldAlert, Sliders, Lock } from 'lucide-react';

interface JointInspectorProps {
  selectedJointId: JointId | null;
  rotation: THREE.Quaternion;
  stiffness: number;
  onUpdateRotation: (jointId: JointId, quat: THREE.Quaternion) => void;
  onUpdateStiffness: (jointId: JointId, stiffness: number) => void;
  onApplyStiffnessToAll?: (stiffness: number) => void;
  onClose: () => void;
}

export const JointInspector: React.FC<JointInspectorProps> = ({
  selectedJointId,
  rotation,
  stiffness,
  onUpdateRotation,
  onUpdateStiffness,
  onApplyStiffnessToAll,
  onClose,
}) => {
  if (!selectedJointId) {
    return (
      <aside className="absolute bottom-5 right-5 w-80 p-4 bg-dummyPanel/90 backdrop-blur-md rounded-xl border border-dummyBorder shadow-2xl z-20 text-slate-400 text-xs flex items-center gap-3">
        <ShieldAlert className="w-5 h-5 text-dummyAccent shrink-0" />
        <span>Click any joint ball-handle on the mannequin in the viewport to inspect and clamp its angles.</span>
      </aside>
    );
  }

  const def = JOINT_DEFINITIONS[selectedJointId];
  const canonicalQuat = rotation.clone().normalize();
  if (canonicalQuat.w < 0) {
    canonicalQuat.set(-canonicalQuat.x, -canonicalQuat.y, -canonicalQuat.z, -canonicalQuat.w);
  }
  const euler = new THREE.Euler().setFromQuaternion(canonicalQuat, 'XYZ');

  const handleEulerChange = (axis: 'x' | 'y' | 'z', degrees: number) => {
    const rad = THREE.MathUtils.degToRad(degrees);
    const newEuler = euler.clone();
    newEuler[axis] = rad;
    const newQuat = new THREE.Quaternion().setFromEuler(newEuler);
    onUpdateRotation(selectedJointId, newQuat);
  };
  const degX = THREE.MathUtils.radToDeg(euler.x);
  const degY = THREE.MathUtils.radToDeg(euler.y);
  const degZ = THREE.MathUtils.radToDeg(euler.z);

  const minDegX = THREE.MathUtils.radToDeg(def.constraints.minX);
  const maxDegX = THREE.MathUtils.radToDeg(def.constraints.maxX);
  const minDegY = THREE.MathUtils.radToDeg(def.constraints.minY);
  const maxDegY = THREE.MathUtils.radToDeg(def.constraints.maxY);
  const minDegZ = THREE.MathUtils.radToDeg(def.constraints.minZ);
  const maxDegZ = THREE.MathUtils.radToDeg(def.constraints.maxZ);

  return (
    <aside className="absolute bottom-5 right-5 w-84 p-4 bg-dummyPanel/95 backdrop-blur-md rounded-xl border border-dummyBorder shadow-2xl z-20 text-slate-200">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-dummyBorder">
        <div>
          <h3 className="text-sm font-semibold text-white">{def.name}</h3>
          <span className="text-[11px] font-mono text-dummyAccent uppercase">
            Type: {def.constraints.type.replace('_', ' ')}
          </span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3">
        {/* Pitch (X) */}
        <div>
          <div className="flex justify-between text-xs font-mono mb-1">
            <span className="text-rose-400 font-semibold">Pitch (X-Axis)</span>
            <span>{degX.toFixed(1)}°</span>
          </div>
          <input
            type="range"
            min={minDegX}
            max={maxDegX}
            step={1}
            value={Math.round(degX)}
            onChange={(e) => handleEulerChange('x', parseFloat(e.target.value))}
            disabled={def.constraints.type === 'hinge_y' || def.constraints.type === 'hinge_z'}
            className="w-full accent-rose-500 bg-dummyDark h-1.5 rounded-lg cursor-pointer disabled:opacity-30"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>{minDegX.toFixed(0)}°</span>
            <span>{maxDegX.toFixed(0)}°</span>
          </div>
        </div>

        {/* Yaw (Y) */}
        <div>
          <div className="flex justify-between text-xs font-mono mb-1">
            <span className="text-emerald-400 font-semibold">Yaw (Y-Axis)</span>
            <span>{degY.toFixed(1)}°</span>
          </div>
          <input
            type="range"
            min={minDegY}
            max={maxDegY}
            step={1}
            value={Math.round(degY)}
            onChange={(e) => handleEulerChange('y', parseFloat(e.target.value))}
            disabled={def.constraints.type === 'hinge_x' || def.constraints.type === 'hinge_z'}
            className="w-full accent-emerald-500 bg-dummyDark h-1.5 rounded-lg cursor-pointer disabled:opacity-30"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>{minDegY.toFixed(0)}°</span>
            <span>{maxDegY.toFixed(0)}°</span>
          </div>
        </div>

        {/* Roll (Z) */}
        <div>
          <div className="flex justify-between text-xs font-mono mb-1">
            <span className="text-blue-400 font-semibold">Roll (Z-Axis)</span>
            <span>{degZ.toFixed(1)}°</span>
          </div>
          <input
            type="range"
            min={minDegZ}
            max={maxDegZ}
            step={1}
            value={Math.round(degZ)}
            onChange={(e) => handleEulerChange('z', parseFloat(e.target.value))}
            disabled={def.constraints.type === 'hinge_x' || def.constraints.type === 'hinge_y'}
            className="w-full accent-blue-500 bg-dummyDark h-1.5 rounded-lg cursor-pointer disabled:opacity-30"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>{minDegZ.toFixed(0)}°</span>
            <span>{maxDegZ.toFixed(0)}°</span>
          </div>
        </div>
      </div>

      {/* Joint Stiffness / Friction Section */}
      <div className="mt-4 pt-3 border-t border-dummyBorder/80 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-sky-300">
            <Sliders className="w-3.5 h-3.5" />
            <span>Joint Stiffness / Friction</span>
          </div>
          <span className="text-xs font-mono text-white">{Math.round(stiffness * 100)}%</span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={Math.round(stiffness * 100)}
          onChange={(e) => onUpdateStiffness(selectedJointId, parseFloat(e.target.value) / 100)}
          className="w-full accent-sky-400 bg-dummyDark h-1.5 rounded-lg cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-slate-400 font-mono">
          <span>Flaccid (0%)</span>
          <span>Firm (85%)</span>
          <span>Locked (100%)</span>
        </div>

        <div className="flex items-center gap-1.5 pt-1">
          <button
            type="button"
            onClick={() => onUpdateStiffness(selectedJointId, 0.0)}
            className={`flex-1 py-1 text-[11px] font-medium rounded transition ${
              stiffness === 0 ? 'bg-amber-500/20 border border-amber-500 text-amber-300' : 'bg-dummyDark/60 hover:bg-dummyDark text-slate-400 border border-transparent'
            }`}
          >
            Loose
          </button>
          <button
            type="button"
            onClick={() => onUpdateStiffness(selectedJointId, 0.85)}
            className={`flex-1 py-1 text-[11px] font-medium rounded transition ${
              stiffness >= 0.8 && stiffness < 1.0 ? 'bg-sky-500/20 border border-sky-500 text-sky-300' : 'bg-dummyDark/60 hover:bg-dummyDark text-slate-400 border border-transparent'
            }`}
          >
            Firm
          </button>
          <button
            type="button"
            onClick={() => onUpdateStiffness(selectedJointId, 1.0)}
            className={`flex-1 py-1 text-[11px] font-medium rounded transition ${
              stiffness === 1.0 ? 'bg-emerald-500/20 border border-emerald-500 text-emerald-300' : 'bg-dummyDark/60 hover:bg-dummyDark text-slate-400 border border-transparent'
            }`}
          >
            Rigid
          </button>
        </div>

        {onApplyStiffnessToAll && (
          <button
            type="button"
            onClick={() => onApplyStiffnessToAll(stiffness)}
            className="w-full mt-1.5 py-1 px-2 flex items-center justify-center gap-1.5 text-[11px] font-medium text-slate-300 bg-dummyDark/80 hover:bg-dummyBorder/80 border border-dummyBorder rounded transition"
          >
            <Lock className="w-3 h-3 text-sky-400" />
            Apply {Math.round(stiffness * 100)}% Stiffness to All Limbs
          </button>
        )}
      </div>
    </aside>
  );
};
