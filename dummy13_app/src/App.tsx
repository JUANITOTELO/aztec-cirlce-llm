import React, { useState, useRef, useCallback, useEffect } from 'react';
import * as THREE from 'three';
import { Viewport } from './components/Viewport';
import { Toolbar } from './components/Toolbar';
import { JointInspector } from './components/JointInspector';
import { ThemeCustomizer } from './components/ThemeCustomizer';
import { HelpModal } from './components/HelpModal';
import { SavedPosesModal } from './components/SavedPosesModal';
import { ViewportEngine } from './engine/ViewportEngine';
import { POSE_PRESETS } from './engine/PresetLibrary';
import { JointId, MannequinTheme, GizmoMode, TransformSpace, PoseData, SavedPoseRecord } from './types/dummy13';
import { dbService } from './services/db';

const DEFAULT_THEME: MannequinTheme = {
  name: 'Cyberpunk Neon',
  armorColor: '#0f172a',
  frameColor: '#334155',
  jointColor: '#0284c7',
  accentColor: '#00f0ff',
  roughness: 0.25,
  metalness: 0.8
};

const ToolbarComponent = Toolbar as React.ComponentType<any>;

export const App: React.FC = () => {
  const engineRef = useRef<ViewportEngine | null>(null);
  const [theme, setTheme] = useState<MannequinTheme>(DEFAULT_THEME);
  const [currentPoseId, setCurrentPoseId] = useState<string>(POSE_PRESETS[0].id);
  const [gizmoMode, setGizmoMode] = useState<GizmoMode>('rotate');
  const [gizmoSpace, setGizmoSpace] = useState<TransformSpace>('local');
  const [selectedJointId, setSelectedJointId] = useState<JointId | null>(null);
  const [selectedJointRotation, setSelectedJointRotation] = useState<THREE.Quaternion>(new THREE.Quaternion());
  const [selectedJointStiffness, setSelectedJointStiffness] = useState<number>(0.5);
  const [isGravityEnabled, setIsGravityEnabled] = useState<boolean>(false);
  
  const [isThemeModalOpen, setIsThemeModalOpen] = useState<boolean>(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState<boolean>(false);
  const [isSavedPosesOpen, setIsSavedPosesOpen] = useState<boolean>(false);
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
      const rig = engineRef.current.rig as any;
      if (typeof rig.resetPose === 'function') {
        rig.resetPose();
      } else {
        const tPose = POSE_PRESETS.find((p) => p.id === 't_pose');
        if (tPose) {
          engineRef.current.applyPose(tPose.joints as any);
        }
      }
      setCurrentPoseId('t_pose');
      if (selectedJointId) {
        setSelectedJointRotation(engineRef.current.rig.getJointRotation(selectedJointId));
      }
    }
  }, [selectedJointId]);

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const savedTheme = await dbService.getSetting<MannequinTheme>('current_theme');
        if (savedTheme) {
          setTheme(savedTheme);
        }

        const lastSessionPose = await dbService.getSetting<PoseData>('last_session_pose');
        if (lastSessionPose && engineRef.current) {
          engineRef.current.applyPose(lastSessionPose.joints as any);
          setCurrentPoseId(lastSessionPose.id || 'restored_session');
        }
      } catch (err) {
        console.error('Could not restore session from IndexedDB:', err);
      }
    };

    const timer = setTimeout(restoreSession, 250);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    dbService.setSetting('current_theme', theme).catch(() => {});
  }, [theme]);

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
          engineRef.current.toggleGizmoVisibility();
        }
      } else if (e.key === 'g' || e.key === 'G') {
        e.preventDefault();
        if (engineRef.current) {
          const next = engineRef.current.toggleGravity();
          setIsGravityEnabled(next);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleResetPose]);

  const handleToggleGravity = useCallback(() => {
    if (engineRef.current) {
      const next = engineRef.current.toggleGravity();
      setIsGravityEnabled(next);
    }
  }, []);

  const handleDropToFloor = useCallback(() => {
    if (engineRef.current) {
      const engine = engineRef.current as any;
      if (typeof engine.dropToFloor === 'function') {
        engine.dropToFloor();
      } else if (engine.rig && typeof engine.rig.dropToFloor === 'function') {
        engine.rig.dropToFloor();
      }
    }
  }, []);

  const handleMirrorPose = useCallback((side: 'left' | 'right') => {
    if (engineRef.current) {
      const rig = engineRef.current.rig as any;
      if (typeof rig.mirrorPose === 'function') {
        rig.mirrorPose(side);
      }
      if (selectedJointId) {
        setSelectedJointRotation(engineRef.current.rig.getJointRotation(selectedJointId));
      }
    }
  }, [selectedJointId]);

  const handleJointSelected = useCallback((jointId: JointId | null, rotation: THREE.Quaternion) => {
    setSelectedJointId(jointId);
    setSelectedJointRotation(rotation.clone());
    if (jointId && engineRef.current) {
      setSelectedJointStiffness(engineRef.current.rig.getJointStiffness(jointId));
    }
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

  const handleInspectorStiffnessChange = useCallback((jointId: JointId, val: number) => {
    if (engineRef.current) {
      engineRef.current.rig.setJointStiffness(jointId, val);
      setSelectedJointStiffness(val);
    }
  }, []);

  const handleApplyStiffnessToAll = useCallback((val: number) => {
    if (engineRef.current) {
      engineRef.current.rig.setAllJointStiffness(val);
      setSelectedJointStiffness(val);
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

  const handleSavePoseToDB = useCallback(async (poseName: string) => {
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

    let thumbnail: string | undefined;
    const engine = engineRef.current as any;
    if (typeof engine.captureScreenshot === 'function') {
      thumbnail = engine.captureScreenshot();
    } else if (engine.renderer && engine.scene && engine.camera) {
      engine.renderer.render(engine.scene, engine.camera);
      thumbnail = engine.renderer.domElement.toDataURL('image/jpeg', 0.6);
    }

    const newRecord: SavedPoseRecord = {
      id: `idb_pose_${Date.now()}`,
      name: poseName,
      version: '1.0.0',
      timestamp: Date.now(),
      joints: exportedJoints,
      thumbnail
    };

    await dbService.savePose(newRecord);
    await dbService.setSetting('last_session_pose', newRecord);
    setCurrentPoseId(newRecord.id);
  }, []);

  const handleApplySavedPose = useCallback((pose: SavedPoseRecord) => {
    if (engineRef.current) {
      engineRef.current.applyPose(pose.joints as any);
      setCurrentPoseId(pose.id);
      dbService.setSetting('last_session_pose', pose).catch(() => {});
      if (selectedJointId) {
        setSelectedJointRotation(engineRef.current.rig.getJointRotation(selectedJointId));
      }
    }
  }, [selectedJointId]);

  const handleImportPose = useCallback((pose: PoseData) => {
    if (engineRef.current) {
      engineRef.current.applyPose(pose.joints as any);
      setCurrentPoseId('custom_imported');
    }
  }, []);

  const handleCaptureScreenshot = useCallback(() => {
    if (!engineRef.current) return;
    const engine = engineRef.current as any;
    let dataUrl = '';
    if (typeof engine.captureScreenshot === 'function') {
      dataUrl = engine.captureScreenshot();
    } else if (engine.renderer && engine.scene && engine.camera) {
      engine.renderer.render(engine.scene, engine.camera);
      dataUrl = engine.renderer.domElement.toDataURL('image/png');
    }
    if (dataUrl) {
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `dummy13-render-${Date.now()}.png`;
      a.click();
    }
  }, []);

  return (
    <main className="w-screen h-screen relative bg-dummyDark overflow-hidden select-none flex flex-col">
      <ToolbarComponent
        currentPoseId={currentPoseId}
        gizmoMode={gizmoMode}
        gizmoSpace={gizmoSpace}
        onSelectPreset={handleSelectPreset}
        onResetPose={handleResetPose}
        onMirrorPose={handleMirrorPose}
        onSetGizmoMode={setGizmoMode}
        onSetGizmoSpace={setGizmoSpace}
        onExportPose={handleExportPose}
        onImportPose={handleImportPose}
        onCaptureScreenshot={handleCaptureScreenshot}
        isGravityEnabled={isGravityEnabled}
        onToggleGravity={handleToggleGravity}
        onDropToFloor={handleDropToFloor}
        isInspectorOpen={isInspectorOpen}
        onToggleInspector={() => setIsInspectorOpen((prev) => !prev)}
        onOpenTheme={() => setIsThemeModalOpen(true)}
        onOpenHelp={() => setIsHelpModalOpen(true)}
        onOpenSavedPoses={() => setIsSavedPosesOpen(true)}
      />

      <div className="flex-1 relative overflow-hidden">
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
            stiffness={selectedJointStiffness}
            onUpdateRotation={handleInspectorRotationChange}
            onUpdateStiffness={handleInspectorStiffnessChange}
            onApplyStiffnessToAll={handleApplyStiffnessToAll}
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

      <SavedPosesModal
        isOpen={isSavedPosesOpen}
        onClose={() => setIsSavedPosesOpen(false)}
        onApplyPose={handleApplySavedPose}
        onSaveCurrentPose={handleSavePoseToDB}
      />
    </main>
  );
};

export default App;
