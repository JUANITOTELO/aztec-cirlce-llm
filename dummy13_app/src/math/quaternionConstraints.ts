import * as THREE from 'three';
import { JointConstraint } from '../types/dummy13';

const _tempVec = new THREE.Vector3();
const _tempEuler = new THREE.Euler(0, 0, 0, 'ZYX');

/**
 * Clamps a quaternion to physical anatomical joint limits avoiding gimbal locks and singular matrices.
 * Uses swing-twist decomposition for ball-and-socket joints and direct axis clamping for hinge joints.
 */
export function clampJointRotation(
  inputQuat: THREE.Quaternion,
  constraint: JointConstraint,
  referenceQuat: THREE.Quaternion = new THREE.Quaternion()
): THREE.Quaternion {
  const result = inputQuat.clone().normalize();

  if (constraint.type === 'root') {
    return result;
  }

  // For Hinge or Universal joints, compute clamped Euler representation with ZYX order
  if (constraint.type.startsWith('hinge') || constraint.type === 'universal') {
    _tempEuler.setFromQuaternion(result, 'XYZ');

    if (constraint.type === 'hinge_x') {
      _tempEuler.x = THREE.MathUtils.clamp(_tempEuler.x, constraint.minX, constraint.maxX);
      _tempEuler.y = 0;
      _tempEuler.z = 0;
    } else if (constraint.type === 'hinge_y') {
      _tempEuler.x = 0;
      _tempEuler.y = THREE.MathUtils.clamp(_tempEuler.y, constraint.minY, constraint.maxY);
      _tempEuler.z = 0;
    } else if (constraint.type === 'hinge_z') {
      _tempEuler.x = 0;
      _tempEuler.y = 0;
      _tempEuler.z = THREE.MathUtils.clamp(_tempEuler.z, constraint.minZ, constraint.maxZ);
    } else {
      // universal
      _tempEuler.x = THREE.MathUtils.clamp(_tempEuler.x, constraint.minX, constraint.maxX);
      _tempEuler.y = THREE.MathUtils.clamp(_tempEuler.y, constraint.minY, constraint.maxY);
      _tempEuler.z = THREE.MathUtils.clamp(_tempEuler.z, constraint.minZ, constraint.maxZ);
    }

    result.setFromEuler(_tempEuler);
    return result.normalize();
  }

  // Ball joint swing-twist decomposition along Z-axis (pointing down limb)
  if (constraint.type === 'ball') {
    const twistAxis = _tempVec.set(0, 1, 0);
    const { swing, twist } = decomposeSwingTwist(result, twistAxis);

    // Clamp twist angle
    const maxTwist = constraint.maxTwist || Math.PI * 0.75;
    let twistAngle = 2 * Math.atan2(twist.y, twist.w);
    if (twistAngle > Math.PI) twistAngle -= 2 * Math.PI;
    if (twistAngle < -Math.PI) twistAngle += 2 * Math.PI;
    const clampedTwistAngle = THREE.MathUtils.clamp(twistAngle, -maxTwist, maxTwist);
    twist.setFromAxisAngle(twistAxis, clampedTwistAngle);

    // Clamp swing cone
    const maxSwing = constraint.maxSwing || (constraint.maxX > 0 ? constraint.maxX : Math.PI * 0.5);
    const swingAxis = new THREE.Vector3(swing.x, swing.y, swing.z);
    const swingLen = swingAxis.length();
    if (swingLen > 0.0001) {
      swingAxis.normalize();
      let swingAngle = 2 * Math.acos(THREE.MathUtils.clamp(swing.w, -1, 1));
      if (swingAngle > Math.PI) swingAngle = 2 * Math.PI - swingAngle;
      const clampedSwingAngle = THREE.MathUtils.clamp(swingAngle, 0, maxSwing);
      swing.setFromAxisAngle(swingAxis, clampedSwingAngle);
    } else {
      swing.identity();
    }

    result.multiplyQuaternions(swing, twist);
    return result.normalize();
  }

  return result;
}

/**
 * Decomposes a rotation quaternion into Swing and Twist components with respect to an axis.
 */
export function decomposeSwingTwist(
  q: THREE.Quaternion,
  twistAxis: THREE.Vector3
): { swing: THREE.Quaternion; twist: THREE.Quaternion } {
  const axis = twistAxis.clone().normalize();
  const dot = q.x * axis.x + q.y * axis.y + q.z * axis.z;
  const twist = new THREE.Quaternion(axis.x * dot, axis.y * dot, axis.z * dot, q.w).normalize();
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
