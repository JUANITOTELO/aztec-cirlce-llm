import React, { useState, useRef, useCallback, useEffect } from 'react';
import * as THREE from 'three';
import { Viewport } from './components/Viewport';
import { Toolbar } from './components/Toolbar';
import { JointInspector } from './components/JointInspector';
import { ThemeCustomizer } from './components/ThemeCustomizer';
import { HelpModal } from './components/HelpModal';
import { ViewportEngine } from './engine/ViewportEngine';
import { POSE_PRESETS } from './engine/PresetLibrary';
import { JointId, MannequinTheme, GizmoMode, TransformSpace, PoseData } from './types/dummy13';

const DEFAULT_THEME: MannequinTheme = {
  name: 'Cyberpunk Neon',
  armorColor: '#0f172a',
  frameColor: '#334155',
  jointColor: '#0284c7',
  accentColor: '#00f0ff',
  roughness: 0.25,
  metalness: 0.8
};

export const App: React.FC = () => {
  const engineRef = useRef<ViewportEngine | null>(null);
  const [theme, setTheme] = useState<MannequinTheme>(DEFAULT_THEME);
  const [currentPoseId, setCurrentPoseId] = useState<string>(POSE_PRESETS[0].id);
  const [gizmoMode, setGizmoMode] = useState<GizmoMode>('rotate');
  const [gizmoSpace] = useState<TransformSpace>('local');
  const [selectedJointId, setSelectedJointId] = useState<JointId | null>(null);
  const [selectedJointRotation, setSelectedJointRotation] = useState<THREE.Quaternion>(new THREE.Quaternion());
  
  const [isThemeModalOpen, setIsThemeModalOpen] = useState<boolean>(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState<boolean>(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(true);

  const handleSelectPreset = useCallback((preset: PoseData) => {
    setCurrentPoseId(preset.id);
    if (engineRef.current) {
      engineRef.current.applyPose(preset.joints as any);
      if (selectedJointId) {
        setSelectedJointRotation(engineRef.current.rig.getJointRotation(selectedJointId));
      }
    }
  }, [selectedJointId]);

  const handleResetPose = useCallback(() => {
    if (engineRef.current) {
      engineRef.current.rig.resetPose();
      setCurrentPoseId('t_pose');
      if (selectedJointId) {
        setSelectedJointRotation(engineRef.current.rig.getJointRotation(selectedJointId));
      }
    }
  }, [selectedJointId]);
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        handleResetPose();
      } else if (e.key === 'w' || e.key === 'W') {
        e.preventDefault();
        if (engineRef.current) {
          engineRef.current.toggleWireframe();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleResetPose]);

  const handleMirrorPose = useCallback((side: 'left' | 'right') => {
    if (engineRef.current) {
      engineRef.current.rig.mirrorPose(side);
      if (selectedJointId) {
        setSelectedJointRotation(engineRef.current.rig.getJointRotation(selectedJointId));
      }
    }
  }, [selectedJointId]);

  const handleJointSelected = useCallback((jointId: JointId | null, rotation: THREE.Quaternion) => {
    setSelectedJointId(jointId);
    setSelectedJointRotation(rotation.clone());
  }, []);

  const handleJointUpdated = useCallback((jointId: JointId, rotation: THREE.Quaternion) => {
    if (selectedJointId === jointId) {
      setSelectedJointRotation(rotation.clone());
    }
  }, [selectedJointId]);

  const handleInspectorRotationChange = useCallback((jointId: JointId, quat: THREE.Quaternion) => {
    if (engineRef.current) {
      engineRef.current.rig.setJointRotation(jointId, quat);
      setSelectedJointRotation(quat);
    }
  }, []);

  const handleExportPose = useCallback(() => {
    if (!engineRef.current) return;
    const jointMap = engineRef.current.rig.jointNodes;
    const exportedJoints: PoseData['joints'] = {};

    jointMap.forEach((node, id) => {
      const q = node.quaternion;
      exportedJoints[id] = {
        rotation: { x: q.x, y: q.y, z: q.z, w: q.w },
        position: id === 'pelvis' ? { x: node.position.x, y: node.position.y, z: node.position.z } : undefined
      };
    });

    const poseData: PoseData = {
      id: `pose_${Date.now()}`,
      name: 'Custom Dummy 13 Pose',
      version: '1.0.0',
      timestamp: Date.now(),
      joints: exportedJoints
    };

    const blob = new Blob([JSON.stringify(poseData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dummy13-pose-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleImportPose = useCallback((pose: PoseData) => {
    if (engineRef.current) {
      engineRef.current.applyPose(pose.joints as any);
      setCurrentPoseId('custom_imported');
    }
  }, []);

  const handleCaptureScreenshot = useCallback(() => {
    if (!engineRef.current) return;
    const dataUrl = engineRef.current.captureScreenshot();
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `dummy13-render-${Date.now()}.png`;
    a.click();
  }, []);

  return (
    <main className="w-screen h-screen relative bg-dummyDark overflow-hidden select-none flex flex-col">
      <Toolbar
        currentPoseId={currentPoseId}
        gizmoMode={gizmoMode}
        onSelectPreset={handleSelectPreset}
        onResetPose={handleResetPose}
        onMirrorPose={handleMirrorPose}
        onSetGizmoMode={setGizmoMode}
        onExportPose={handleExportPose}
        onImportPose={handleImportPose}
        onCaptureScreenshot={handleCaptureScreenshot}
        onToggleThemeModal={() => setIsThemeModalOpen(true)}
        onToggleInspector={() => setIsInspectorOpen((prev) => !prev)}
        onToggleHelpModal={() => setIsHelpModalOpen(true)}
        isInspectorOpen={isInspectorOpen}
      />

      <div className="flex-1 w-full h-full relative">
        <Viewport
          theme={theme}
          gizmoMode={gizmoMode}
          gizmoSpace={gizmoSpace}
          currentPose={POSE_PRESETS[0]}
          onJointSelected={handleJointSelected}
          onJointUpdated={handleJointUpdated}
          engineRef={engineRef}
        />

        {isInspectorOpen && (
          <JointInspector
            selectedJointId={selectedJointId}
            rotation={selectedJointRotation}
            onUpdateRotation={handleInspectorRotationChange}
            onClose={() => setIsInspectorOpen(false)}
          />
        )}
      </div>

      {isThemeModalOpen && (
        <ThemeCustomizer
          theme={theme}
          onChangeTheme={setTheme}
          onClose={() => setIsThemeModalOpen(false)}
        />
      )}

      {isHelpModalOpen && (
        <HelpModal onClose={() => setIsHelpModalOpen(false)} />
      )}
    </main>
  );
};

export default App;
