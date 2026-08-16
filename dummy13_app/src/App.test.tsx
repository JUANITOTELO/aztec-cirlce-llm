import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { clampJointRotation, decomposeSwingTwist } from './math/quaternionConstraints';
import { JointConstraint } from './types/dummy13';
import { Dummy13Rig, JOINT_DEFINITIONS } from './engine/Dummy13Rig';

const MOCK_THEME = {
  name: 'Test',
  armorColor: '#ffffff',
  frameColor: '#000000',
  jointColor: '#ff0000',
  accentColor: '#00ffff',
  roughness: 0.5,
  metalness: 0.5
};

describe('Dummy 13 Rig & Kinematics Engine', () => {
  it('should initialize the full 24-joint bone hierarchy', () => {
    const rig = new Dummy13Rig(MOCK_THEME);
    expect(rig.jointNodes.size).toBe(Object.keys(JOINT_DEFINITIONS).length);
    expect(rig.jointNodes.has('head')).toBe(true);
    expect(rig.jointNodes.has('elbow_l')).toBe(true);
    expect(rig.jointNodes.has('knee_r')).toBe(true);
    rig.dispose();
  });

  it('should clamp hinge joints strictly along authorized 1-DOF axis without gimbal lock', () => {
    const constraint: JointConstraint = {
      type: 'hinge_x',
      minX: 0,
      maxX: 2.0,
      minY: 0,
      maxY: 0,
      minZ: 0,
      maxZ: 0
    };

    // Test extreme over-rotation (3.5 rad on X, 1.2 rad on Y)
    const rawQuat = new THREE.Quaternion().setFromEuler(new THREE.Euler(3.5, 1.2, -0.8, 'XYZ'));
    const clamped = clampJointRotation(rawQuat, constraint);
    const clampedEuler = new THREE.Euler().setFromQuaternion(clamped, 'XYZ');

    expect(clampedEuler.x).toBeLessThanOrEqual(2.001);
    expect(clampedEuler.x).toBeGreaterThanOrEqual(-0.001);
    expect(Math.abs(clampedEuler.y)).toBeLessThan(0.001);
    expect(Math.abs(clampedEuler.z)).toBeLessThan(0.001);
  });

  it('should correctly decompose swing and twist quaternions along an axis', () => {
    const axis = new THREE.Vector3(0, 1, 0);
    const inputQuat = new THREE.Quaternion().setFromAxisAngle(axis, Math.PI / 4);
    const { swing, twist } = decomposeSwingTwist(inputQuat, axis);

    expect(twist.w).toBeCloseTo(Math.cos(Math.PI / 8), 4);
    expect(swing.x).toBeCloseTo(0, 4);
  });

  it('should mirror bilateral poses between left and right limbs accurately', () => {
    const rig = new Dummy13Rig(MOCK_THEME);
    const testQuat = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.5, 0.2, -0.4));
    rig.setJointRotation('shoulder_l', testQuat);
    rig.mirrorPose('left');

    const mirroredQuat = rig.getJointRotation('shoulder_r');
    expect(mirroredQuat.x).toBeCloseTo(testQuat.x, 3);
    expect(mirroredQuat.y).toBeCloseTo(-testQuat.y, 3);
    rig.dispose();
  });
});
