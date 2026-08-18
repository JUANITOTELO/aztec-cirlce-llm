import * as THREE from 'three';
import { JointId, JointDefinition, MannequinTheme } from '../types/dummy13';
import { clampJointRotation } from '../math/quaternionConstraints';

export const JOINT_DEFINITIONS: Record<JointId, JointDefinition> = {
  root: {
    id: 'root',
    name: 'Root Base',
    parentId: null,
    defaultOffset: [0, 0, 0],
    constraints: { type: 'root', minX: -Math.PI, maxX: Math.PI, minY: -Math.PI, maxY: Math.PI, minZ: -Math.PI, maxZ: Math.PI },
    side: 'center',
    weight: 0
  },
  pelvis: {
    id: 'pelvis',
    name: 'Pelvis (Core)',
    parentId: 'root',
    defaultOffset: [0, 1.1, 0],
    constraints: { type: 'ball', minX: -0.4, maxX: 0.4, minY: -0.4, maxY: 0.4, minZ: -0.4, maxZ: 0.4, maxSwing: 0.5, maxTwist: 0.5 },
    side: 'center',
    weight: 3.5
  },
  spine_lower: {
    id: 'spine_lower',
    name: 'Lower Spine',
    parentId: 'pelvis',
    defaultOffset: [0, 0.22, 0],
    constraints: { type: 'ball', minX: -0.5, maxX: 0.5, minY: -0.4, maxY: 0.4, minZ: -0.3, maxZ: 0.3, maxSwing: 0.6, maxTwist: 0.4 },
    side: 'center',
    weight: 2.2
  },
  spine_upper: {
    id: 'spine_upper',
    name: 'Upper Chest',
    parentId: 'spine_lower',
    defaultOffset: [0, 0.26, 0],
    constraints: { type: 'ball', minX: -0.4, maxX: 0.4, minY: -0.4, maxY: 0.4, minZ: -0.3, maxZ: 0.3, maxSwing: 0.5, maxTwist: 0.4 },
    side: 'center',
    weight: 2.8
  },
  neck: {
    id: 'neck',
    name: 'Neck',
    parentId: 'spine_upper',
    defaultOffset: [0, 0.28, 0],
    constraints: { type: 'ball', minX: -0.5, maxX: 0.5, minY: -0.7, maxY: 0.7, minZ: -0.4, maxZ: 0.4, maxSwing: 0.6, maxTwist: 0.8 },
    side: 'center',
    weight: 0.6
  },
  head: {
    id: 'head',
    name: 'Head / Visor',
    parentId: 'neck',
    defaultOffset: [0, 0.16, 0],
    constraints: { type: 'ball', minX: -0.6, maxX: 0.6, minY: -1.0, maxY: 1.0, minZ: -0.4, maxZ: 0.4, maxSwing: 0.7, maxTwist: 1.0 },
    side: 'center',
    weight: 1.5
  },
  clavicle_l: {
    id: 'clavicle_l',
    name: 'Clavicle (L)',
    parentId: 'spine_upper',
    defaultOffset: [0.18, 0.18, 0],
    constraints: { type: 'universal', minX: -0.3, maxX: 0.3, minY: -0.3, maxY: 0.4, minZ: -0.4, maxZ: 0.4 },
    side: 'left',
    weight: 0.8
  },
  shoulder_l: {
    id: 'shoulder_l',
    name: 'Shoulder (L)',
    parentId: 'clavicle_l',
    defaultOffset: [0.18, 0, 0],
    constraints: { type: 'ball', minX: -Math.PI * 0.9, maxX: Math.PI * 0.9, minY: -Math.PI * 0.9, maxY: Math.PI * 0.9, minZ: -Math.PI * 0.9, maxZ: Math.PI * 0.9, maxSwing: Math.PI * 0.85, maxTwist: Math.PI * 0.8 },
    side: 'left',
    weight: 1.4
  },
  elbow_l: {
    id: 'elbow_l',
    name: 'Elbow (L)',
    parentId: 'shoulder_l',
    defaultOffset: [0, -0.35, 0],
    constraints: { type: 'hinge_x', minX: -0.05, maxX: 2.6, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'left',
    weight: 1.0
  },
  wrist_l: {
    id: 'wrist_l',
    name: 'Wrist (L)',
    parentId: 'elbow_l',
    defaultOffset: [0, -0.32, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.5, maxY: 0.5, minZ: -0.8, maxZ: 0.8, maxSwing: 0.9, maxTwist: 1.2 },
    side: 'left',
    weight: 0.5
  },
  hand_l: {
    id: 'hand_l',
    name: 'Hand (L)',
    parentId: 'wrist_l',
    defaultOffset: [0, -0.1, 0],
    constraints: { type: 'universal', minX: -0.5, maxX: 0.5, minY: -0.3, maxY: 0.3, minZ: -0.3, maxZ: 0.3 },
    side: 'left',
    weight: 0.3
  },
  clavicle_r: {
    id: 'clavicle_r',
    name: 'Clavicle (R)',
    parentId: 'spine_upper',
    defaultOffset: [-0.18, 0.18, 0],
    constraints: { type: 'universal', minX: -0.3, maxX: 0.3, minY: -0.4, maxY: 0.3, minZ: -0.4, maxZ: 0.4 },
    side: 'right',
    weight: 0.8
  },
  shoulder_r: {
    id: 'shoulder_r',
    name: 'Shoulder (R)',
    parentId: 'clavicle_r',
    defaultOffset: [-0.18, 0, 0],
    constraints: { type: 'ball', minX: -Math.PI * 0.9, maxX: Math.PI * 0.9, minY: -Math.PI * 0.9, maxY: Math.PI * 0.9, minZ: -Math.PI * 0.9, maxZ: Math.PI * 0.9, maxSwing: Math.PI * 0.85, maxTwist: Math.PI * 0.8 },
    side: 'right',
    weight: 1.4
  },
  elbow_r: {
    id: 'elbow_r',
    name: 'Elbow (R)',
    parentId: 'shoulder_r',
    defaultOffset: [0, -0.35, 0],
    constraints: { type: 'hinge_x', minX: -0.05, maxX: 2.6, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'right',
    weight: 1.0
  },
  wrist_r: {
    id: 'wrist_r',
    name: 'Wrist (R)',
    parentId: 'elbow_r',
    defaultOffset: [0, -0.32, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.5, maxY: 0.5, minZ: -0.8, maxZ: 0.8, maxSwing: 0.9, maxTwist: 1.2 },
    side: 'right',
    weight: 0.5
  },
  hand_r: {
    id: 'hand_r',
    name: 'Hand (R)',
    parentId: 'wrist_r',
    defaultOffset: [0, -0.1, 0],
    constraints: { type: 'universal', minX: -0.5, maxX: 0.5, minY: -0.3, maxY: 0.3, minZ: -0.3, maxZ: 0.3 },
    side: 'right',
    weight: 0.3
  },
  hip_l: {
    id: 'hip_l',
    name: 'Hip (L)',
    parentId: 'pelvis',
    defaultOffset: [0.18, -0.12, 0],
    constraints: { type: 'ball', minX: -1.6, maxX: 1.4, minY: -0.6, maxY: 0.6, minZ: -0.8, maxZ: 1.2, maxSwing: 1.6, maxTwist: 0.9 },
    side: 'left',
    weight: 3.0
  },
  knee_l: {
    id: 'knee_l',
    name: 'Knee (L)',
    parentId: 'hip_l',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'hinge_x', minX: -2.6, maxX: 0.05, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'left',
    weight: 2.0
  },
  ankle_l: {
    id: 'ankle_l',
    name: 'Ankle (L)',
    parentId: 'knee_l',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.4, maxY: 0.4, minZ: -0.5, maxZ: 0.5, maxSwing: 0.8, maxTwist: 0.5 },
    side: 'left',
    weight: 0.8
  },
  foot_l: {
    id: 'foot_l',
    name: 'Foot (L)',
    parentId: 'ankle_l',
    defaultOffset: [0, -0.08, 0.08],
    constraints: { type: 'hinge_x', minX: -0.3, maxX: 0.3, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'left',
    weight: 0.5
  },
  hip_r: {
    id: 'hip_r',
    name: 'Hip (R)',
    parentId: 'pelvis',
    defaultOffset: [-0.18, -0.12, 0],
    constraints: { type: 'ball', minX: -1.6, maxX: 1.4, minY: -0.6, maxY: 0.6, minZ: -1.2, maxZ: 0.8, maxSwing: 1.6, maxTwist: 0.9 },
    side: 'right',
    weight: 3.0
  },
  knee_r: {
    id: 'knee_r',
    name: 'Knee (R)',
    parentId: 'hip_r',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'hinge_x', minX: -2.6, maxX: 0.05, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'right',
    weight: 2.0
  },
  ankle_r: {
    id: 'ankle_r',
    name: 'Ankle (R)',
    parentId: 'knee_r',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.4, maxY: 0.4, minZ: -0.5, maxZ: 0.5, maxSwing: 0.8, maxTwist: 0.5 },
    side: 'right',
    weight: 0.8
  },
  foot_r: {
    id: 'foot_r',
    name: 'Foot (R)',
    parentId: 'ankle_r',
    defaultOffset: [0, -0.08, 0.08],
    constraints: { type: 'hinge_x', minX: -0.3, maxX: 0.3, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'right',
    weight: 0.5
  }
};

const _gravityDir = new THREE.Vector3(0, -9.81, 0);
const _parentWorldQuat = new THREE.Quaternion();
const _invParentWorldQuat = new THREE.Quaternion();
const _gParent = new THREE.Vector3();
const _rParent = new THREE.Vector3();
const _torqueAxis = new THREE.Vector3();
const _deltaQuat = new THREE.Quaternion();
const _qNext = new THREE.Quaternion();
const _tempBox = new THREE.Box3();
const _comVec = new THREE.Vector3();
const _qDiff = new THREE.Quaternion();
const _qInvCurrent = new THREE.Quaternion();
const _springTorque = new THREE.Vector3();
const _gravTorque = new THREE.Vector3();
const _totalTorque = new THREE.Vector3();

const PHYSICS_JOINT_ORDER: JointId[] = [
  'spine_lower',
  'spine_upper',
  'neck',
  'head',
  'clavicle_l',
  'shoulder_l',
  'elbow_l',
  'wrist_l',
  'hand_l',
  'clavicle_r',
  'shoulder_r',
  'elbow_r',
  'wrist_r',
  'hand_r',
  'hip_l',
  'knee_l',
  'ankle_l',
  'foot_l',
  'hip_r',
  'knee_r',
  'ankle_r',
  'foot_r'
];

const SUBTREE_MASS: Record<JointId, number> = {
  root: 0,
  pelvis: 18.0,
  spine_lower: 13.5,
  spine_upper: 11.3,
  neck: 2.1,
  head: 1.5,
  clavicle_l: 3.8,
  shoulder_l: 3.2,
  elbow_l: 1.8,
  wrist_l: 0.8,
  hand_l: 0.3,
  clavicle_r: 3.8,
  shoulder_r: 3.2,
  elbow_r: 1.8,
  wrist_r: 0.8,
  hand_r: 0.3,
  hip_l: 6.3,
  knee_l: 3.3,
  ankle_l: 1.3,
  foot_l: 0.5,
  hip_r: 6.3,
  knee_r: 3.3,
  ankle_r: 1.3,
  foot_r: 0.5
};

export class Dummy13Rig {
  public rootGroup: THREE.Group;
  public jointNodes: Map<JointId, THREE.Group> = new Map();
  public jointMeshMap: Map<JointId, THREE.Mesh[]> = new Map();
  public armorMeshes: THREE.Mesh[] = [];
  public frameMeshes: THREE.Mesh[] = [];
  public solidMeshes: THREE.Mesh[] = [];
  public jointSpheres: Map<JointId, THREE.Mesh> = new Map();
  public hitHandles: Map<JointId, THREE.Mesh> = new Map();
  
  public jointStiffness: Map<JointId, number> = new Map();
  public targetRotations: Map<JointId, THREE.Quaternion> = new Map();
  public jointAngularVelocity: Map<JointId, THREE.Vector3> = new Map();
  private armorMaterial: THREE.MeshStandardMaterial;
  private frameMaterial: THREE.MeshStandardMaterial;
  private jointMaterial: THREE.MeshStandardMaterial;
  private visorMaterial: THREE.MeshStandardMaterial;
  private handleMaterial: THREE.MeshBasicMaterial;
  private selectedHandleMaterial: THREE.MeshBasicMaterial;
  private hoveredHandleMaterial: THREE.MeshBasicMaterial;

  public currentTheme: MannequinTheme;
  private selectedJointId: JointId | null = null;
  private hoveredJointId: JointId | null = null;

  constructor(theme: MannequinTheme) {
    this.currentTheme = theme;
    this.rootGroup = new THREE.Group();
    this.rootGroup.name = 'Dummy13_Rig';

    this.armorMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color(theme.armorColor),
      roughness: theme.roughness,
      metalness: theme.metalness,
      polygonOffset: true,
      polygonOffsetFactor: 1,
      polygonOffsetUnits: 1
    });

    this.frameMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color(theme.frameColor),
      roughness: 0.65,
      metalness: 0.2
    });

    this.jointMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color(theme.jointColor),
      roughness: 0.4,
      metalness: 0.1
    });

    this.visorMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color(theme.accentColor),
      emissive: new THREE.Color(theme.accentColor),
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.8
    });

    this.handleMaterial = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
      depthTest: false,
      depthWrite: false
    });

    this.selectedHandleMaterial = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      wireframe: true,
      transparent: true,
      opacity: 0.95,
      depthTest: false,
      depthWrite: false
    });

    this.hoveredHandleMaterial = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      wireframe: true,
      transparent: true,
      opacity: 0.9,
      depthTest: false,
      depthWrite: false
    });

    Object.values(JOINT_DEFINITIONS).forEach((def) => {
      this.jointStiffness.set(def.id, 0.9);
      this.targetRotations.set(def.id, new THREE.Quaternion());
      this.jointAngularVelocity.set(def.id, new THREE.Vector3(0, 0, 0));
    });

    this.buildSkeletonHierarchy();
    this.generateDummy13Geometry();
    this.cacheSolidMeshes();
  }

  private buildSkeletonHierarchy(): void {
    Object.values(JOINT_DEFINITIONS).forEach((def) => {
      const jointNode = new THREE.Group();
      jointNode.name = `joint_${def.id}`;
      jointNode.position.set(...def.defaultOffset);
      this.jointNodes.set(def.id, jointNode);
    });

    Object.values(JOINT_DEFINITIONS).forEach((def) => {
      const jointNode = this.jointNodes.get(def.id)!;
      if (def.parentId === null) {
        this.rootGroup.add(jointNode);
      } else {
        const parentNode = this.jointNodes.get(def.parentId);
        if (parentNode) {
          parentNode.add(jointNode);
        }
      }
    });
  }

  private generateDummy13Geometry(): void {
    const pelvisNode = this.jointNodes.get('pelvis')!;
    const pelvisFrame = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.12, 0.16, 8), this.frameMaterial);
    pelvisFrame.castShadow = true;
    pelvisNode.add(pelvisFrame);
    this.frameMeshes.push(pelvisFrame);

    const pelvisArmor = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.14, 0.22), this.armorMaterial);
    pelvisArmor.position.set(0, 0.02, 0);
    pelvisArmor.castShadow = true;
    pelvisNode.add(pelvisArmor);
    this.armorMeshes.push(pelvisArmor);
    this.attachHandle(pelvisNode, 'pelvis', 0.2);

    const spineLNode = this.jointNodes.get('spine_lower')!;
    const abFrame = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.12, 0.18, 8), this.frameMaterial);
    abFrame.position.set(0, 0.09, 0);
    abFrame.castShadow = true;
    spineLNode.add(abFrame);
    this.frameMeshes.push(abFrame);

    const abArmor = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.15, 0.18), this.armorMaterial);
    abArmor.position.set(0, 0.09, 0.02);
    abArmor.castShadow = true;
    spineLNode.add(abArmor);
    this.armorMeshes.push(abArmor);
    this.attachHandle(spineLNode, 'spine_lower', 0.16);

    const spineUNode = this.jointNodes.get('spine_upper')!;
    const chestArmor = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.24, 0.24), this.armorMaterial);
    chestArmor.position.set(0, 0.12, 0);
    chestArmor.castShadow = true;
    spineUNode.add(chestArmor);
    this.armorMeshes.push(chestArmor);

    const chestPlate = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.16, 0.04), this.frameMaterial);
    chestPlate.position.set(0, 0.13, 0.11);
    spineUNode.add(chestPlate);
    this.frameMeshes.push(chestPlate);

    const backPlate = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.16, 0.04), this.frameMaterial);
    backPlate.position.set(0, 0.13, -0.11);
    spineUNode.add(backPlate);
    this.frameMeshes.push(backPlate);

    const neckNode = this.jointNodes.get('neck')!;
    const neckMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.14, 8), this.frameMaterial);
    neckMesh.position.set(0, 0.07, 0);
    neckNode.add(neckMesh);
    this.frameMeshes.push(neckMesh);
    this.attachHandle(neckNode, 'neck', 0.12);

    const headNode = this.jointNodes.get('head')!;
    const headBase = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.24, 0.22), this.armorMaterial);
    headBase.position.set(0, 0.12, 0);
    headBase.castShadow = true;
    headNode.add(headBase);
    this.armorMeshes.push(headBase);

    const visorMesh = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.08, 0.08), this.visorMaterial);
    visorMesh.position.set(0, 0.14, 0.11);
    headNode.add(visorMesh);
    this.attachHandle(headNode, 'head', 0.18);

    this.buildLimb('l', 1);
    this.buildLimb('r', -1);
    this.buildLeg('l', 1);
    this.buildLeg('r', -1);
  }

  private buildLimb(side: 'l' | 'r', dir: number): void {
    const clavNode = this.jointNodes.get(`clavicle_${side}` as JointId)!;
    const clavMesh = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), this.jointMaterial);
    clavNode.add(clavMesh);
    this.attachHandle(clavNode, `clavicle_${side}` as JointId, 0.1);

    const shNode = this.jointNodes.get(`shoulder_${side}` as JointId)!;
    const shPad = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.18, 0.18), this.armorMaterial);
    shPad.position.set(0.02 * dir, -0.05, 0);
    shPad.castShadow = true;
    shNode.add(shPad);
    this.armorMeshes.push(shPad);

    const bicepMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.28, 8), this.frameMaterial);
    bicepMesh.position.set(0, -0.18, 0);
    bicepMesh.castShadow = true;
    shNode.add(bicepMesh);
    this.frameMeshes.push(bicepMesh);
    this.attachHandle(shNode, `shoulder_${side}` as JointId, 0.14);

    const elNode = this.jointNodes.get(`elbow_${side}` as JointId)!;
    const elJoint = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.12, 12), this.jointMaterial);
    elJoint.rotation.z = Math.PI / 2;
    elNode.add(elJoint);

    const forearmMesh = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.26, 0.14), this.armorMaterial);
    forearmMesh.position.set(0, -0.16, 0);
    forearmMesh.castShadow = true;
    elNode.add(forearmMesh);
    this.armorMeshes.push(forearmMesh);
    this.attachHandle(elNode, `elbow_${side}` as JointId, 0.14);

    const wrNode = this.jointNodes.get(`wrist_${side}` as JointId)!;
    const handMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.14, 0.06), this.frameMaterial);
    handMesh.position.set(0, -0.07, 0);
    wrNode.add(handMesh);
    this.frameMeshes.push(handMesh);
    this.attachHandle(wrNode, `wrist_${side}` as JointId, 0.12);
  }

  private buildLeg(side: 'l' | 'r', _dir: number): void {
    const hipNode = this.jointNodes.get(`hip_${side}` as JointId)!;
    const hipSphere = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 12), this.jointMaterial);
    hipNode.add(hipSphere);

    const thighArmor = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.36, 0.2), this.armorMaterial);
    thighArmor.position.set(0, -0.22, 0);
    thighArmor.castShadow = true;
    hipNode.add(thighArmor);
    this.armorMeshes.push(thighArmor);
    this.attachHandle(hipNode, `hip_${side}` as JointId, 0.18);

    const kneeNode = this.jointNodes.get(`knee_${side}` as JointId)!;
    const kneeJoint = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.14, 12), this.jointMaterial);
    kneeJoint.rotation.z = Math.PI / 2;
    kneeNode.add(kneeJoint);

    const shinArmor = new THREE.Mesh(new THREE.BoxGeometry(0.17, 0.36, 0.18), this.armorMaterial);
    shinArmor.position.set(0, -0.22, 0.01);
    shinArmor.castShadow = true;
    kneeNode.add(shinArmor);
    this.armorMeshes.push(shinArmor);
    this.attachHandle(kneeNode, `knee_${side}` as JointId, 0.18);

    const ankleNode = this.jointNodes.get(`ankle_${side}` as JointId)!;
    const ankleJoint = new THREE.Mesh(new THREE.SphereGeometry(0.07, 12, 12), this.jointMaterial);
    ankleNode.add(ankleJoint);

    const footMesh = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.08, 0.28), this.armorMaterial);
    footMesh.position.set(0, -0.04, 0.06);
    footMesh.castShadow = true;
    ankleNode.add(footMesh);
    this.armorMeshes.push(footMesh);
    this.attachHandle(ankleNode, `ankle_${side}` as JointId, 0.14);
  }

  private attachHandle(node: THREE.Group, jointId: JointId, radius: number): void {
    const handle = new THREE.Mesh(
      new THREE.SphereGeometry(radius, 14, 10),
      this.handleMaterial
    );
    handle.userData = { isJointHandle: true, jointId };
    handle.renderOrder = 9999;
    node.add(handle);
    this.hitHandles.set(jointId, handle);
  }

  public setHandlesVisible(visible: boolean): void {
    this.hitHandles.forEach((handle) => {
      handle.visible = visible;
    });
  }

  public setJointRotation(jointId: JointId, quaternion: THREE.Quaternion, updateTarget: boolean = true): void {
    const node = this.jointNodes.get(jointId);
    const def = JOINT_DEFINITIONS[jointId];
    if (node && def) {
      const clamped = clampJointRotation(quaternion, def.constraints);
      node.quaternion.copy(clamped);
      if (updateTarget) {
        const target = this.targetRotations.get(jointId);
        if (target) {
          target.copy(clamped);
        }
        const vel = this.jointAngularVelocity.get(jointId);
        if (vel) vel.set(0, 0, 0);
      }
    }
  }

  public getJointRotation(jointId: JointId): THREE.Quaternion {
    const node = this.jointNodes.get(jointId);
    return node ? node.quaternion.clone() : new THREE.Quaternion();
  }

  public setJointStiffness(jointId: JointId, stiffness: number): void {
    this.jointStiffness.set(jointId, Math.max(0, Math.min(1, stiffness)));
  }

  public getJointStiffness(jointId: JointId): number {
    return this.jointStiffness.get(jointId) ?? 0.85;
  }

  public setAllJointStiffness(stiffness: number): void {
    const clamped = Math.max(0, Math.min(1, stiffness));
    Object.keys(JOINT_DEFINITIONS).forEach((id) => {
      this.jointStiffness.set(id as JointId, clamped);
    });
  }

  public setJointPosition(jointId: JointId, position: THREE.Vector3): void {
    if (jointId !== 'pelvis' && jointId !== 'root') {
      return;
    }
    const node = this.jointNodes.get(jointId);
    if (node) {
      node.position.copy(position);
    }
  }

  public getJointPosition(jointId: JointId): THREE.Vector3 {
    const node = this.jointNodes.get(jointId);
    return node ? node.position.clone() : new THREE.Vector3();
  }

  public selectJoint(jointId: JointId | null): void {
    if (this.selectedJointId && this.hitHandles.has(this.selectedJointId)) {
      this.hitHandles.get(this.selectedJointId)!.material = this.handleMaterial;
    }
    this.selectedJointId = jointId;
    if (jointId && this.hitHandles.has(jointId)) {
      this.hitHandles.get(jointId)!.material = this.selectedHandleMaterial;
    }
  }

  public hoverJoint(jointId: JointId | null): void {
    if (this.hoveredJointId && this.hoveredJointId !== this.selectedJointId) {
      if (this.hitHandles.has(this.hoveredJointId)) {
        this.hitHandles.get(this.hoveredJointId)!.material = this.handleMaterial;
      }
    }
    this.hoveredJointId = jointId;
    if (jointId && jointId !== this.selectedJointId) {
      if (this.hitHandles.has(jointId)) {
        this.hitHandles.get(jointId)!.material = this.hoveredHandleMaterial;
      }
    }
  }

  public applyPose(pose: { joints?: Record<string, { rotation?: THREE.Quaternion | { x: number; y: number; z: number; w: number }; position?: { x: number; y: number; z: number } }> }, updateTargets: boolean = true): void {
    if (!pose || !pose.joints) return;
    Object.entries(pose.joints).forEach(([jointId, jointData]) => {
      const id = jointId as JointId;
      if (jointData.rotation) {
        let quat: THREE.Quaternion;
        if (jointData.rotation instanceof THREE.Quaternion) {
          quat = jointData.rotation;
        } else {
          const r = jointData.rotation as any;
          quat = new THREE.Quaternion(r._x ?? r.x ?? 0, r._y ?? r.y ?? 0, r._z ?? r.z ?? 0, r._w ?? r.w ?? 1);
        }
        this.setJointRotation(id, quat, updateTargets);
      }
      if (jointData.position && (id === 'pelvis' || id === 'root')) {
        this.setJointPosition(id, new THREE.Vector3(jointData.position.x, jointData.position.y, jointData.position.z));
      }
    });
    this.rootGroup.updateMatrixWorld(true);
  }

  private cacheSolidMeshes(): void {
    this.solidMeshes = [...this.armorMeshes, ...this.frameMeshes];
  }

  public applyGravitySag(dt: number, excludedJoint?: JointId | null): void {
    const clampedDt = Math.min(dt, 0.066);
    const maxSubDt = 0.016;
    const subSteps = Math.max(1, Math.ceil(clampedDt / maxSubDt));
    const subDt = clampedDt / subSteps;

    for (let step = 0; step < subSteps; step++) {
      for (let j = 0; j < PHYSICS_JOINT_ORDER.length; j++) {
        const id = PHYSICS_JOINT_ORDER[j];
        if (id === excludedJoint) continue;

        const def = JOINT_DEFINITIONS[id];
        const node = this.jointNodes.get(id);
        if (!node || !def) continue;

        const stiffness = this.getJointStiffness(id);
        const angVel = this.jointAngularVelocity.get(id);
        if (!angVel) continue;

        const targetQuat = this.targetRotations.get(id) || new THREE.Quaternion();

        if (stiffness >= 0.999) {
          node.quaternion.copy(targetQuat);
          angVel.set(0, 0, 0);
          continue;
        }

        const compliance = Math.max(0, 1 - stiffness);
        const effectiveMass = SUBTREE_MASS[id] ?? (def.weight || 1.0);

        _qInvCurrent.copy(node.quaternion).invert();
        _qDiff.multiplyQuaternions(targetQuat, _qInvCurrent);
        if (_qDiff.w < 0) {
          _qDiff.set(-_qDiff.x, -_qDiff.y, -_qDiff.z, -_qDiff.w);
        }

        const halfAngle = Math.acos(THREE.MathUtils.clamp(_qDiff.w, -1, 1));
        const diffAngle = 2 * halfAngle;
        _springTorque.set(0, 0, 0);

        if (diffAngle > 0.0001) {
          const sinHalf = Math.sin(halfAngle);
          if (sinHalf > 0.0001) {
            _springTorque.set(_qDiff.x / sinHalf, _qDiff.y / sinHalf, _qDiff.z / sinHalf);
            const springK = (stiffness * stiffness * 180.0) + (stiffness * 40.0);
            _springTorque.multiplyScalar(diffAngle * springK);
          }
        }

        if (node.parent) {
          node.parent.getWorldQuaternion(_parentWorldQuat);
          _invParentWorldQuat.copy(_parentWorldQuat).invert();
          _gParent.copy(_gravityDir).applyQuaternion(_invParentWorldQuat);
        } else {
          _gParent.copy(_gravityDir);
        }

        _comVec.set(0, -0.15, 0);
        if (id.startsWith('clavicle_l')) _comVec.set(0.09, 0, 0);
        else if (id.startsWith('clavicle_r')) _comVec.set(-0.09, 0, 0);
        else if (id.startsWith('shoulder')) _comVec.set(0, -0.18, 0);
        else if (id.startsWith('elbow')) _comVec.set(0, -0.16, 0);
        else if (id.startsWith('wrist')) _comVec.set(0, -0.05, 0);
        else if (id.startsWith('hand')) _comVec.set(0, -0.06, 0);
        else if (id.startsWith('hip')) _comVec.set(0, -0.22, 0);
        else if (id.startsWith('knee')) _comVec.set(0, -0.22, 0);
        else if (id.startsWith('ankle')) _comVec.set(0, -0.04, 0.04);
        else if (id.startsWith('foot')) _comVec.set(0, -0.02, 0.06);
        else if (id === 'head') _comVec.set(0, 0.12, 0);
        else if (id === 'neck') _comVec.set(0, 0.08, 0);
        else if (id === 'spine_upper') _comVec.set(0, 0.13, 0);
        else if (id === 'spine_lower') _comVec.set(0, 0.11, 0);

        _rParent.copy(_comVec).applyQuaternion(node.quaternion);
        _gravTorque.crossVectors(_rParent, _gParent).multiplyScalar(effectiveMass * compliance);

        _totalTorque.addVectors(_springTorque, _gravTorque);
        const momentOfInertia = Math.max(0.05, effectiveMass * 0.12);
        angVel.addScaledVector(_totalTorque.divideScalar(momentOfInertia), subDt);

        const friction = 18.0 * (0.2 + stiffness * 0.8);
        const dampingFactor = Math.exp(-friction * subDt);
        angVel.multiplyScalar(dampingFactor);

        const speed = angVel.length();
        if (speed > 0.0001) {
          const sagAngle = Math.min(speed * subDt, 0.35);
          _torqueAxis.copy(angVel).multiplyScalar(1 / speed);
          _deltaQuat.setFromAxisAngle(_torqueAxis, sagAngle);
          _qNext.multiplyQuaternions(_deltaQuat, node.quaternion);
          const clamped = clampJointRotation(_qNext, def.constraints);
          node.quaternion.copy(clamped);
        }
      }
    }
  }

  public getLowestY(): number {
    _tempBox.makeEmpty();
    this.rootGroup.updateMatrixWorld(true);
    for (const mesh of this.solidMeshes) {
      _tempBox.expandByObject(mesh);
    }
    return _tempBox.isEmpty() ? 0 : _tempBox.min.y;
  }

  public clampToFloor(): void {
    this.rootGroup.updateMatrixWorld(true);
    const lowest = this.getLowestY();
    if (lowest < 0) {
      const pelvis = this.jointNodes.get('pelvis');
      if (pelvis) {
        pelvis.position.y -= lowest;
        this.rootGroup.updateMatrixWorld(true);
      }
    }
  }

  public dropToFloor(): void {
    this.rootGroup.updateMatrixWorld(true);
    const lowest = this.getLowestY();
    const pelvis = this.jointNodes.get('pelvis');
    if (pelvis && Number.isFinite(lowest)) {
      pelvis.position.y -= lowest;
      this.rootGroup.updateMatrixWorld(true);
    }
  }

  public setTheme(theme: MannequinTheme): void {
    this.currentTheme = theme;
    this.armorMaterial.color.set(theme.armorColor);
    this.armorMaterial.roughness = theme.roughness;
    this.armorMaterial.metalness = theme.metalness;
    this.frameMaterial.color.set(theme.frameColor);
    this.jointMaterial.color.set(theme.jointColor);
    this.visorMaterial.color.set(theme.accentColor);
    this.visorMaterial.emissive.set(theme.accentColor);
  }

  public dispose(): void {
    this.rootGroup.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        if (obj.geometry) {
          obj.geometry.dispose();
        }
      }
    });
    this.armorMaterial.dispose();
    this.frameMaterial.dispose();
    this.jointMaterial.dispose();
    this.visorMaterial.dispose();
    this.handleMaterial.dispose();
    this.selectedHandleMaterial.dispose();
    this.hoveredHandleMaterial.dispose();
  }
}
