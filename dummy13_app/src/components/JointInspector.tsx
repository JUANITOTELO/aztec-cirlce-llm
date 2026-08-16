import React from 'react';
import * as THREE from 'three';
import { JointId } from '../types/dummy13';
import { JOINT_DEFINITIONS } from '../engine/Dummy13Rig';
import { X, ShieldAlert } from 'lucide-react';

interface JointInspectorProps {
  selectedJointId: JointId | null;
  rotation: THREE.Quaternion;
  onUpdateRotation: (jointId: JointId, quat: THREE.Quaternion) => void;
  onClose: () => void;
}

export const JointInspector: React.FC<JointInspectorProps> = ({
  selectedJointId,
  rotation,
  onUpdateRotation,
  onClose
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
  const euler = new THREE.Euler().setFromQuaternion(rotation, 'XYZ');

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
            <span className="text-red-400 font-semibold">Pitch (X-Axis)</span>
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
            className="w-full accent-red-500 bg-dummyDark h-1.5 rounded-lg cursor-pointer disabled:opacity-30"
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
    </aside>
  );
};
