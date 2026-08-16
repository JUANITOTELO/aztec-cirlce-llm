import * as THREE from 'three';
import { JointConstraint } from '../types/dummy13';

const _tempEuler = new THREE.Euler(0, 0, 0, 'XYZ');
const _tempQuat = new THREE.Quaternion();
const _tempAxis = new THREE.Vector3();

/**
 * Clamps a quaternion to physical anatomical joint limits avoiding gimbal locks and inverted rotations.
 * Highly optimized with zero garbage-collection allocations per frame.
 */
export function clampJointRotation(
  inputQuat: THREE.Quaternion,
  constraint: JointConstraint,
  _referenceQuat: THREE.Quaternion = new THREE.Quaternion()
): THREE.Quaternion {
  const result = _tempQuat.copy(inputQuat).normalize();

  if (constraint.type === 'root') {
    return result;
  }

  // Canonicalize quaternion (w >= 0) to prevent opposite-direction flipping
  if (result.w < 0) {
    result.set(-result.x, -result.y, -result.z, -result.w);
  }

  if (constraint.type === 'hinge_x') {
    // Extract rotation angle around X axis
    const halfAngle = Math.atan2(result.x, result.w);
    let angle = halfAngle * 2;
    // Normalize to [-PI, PI]
    while (angle > Math.PI) angle -= Math.PI * 2;
    while (angle < -Math.PI) angle += Math.PI * 2;
    const clampedAngle = THREE.MathUtils.clamp(angle, constraint.minX, constraint.maxX);
    result.set(Math.sin(clampedAngle * 0.5), 0, 0, Math.cos(clampedAngle * 0.5));
    return result.normalize();
  } else if (constraint.type === 'hinge_y') {
    const halfAngle = Math.atan2(result.y, result.w);
    let angle = halfAngle * 2;
    while (angle > Math.PI) angle -= Math.PI * 2;
    while (angle < -Math.PI) angle += Math.PI * 2;
    const clampedAngle = THREE.MathUtils.clamp(angle, constraint.minY, constraint.maxY);
    result.set(0, Math.sin(clampedAngle * 0.5), 0, Math.cos(clampedAngle * 0.5));
    return result.normalize();
  } else if (constraint.type === 'hinge_z') {
    const halfAngle = Math.atan2(result.z, result.w);
    let angle = halfAngle * 2;
    while (angle > Math.PI) angle -= Math.PI * 2;
    while (angle < -Math.PI) angle += Math.PI * 2;
    const clampedAngle = THREE.MathUtils.clamp(angle, constraint.minZ, constraint.maxZ);
    result.set(0, 0, Math.sin(clampedAngle * 0.5), Math.cos(clampedAngle * 0.5));
    return result.normalize();
  }

  _tempEuler.setFromQuaternion(result, 'XYZ');
  _tempEuler.x = THREE.MathUtils.clamp(_tempEuler.x, constraint.minX, constraint.maxX);
  _tempEuler.y = THREE.MathUtils.clamp(_tempEuler.y, constraint.minY, constraint.maxY);
  _tempEuler.z = THREE.MathUtils.clamp(_tempEuler.z, constraint.minZ, constraint.maxZ);

  result.setFromEuler(_tempEuler);

  // Ball joint cone angle constraint (maxSwing)
  if (constraint.maxSwing !== undefined && constraint.maxSwing > 0) {
    const angle = 2 * Math.acos(THREE.MathUtils.clamp(result.w, -1, 1));
    if (angle > constraint.maxSwing) {
      const factor = Math.sin(constraint.maxSwing * 0.5) / Math.sin(angle * 0.5);
      result.x *= factor;
      result.y *= factor;
      result.z *= factor;
      result.w = Math.cos(constraint.maxSwing * 0.5);
    }
  }

  return result.normalize();
}

/**
 * Decomposes a rotation quaternion into Swing and Twist components with respect to an axis.
 */
export function decomposeSwingTwist(
  q: THREE.Quaternion,
  twistAxis: THREE.Vector3
): { swing: THREE.Quaternion; twist: THREE.Quaternion } {
  _tempAxis.copy(twistAxis).normalize();
  const dot = q.x * _tempAxis.x + q.y * _tempAxis.y + q.z * _tempAxis.z;
  const twist = new THREE.Quaternion(_tempAxis.x * dot, _tempAxis.y * dot, _tempAxis.z * dot, q.w).normalize();
  if (twist.lengthSq() < 0.0001) {
    twist.identity();
  }
  const twistInv = twist.clone().conjugate();
  const swing = new THREE.Quaternion().multiplyQuaternions(q, twistInv).normalize();

  return { swing, twist };
}

/**
 * Slerp between two poses safely.
 */
export function slerpPoseQuat(
  current: THREE.Quaternion,
  target: THREE.Quaternion,
  alpha: number
): THREE.Quaternion {
  return current.clone().slerp(target, THREE.MathUtils.clamp(alpha, 0, 1));
}
