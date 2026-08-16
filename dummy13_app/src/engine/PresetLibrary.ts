import * as THREE from 'three';
import { PoseData } from '../types/dummy13';

export const POSE_PRESETS: PoseData[] = [
  {
    id: 't_pose',
    name: 'T-Pose (Default Calibration)',
    version: '1.0.0',
    timestamp: Date.now(),
    joints: {
      pelvis: { rotation: { x: 0, y: 0, z: 0, w: 1 }, position: { x: 0, y: 1.1, z: 0 } },
      spine_lower: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      spine_upper: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      head: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      shoulder_l: { rotation: new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), Math.PI / 2) },
      shoulder_r: { rotation: new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), -Math.PI / 2) },
      elbow_l: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      elbow_r: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      hip_l: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      hip_r: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      knee_l: { rotation: { x: 0, y: 0, z: 0, w: 1 } },
      knee_r: { rotation: { x: 0, y: 0, z: 0, w: 1 } }
    }
  },
  {
    id: 'hero_landing',
    name: 'Superhero 3-Point Landing',
    version: '1.0.0',
    timestamp: Date.now(),
    joints: {
      pelvis: { rotation: { x: 0.45, y: 0.1, z: 0, w: 0.88 }, position: { x: 0, y: 0.45, z: 0 } },
      spine_lower: { rotation: { x: 0.35, y: 0, z: 0, w: 0.93 } },
      spine_upper: { rotation: { x: 0.3, y: 0, z: 0, w: 0.95 } },
      neck: { rotation: { x: -0.4, y: 0, z: 0, w: 0.91 } },
      head: { rotation: { x: -0.3, y: 0, z: 0, w: 0.95 } },
      // Left punch ground arm
      shoulder_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.8, -0.2, 0.4)) },
      elbow_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.6, 0, 0)) },
      wrist_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.4, 0, 0)) },
      // Right poised back arm
      shoulder_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.9, 0.6, -0.6)) },
      elbow_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2, 0, 0)) },
      // Legs crouching
      hip_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2, 0.3, 0.3)) },
      knee_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-2.1, 0, 0)) },
      ankle_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.6, 0, 0)) },
      hip_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.5, -0.6, -0.8)) },
      knee_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-1.5, 0, 0)) },
      ankle_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.5, 0, 0)) }
    }
  },
  {
    id: 'martial_arts',
    name: 'Dragon Martial Arts Stance',
    version: '1.0.0',
    timestamp: Date.now(),
    joints: {
      pelvis: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0.6, 0)), position: { x: 0, y: 0.9, z: 0 } },
      spine_lower: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.1, -0.3, 0)) },
      spine_upper: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.1, -0.2, 0)) },
      head: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -0.2, 0)) },
      shoulder_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.6, 0.2, 0.9)) },
      elbow_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.4, 0, 0)) },
      shoulder_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.3, -0.5, -1.1)) },
      elbow_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.8, 0, 0)) },
      hip_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.8, 0.4, 0.2)) },
      knee_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-1.3, 0, 0)) },
      hip_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.4, -0.3, -0.5)) },
      knee_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.9, 0, 0)) }
    }
  },
  {
    id: 'sprint',
    name: 'Dynamic Sprint Action',
    version: '1.0.0',
    timestamp: Date.now(),
    joints: {
      pelvis: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.4, 0, 0)), position: { x: 0, y: 0.98, z: 0 } },
      spine_lower: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, -0.2, 0)) },
      spine_upper: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.1, 0.2, 0)) },
      shoulder_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-1.2, 0.2, 0.3)) },
      elbow_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.5, 0, 0)) },
      shoulder_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.9, -0.2, -0.3)) },
      elbow_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.7, 0, 0)) },
      hip_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2, 0, 0)) },
      knee_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-1.6, 0, 0)) },
      ankle_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.4, 0, 0)) },
      hip_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.9, 0, 0)) },
      knee_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.4, 0, 0)) },
      ankle_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.3, 0, 0)) }
    }
  },
  {
    id: 'zen_sit',
    name: 'Zen Meditation (Lotus)',
    version: '1.0.0',
    timestamp: Date.now(),
    joints: {
      pelvis: { rotation: { x: 0, y: 0, z: 0, w: 1 }, position: { x: 0, y: 0.28, z: 0 } },
      spine_lower: { rotation: { x: -0.05, y: 0, z: 0, w: 0.99 } },
      spine_upper: { rotation: { x: -0.05, y: 0, z: 0, w: 0.99 } },
      head: { rotation: { x: 0.1, y: 0, z: 0, w: 0.99 } },
      shoulder_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, 0, 0.4)) },
      elbow_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2, 0, 0)) },
      shoulder_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, 0, -0.4)) },
      elbow_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.2, 0, 0)) },
      hip_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.4, 0.8, 1.2)) },
      knee_l: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-2.4, 0, 0)) },
      hip_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(1.4, -0.8, -1.2)) },
      knee_r: { rotation: new THREE.Quaternion().setFromEuler(new THREE.Euler(-2.4, 0, 0)) }
    }
  }
];
