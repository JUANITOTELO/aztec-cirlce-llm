export type JointId =
  | 'root'
  | 'pelvis'
  | 'spine_lower'
  | 'spine_upper'
  | 'neck'
  | 'head'
  | 'clavicle_l'
  | 'shoulder_l'
  | 'elbow_l'
  | 'wrist_l'
  | 'hand_l'
  | 'clavicle_r'
  | 'shoulder_r'
  | 'elbow_r'
  | 'wrist_r'
  | 'hand_r'
  | 'hip_l'
  | 'knee_l'
  | 'ankle_l'
  | 'foot_l'
  | 'hip_r'
  | 'knee_r'
  | 'ankle_r'
  | 'foot_r';

export type JointType = 'ball' | 'hinge_x' | 'hinge_y' | 'hinge_z' | 'universal' | 'root';

export interface JointConstraint {
  type: JointType;
  minX: number; // in radians
  maxX: number;
  minY: number;
  maxY: number;
  minZ: number;
  maxZ: number;
  maxTwist?: number; // for ball joints
  maxSwing?: number; // cone angle in radians
}

export interface QuaternionData {
  x: number;
  y: number;
  z: number;
  w: number;
}

export interface Vector3Data {
  x: number;
  y: number;
  z: number;
}

export interface PoseJointState {
  rotation: QuaternionData;
  position?: Vector3Data; // Pelvis / Root offset
}

export interface PoseData {
  id: string;
  name: string;
  author?: string;
  version: string;
  timestamp: number;
  joints: Partial<Record<JointId, PoseJointState>>;
}

export interface MannequinTheme {
  name: string;
  armorColor: string;
  frameColor: string;
  jointColor: string;
  accentColor: string;
  roughness: number;
  metalness: number;
}

export type GizmoMode = 'rotate' | 'translate' | 'none';
export type TransformSpace = 'local' | 'world';

export interface JointDefinition {
  id: JointId;
  name: string;
  parentId: JointId | null;
  defaultOffset: [number, number, number];
  constraints: JointConstraint;
  side?: 'left' | 'right' | 'center';
}
