import React, { useEffect, useRef } from 'react';
import { ViewportEngine } from '../engine/ViewportEngine';
import { JointId, MannequinTheme, GizmoMode, TransformSpace, PoseData } from '../types/dummy13';
import * as THREE from 'three';

interface ViewportProps {
  theme: MannequinTheme;
  gizmoMode: GizmoMode;
  gizmoSpace: TransformSpace;
  currentPose: PoseData | null;
  onJointSelected: (jointId: JointId | null, rotation: THREE.Quaternion) => void;
  onJointUpdated: (jointId: JointId, rotation: THREE.Quaternion) => void;
  engineRef: React.MutableRefObject<ViewportEngine | null>;
}

export const Viewport: React.FC<ViewportProps> = ({
  theme,
  gizmoMode,
  gizmoSpace,
  currentPose,
  onJointSelected,
  onJointUpdated,
  engineRef
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const engine = new ViewportEngine(containerRef.current, theme);
    engineRef.current = engine;

    engine.onJointSelected = (jointId) => {
      if (jointId) {
        const rot = engine.rig.getJointRotation(jointId);
        onJointSelected(jointId, rot);
      } else {
        onJointSelected(null, new THREE.Quaternion());
      }
    };

    engine.onJointChanged = (jointId, rotation) => {
      onJointUpdated(jointId, rotation);
    };

    if (currentPose) {
      engine.applyPose(currentPose.joints as any);
    }

    return () => {
      engine.dispose();
      engineRef.current = null;
    };
  }, []);

  // Prop update synchronizations
  useEffect(() => {
    if (engineRef.current) {
      const engine = engineRef.current as any;
      if (typeof engine.setTheme === 'function') {
        engine.setTheme(theme);
      } else if (typeof engine.rig?.updateTheme === 'function') {
        engine.rig.updateTheme(theme);
      } else if (typeof engine.rig?.setTheme === 'function') {
        engine.rig.setTheme(theme);
      }
    }
  }, [theme]);

  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setGizmoMode(gizmoMode);
    }
  }, [gizmoMode]);

  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setGizmoSpace(gizmoSpace);
    }
  }, [gizmoSpace]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative cursor-grab active:cursor-grabbing outline-none overflow-hidden"
    />
  );
};
