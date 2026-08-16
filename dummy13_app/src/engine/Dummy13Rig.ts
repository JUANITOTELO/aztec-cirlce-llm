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
    side: 'center'
  },
  pelvis: {
    id: 'pelvis',
    name: 'Pelvis (Core)',
    parentId: 'root',
    defaultOffset: [0, 1.1, 0],
    constraints: { type: 'ball', minX: -0.4, maxX: 0.4, minY: -0.4, maxY: 0.4, minZ: -0.4, maxZ: 0.4, maxSwing: 0.5, maxTwist: 0.5 },
    side: 'center'
  },
  spine_lower: {
    id: 'spine_lower',
    name: 'Lower Spine',
    parentId: 'pelvis',
    defaultOffset: [0, 0.22, 0],
    constraints: { type: 'ball', minX: -0.5, maxX: 0.5, minY: -0.4, maxY: 0.4, minZ: -0.3, maxZ: 0.3, maxSwing: 0.6, maxTwist: 0.4 },
    side: 'center'
  },
  spine_upper: {
    id: 'spine_upper',
    name: 'Upper Chest',
    parentId: 'spine_lower',
    defaultOffset: [0, 0.26, 0],
    constraints: { type: 'ball', minX: -0.4, maxX: 0.4, minY: -0.4, maxY: 0.4, minZ: -0.3, maxZ: 0.3, maxSwing: 0.5, maxTwist: 0.4 },
    side: 'center'
  },
  neck: {
    id: 'neck',
    name: 'Neck',
    parentId: 'spine_upper',
    defaultOffset: [0, 0.28, 0],
    constraints: { type: 'ball', minX: -0.5, maxX: 0.5, minY: -0.7, maxY: 0.7, minZ: -0.4, maxZ: 0.4, maxSwing: 0.6, maxTwist: 0.8 },
    side: 'center'
  },
  head: {
    id: 'head',
    name: 'Head / Visor',
    parentId: 'neck',
    defaultOffset: [0, 0.16, 0],
    constraints: { type: 'ball', minX: -0.6, maxX: 0.6, minY: -1.0, maxY: 1.0, minZ: -0.4, maxZ: 0.4, maxSwing: 0.7, maxTwist: 1.0 },
    side: 'center'
  },
  // Left Arm
  clavicle_l: {
    id: 'clavicle_l',
    name: 'Clavicle (L)',
    parentId: 'spine_upper',
    defaultOffset: [0.18, 0.18, 0],
    constraints: { type: 'universal', minX: -0.3, maxX: 0.3, minY: -0.3, maxY: 0.4, minZ: -0.4, maxZ: 0.4 },
    side: 'left'
  },
  shoulder_l: {
    id: 'shoulder_l',
    name: 'Shoulder (L)',
    parentId: 'clavicle_l',
    defaultOffset: [0.18, 0, 0],
    constraints: { type: 'ball', minX: -Math.PI * 0.9, maxX: Math.PI * 0.9, minY: -Math.PI * 0.9, maxY: Math.PI * 0.9, minZ: -Math.PI * 0.9, maxZ: Math.PI * 0.9, maxSwing: Math.PI * 0.85, maxTwist: Math.PI * 0.8 },
    side: 'left'
  },
  elbow_l: {
    id: 'elbow_l',
    name: 'Elbow (L)',
    parentId: 'shoulder_l',
    defaultOffset: [0, -0.35, 0],
    constraints: { type: 'hinge_x', minX: -0.05, maxX: 2.6, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'left'
  },
  wrist_l: {
    id: 'wrist_l',
    name: 'Wrist (L)',
    parentId: 'elbow_l',
    defaultOffset: [0, -0.32, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.5, maxY: 0.5, minZ: -0.8, maxZ: 0.8, maxSwing: 0.9, maxTwist: 1.2 },
    side: 'left'
  },
  hand_l: {
    id: 'hand_l',
    name: 'Hand (L)',
    parentId: 'wrist_l',
    defaultOffset: [0, -0.1, 0],
    constraints: { type: 'universal', minX: -0.5, maxX: 0.5, minY: -0.3, maxY: 0.3, minZ: -0.3, maxZ: 0.3 },
    side: 'left'
  },
  // Right Arm
  clavicle_r: {
    id: 'clavicle_r',
    name: 'Clavicle (R)',
    parentId: 'spine_upper',
    defaultOffset: [-0.18, 0.18, 0],
    constraints: { type: 'universal', minX: -0.3, maxX: 0.3, minY: -0.4, maxY: 0.3, minZ: -0.4, maxZ: 0.4 },
    side: 'right'
  },
  shoulder_r: {
    id: 'shoulder_r',
    name: 'Shoulder (R)',
    parentId: 'clavicle_r',
    defaultOffset: [-0.18, 0, 0],
    constraints: { type: 'ball', minX: -Math.PI * 0.9, maxX: Math.PI * 0.9, minY: -Math.PI * 0.9, maxY: Math.PI * 0.9, minZ: -Math.PI * 0.9, maxZ: Math.PI * 0.9, maxSwing: Math.PI * 0.85, maxTwist: Math.PI * 0.8 },
    side: 'right'
  },
  elbow_r: {
    id: 'elbow_r',
    name: 'Elbow (R)',
    parentId: 'shoulder_r',
    defaultOffset: [0, -0.35, 0],
    constraints: { type: 'hinge_x', minX: -0.05, maxX: 2.6, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'right'
  },
  wrist_r: {
    id: 'wrist_r',
    name: 'Wrist (R)',
    parentId: 'elbow_r',
    defaultOffset: [0, -0.32, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.5, maxY: 0.5, minZ: -0.8, maxZ: 0.8, maxSwing: 0.9, maxTwist: 1.2 },
    side: 'right'
  },
  hand_r: {
    id: 'hand_r',
    name: 'Hand (R)',
    parentId: 'wrist_r',
    defaultOffset: [0, -0.1, 0],
    constraints: { type: 'universal', minX: -0.5, maxX: 0.5, minY: -0.3, maxY: 0.3, minZ: -0.3, maxZ: 0.3 },
    side: 'right'
  },
  // Left Leg
  hip_l: {
    id: 'hip_l',
    name: 'Hip (L)',
    parentId: 'pelvis',
    defaultOffset: [0.18, -0.12, 0],
    constraints: { type: 'ball', minX: -1.6, maxX: 1.4, minY: -0.6, maxY: 0.6, minZ: -0.8, maxZ: 1.2, maxSwing: 1.6, maxTwist: 0.9 },
    side: 'left'
  },
  knee_l: {
    id: 'knee_l',
    name: 'Knee (L)',
    parentId: 'hip_l',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'hinge_x', minX: -2.6, maxX: 0.05, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'left'
  },
  ankle_l: {
    id: 'ankle_l',
    name: 'Ankle (L)',
    parentId: 'knee_l',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.4, maxY: 0.4, minZ: -0.5, maxZ: 0.5, maxSwing: 0.8, maxTwist: 0.5 },
    side: 'left'
  },
  foot_l: {
    id: 'foot_l',
    name: 'Foot (L)',
    parentId: 'ankle_l',
    defaultOffset: [0, -0.08, 0.08],
    constraints: { type: 'hinge_x', minX: -0.3, maxX: 0.3, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'left'
  },
  // Right Leg
  hip_r: {
    id: 'hip_r',
    name: 'Hip (R)',
    parentId: 'pelvis',
    defaultOffset: [-0.18, -0.12, 0],
    constraints: { type: 'ball', minX: -1.6, maxX: 1.4, minY: -0.6, maxY: 0.6, minZ: -1.2, maxZ: 0.8, maxSwing: 1.6, maxTwist: 0.9 },
    side: 'right'
  },
  knee_r: {
    id: 'knee_r',
    name: 'Knee (R)',
    parentId: 'hip_r',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'hinge_x', minX: -2.6, maxX: 0.05, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'right'
  },
  ankle_r: {
    id: 'ankle_r',
    name: 'Ankle (R)',
    parentId: 'knee_r',
    defaultOffset: [0, -0.45, 0],
    constraints: { type: 'ball', minX: -0.8, maxX: 0.8, minY: -0.4, maxY: 0.4, minZ: -0.5, maxZ: 0.5, maxSwing: 0.8, maxTwist: 0.5 },
    side: 'right'
  },
  foot_r: {
    id: 'foot_r',
    name: 'Foot (R)',
    parentId: 'ankle_r',
    defaultOffset: [0, -0.08, 0.08],
    constraints: { type: 'hinge_x', minX: -0.3, maxX: 0.3, minY: 0, maxY: 0, minZ: 0, maxZ: 0 },
    side: 'right'
  }
};

export class Dummy13Rig {
  public rootGroup: THREE.Group;
  public jointNodes: Map<JointId, THREE.Group> = new Map();
  public jointMeshMap: Map<JointId, THREE.Mesh[]> = new Map();
  public armorMeshes: THREE.Mesh[] = [];
  public frameMeshes: THREE.Mesh[] = [];
  public jointSpheres: Map<JointId, THREE.Mesh> = new Map();
  public hitHandles: Map<JointId, THREE.Mesh> = new Map();
  
  private armorMaterial: THREE.MeshStandardMaterial;
  private frameMaterial: THREE.MeshStandardMaterial;
  private jointMaterial: THREE.MeshStandardMaterial;
  private visorMaterial: THREE.MeshStandardMaterial;
  private handleMaterial: THREE.MeshBasicMaterial;
  private selectedHandleMaterial: THREE.MeshBasicMaterial;
  private hoveredHandleMaterial: THREE.MeshBasicMaterial;

  private currentTheme: MannequinTheme;
  private selectedJointId: JointId | null = null;
  private hoveredJointId: JointId | null = null;

  constructor(theme: MannequinTheme) {
    this.currentTheme = theme;
    this.rootGroup = new THREE.Group();
    this.rootGroup.name = 'Dummy13_Rig';

    // Create PBR materials matching Dummy 13 3D-printed aesthetics
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
      color: 0x3b82f6,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
      depthTest: false
    });

    this.selectedHandleMaterial = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      wireframe: true,
      transparent: true,
      opacity: 0.9,
      depthTest: false
    });

    this.hoveredHandleMaterial = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      wireframe: true,
      transparent: true,
      opacity: 0.7,
      depthTest: false
    });

    this.buildSkeletonHierarchy();
    this.generateDummy13Geometry();
  }

  private buildSkeletonHierarchy(): void {
    // Create Groups for each joint
    Object.values(JOINT_DEFINITIONS).forEach((def) => {
      const jointNode = new THREE.Group();
      jointNode.name = `joint_${def.id}`;
      jointNode.position.set(...def.defaultOffset);
      this.jointNodes.set(def.id, jointNode);
    });

    // Establish Parent-Child Hierarchy
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
    // 1. Pelvis (Waist core frame + armor)
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

    // 2. Spine Lower (Abdominal segment)
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

    // 3. Spine Upper (Chest + Ribcage)
    const spineUNode = this.jointNodes.get('spine_upper')!;
    const chestArmor = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.24, 0.24), this.armorMaterial);
    chestArmor.position.set(0, 0.12, 0);
    chestArmor.castShadow = true;
    spineUNode.add(chestArmor);
    this.armorMeshes.push(chestArmor);

    const chestPlate = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.18, 0.08), this.visorMaterial);
    chestPlate.position.set(0, 0.14, 0.11);
    spineUNode.add(chestPlate);
    this.armorMeshes.push(chestPlate);
    this.attachHandle(spineUNode, 'spine_upper', 0.22);

    // 4. Neck & Head
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

    // 5. Clavicles & Arms (Left & Right)
    this.buildLimb('l', 1);
    this.buildLimb('r', -1);

    // 6. Legs (Left & Right)
    this.buildLeg('l', 1);
    this.buildLeg('r', -1);
  }

  private buildLimb(side: 'l' | 'r', dir: number): void {
    // Clavicle / Shoulder socket
    const clavNode = this.jointNodes.get(`clavicle_${side}` as JointId)!;
    const clavMesh = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), this.jointMaterial);
    clavNode.add(clavMesh);
    this.attachHandle(clavNode, `clavicle_${side}` as JointId, 0.1);

    // Shoulder armor
    const shNode = this.jointNodes.get(`shoulder_${side}` as JointId)!;
    const shPad = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.18, 0.18), this.armorMaterial);
    shPad.position.set(0.02 * dir, -0.05, 0);
    shPad.castShadow = true;
    shNode.add(shPad);
    this.armorMeshes.push(shPad);

    // Upper Arm Bone
    const bicepMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.28, 8), this.frameMaterial);
    bicepMesh.position.set(0, -0.18, 0);
    bicepMesh.castShadow = true;
    shNode.add(bicepMesh);
    this.frameMeshes.push(bicepMesh);
    this.attachHandle(shNode, `shoulder_${side}` as JointId, 0.14);

    // Elbow Joint
    const elNode = this.jointNodes.get(`elbow_${side}` as JointId)!;
    const elJoint = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.12, 12), this.jointMaterial);
    elJoint.rotation.z = Math.PI / 2;
    elNode.add(elJoint);

    // Forearm
    const forearmMesh = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.26, 0.14), this.armorMaterial);
    forearmMesh.position.set(0, -0.16, 0);
    forearmMesh.castShadow = true;
    elNode.add(forearmMesh);
    this.armorMeshes.push(forearmMesh);
    this.attachHandle(elNode, `elbow_${side}` as JointId, 0.14);

    // Wrist & Hand
    const wrNode = this.jointNodes.get(`wrist_${side}` as JointId)!;
    const handMesh = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.14, 0.06), this.frameMaterial);
    handMesh.position.set(0, -0.07, 0);
    wrNode.add(handMesh);
    this.frameMeshes.push(handMesh);
    this.attachHandle(wrNode, `wrist_${side}` as JointId, 0.12);
  }

  private buildLeg(side: 'l' | 'r', dir: number): void {
    const hipNode = this.jointNodes.get(`hip_${side}` as JointId)!;
    // Hip socket sphere
    const hipSphere = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 12), this.jointMaterial);
    hipNode.add(hipSphere);

    // Thigh armor & core
    const thighArmor = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.36, 0.2), this.armorMaterial);
    thighArmor.position.set(0, -0.22, 0);
    thighArmor.castShadow = true;
    hipNode.add(thighArmor);
    this.armorMeshes.push(thighArmor);
    this.attachHandle(hipNode, `hip_${side}` as JointId, 0.18);

    // Knee Joint
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

    // Ankle & Foot
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
      new THREE.SphereGeometry(radius, 12, 8),
      this.handleMaterial
    );
    handle.userData = { isJointHandle: true, jointId };
    handle.renderOrder = 999; // Always render on top for easy joint clicking
    node.add(handle);
    this.hitHandles.set(jointId, handle);
  }

  public setJointRotation(jointId: JointId, quaternion: THREE.Quaternion): void {
    const node = this.jointNodes.get(jointId);
    const def = JOINT_DEFINITIONS[jointId];
    if (node && def) {
      const clamped = clampJointRotation(quaternion, def.constraints);
      node.quaternion.copy(clamped);
    }
  }

  public getJointRotation(jointId: JointId): THREE.Quaternion {
    const node = this.jointNodes.get(jointId);
    return node ? node.quaternion.clone() : new THREE.Quaternion();
  }

  public setJointPosition(jointId: JointId, position: THREE.Vector3): void {
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

  public updateTheme(theme: MannequinTheme): void {
    this.currentTheme = theme;
    this.armorMaterial.color.set(theme.armorColor);
    this.armorMaterial.roughness = theme.roughness;
    this.armorMaterial.metalness = theme.metalness;

    this.frameMaterial.color.set(theme.frameColor);
    this.jointMaterial.color.set(theme.jointColor);
    this.visorMaterial.color.set(theme.accentColor);
    this.visorMaterial.emissive.set(theme.accentColor);
  }

  public resetPose(): void {
    Object.values(JOINT_DEFINITIONS).forEach((def) => {
      const node = this.jointNodes.get(def.id);
      if (node) {
        node.quaternion.identity();
        node.position.set(...def.defaultOffset);
      }
    });
  }

  public mirrorPose(fromSide: 'left' | 'right'): void {
    const sidePairs: [JointId, JointId][] = [
      ['clavicle_l', 'clavicle_r'],
      ['shoulder_l', 'shoulder_r'],
      ['elbow_l', 'elbow_r'],
      ['wrist_l', 'wrist_r'],
      ['hand_l', 'hand_r'],
      ['hip_l', 'hip_r'],
      ['knee_l', 'knee_r'],
      ['ankle_l', 'ankle_r'],
      ['foot_l', 'foot_r']
    ];

    sidePairs.forEach(([lId, rId]) => {
      const srcId = fromSide === 'left' ? lId : rId;
      const dstId = fromSide === 'left' ? rId : lId;
      const srcNode = this.jointNodes.get(srcId);
      const dstNode = this.jointNodes.get(dstId);
      if (srcNode && dstNode) {
        const q = srcNode.quaternion.clone();
        // Invert X/Z components for bilateral mirror
        dstNode.quaternion.set(q.x, -q.y, -q.z, q.w);
      }
    });
  }

  public dispose(): void {
    // Full GPU memory leak prevention: traverse and dispose geometries and materials
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
