import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js';
import { Dummy13Rig, JOINT_DEFINITIONS } from './Dummy13Rig';
import { JointId, MannequinTheme, GizmoMode, TransformSpace } from '../types/dummy13';

export class ViewportEngine {
  public container: HTMLElement;
  public scene: THREE.Scene;
  public camera: THREE.PerspectiveCamera;
  public renderer: THREE.WebGLRenderer;
  public orbitControls: OrbitControls;
  public transformControls: TransformControls;
  public rig: Dummy13Rig;
  
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private animFrameId: number | null = null;
  private isDisposed: boolean = false;
  private gridHelper: THREE.GridHelper;
  private shadowPlane: THREE.Mesh;
  private floorMesh: THREE.Mesh;
  private isWireframe: boolean = false;
  public gizmosVisible: boolean = true;
  private currentGizmoMode: GizmoMode = 'rotate';
  public isGravityEnabled: boolean = true;
  public isFloorSolid: boolean = true;
  private velocityY: number = 0;
  private readonly gravityAccel: number = -9.81;
  private readonly bounceRestitution: number = 0.18;
  private readonly airResistance: number = 0.45;
  // Callbacks to React UI
  public onJointSelected?: (jointId: JointId | null) => void;
  public onJointChanged?: (jointId: JointId, rotation: THREE.Quaternion) => void;

  constructor(container: HTMLElement, initialTheme: MannequinTheme) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#121316');

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 50);
    this.camera.position.set(0, 1.4, 3.2);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;
    container.appendChild(this.renderer.domElement);

    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Orbit Controls
    this.orbitControls = new OrbitControls(this.camera, this.renderer.domElement);
    this.orbitControls.enableDamping = true;
    this.orbitControls.dampingFactor = 0.08;
    this.orbitControls.target.set(0, 0.9, 0);
    this.orbitControls.maxDistance = 10;
    this.orbitControls.minDistance = 0.5;

    // Transform Gizmo Controls
    this.transformControls = new TransformControls(this.camera, this.renderer.domElement);
    this.transformControls.size = 0.65;
    this.transformControls.setMode('rotate');
    this.transformControls.setSpace('local');
    this.scene.add(this.transformControls);

    // Setup Rig
    this.rig = new Dummy13Rig(initialTheme);
    this.scene.add(this.rig.rootGroup);

    // Studio Environment: Solid Ground Stage, Grid & Shadows
    const floorGeo = new THREE.CylinderGeometry(5.5, 5.7, 0.1, 48);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x181a20,
      roughness: 0.8,
      metalness: 0.2
    });
    this.floorMesh = new THREE.Mesh(floorGeo, floorMat);
    this.floorMesh.position.y = -0.05;
    this.floorMesh.receiveShadow = true;
    this.scene.add(this.floorMesh);

    this.gridHelper = new THREE.GridHelper(10, 20, 0x3b82f6, 0x334155);
    this.gridHelper.position.y = 0.001;
    this.scene.add(this.gridHelper);

    const shadowGeo = new THREE.PlaneGeometry(12, 12);
    const shadowMat = new THREE.ShadowMaterial({ opacity: 0.55 });
    this.shadowPlane = new THREE.Mesh(shadowGeo, shadowMat);
    this.shadowPlane.rotation.x = -Math.PI / 2;
    this.shadowPlane.position.y = 0.002;
    this.shadowPlane.receiveShadow = true;
    this.scene.add(this.shadowPlane);

    this.setupLighting();
    this.bindEvents();
    this.startLoop();
  }

  private setupLighting(): void {
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
    keyLight.position.set(3, 4, 3);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.bias = -0.0001;
    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x60a5fa, 0.8);
    fillLight.position.set(-3, 2, -2);
    this.scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xf43f5e, 0.5);
    rimLight.position.set(0, 3, -4);
    this.scene.add(rimLight);
  }

  private bindEvents(): void {
    const dom = this.renderer.domElement;

    this.transformControls.addEventListener('dragging-changed', (event) => {
      this.orbitControls.enabled = !event.value;
    });

    this.transformControls.addEventListener('change', () => {
      this.velocityY = 0;
      const attachedObj = this.transformControls.object;
      if (attachedObj && attachedObj.name.startsWith('joint_')) {
        const jointId = attachedObj.name.replace('joint_', '') as JointId;
        const def = JOINT_DEFINITIONS[jointId];
        if (def) {
          if (jointId !== 'pelvis' && jointId !== 'root') {
            this.rig.setJointRotation(jointId, attachedObj.quaternion);
            if (this.isFloorSolid) {
              this.rig.clampToFloor();
            }
            if (this.onJointChanged) {
              this.onJointChanged(jointId, attachedObj.quaternion);
            }
          } else if (this.isFloorSolid) {
            this.rig.clampToFloor();
          }
        }
      }
    });

    dom.addEventListener('pointerdown', this.onPointerDown);
    dom.addEventListener('pointermove', this.onPointerMove);
    window.addEventListener('resize', this.onWindowResize);

    dom.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    });
    dom.addEventListener('webglcontextrestored', () => {
      this.startLoop();
    });
  }

  private onPointerDown = (event: MouseEvent): void => {
    if (!this.gizmosVisible) return;
    if (this.transformControls.dragging) return;
    if (event.button !== 0) return;

    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const handles = Array.from(this.rig.hitHandles.values());
    const intersects = this.raycaster.intersectObjects(handles, false);

    if (intersects.length > 0) {
      const hitHandle = intersects[0].object;
      const jointId = hitHandle.userData.jointId as JointId;
      this.selectJoint(jointId);
    }
  };

  private onPointerMove = (event: MouseEvent): void => {
    if (!this.gizmosVisible) return;
    if (this.transformControls.dragging) return;

    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const handles = Array.from(this.rig.hitHandles.values());
    const intersects = this.raycaster.intersectObjects(handles, false);

    if (intersects.length > 0) {
      const jointId = intersects[0].object.userData.jointId as JointId;
      this.rig.hoverJoint(jointId);
      this.renderer.domElement.style.cursor = 'pointer';
    } else {
      this.rig.hoverJoint(null);
      this.renderer.domElement.style.cursor = 'default';
    }
  };

  private onWindowResize = (): void => {
    if (!this.container || this.isDisposed) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  };

  public selectJoint(jointId: JointId | null): void {
    this.rig.selectJoint(jointId);
    if (jointId) {
      const node = this.rig.jointNodes.get(jointId);
      if (node) {
        this.transformControls.attach(node);
        if (this.currentGizmoMode === 'translate' && jointId !== 'pelvis' && jointId !== 'root') {
          this.transformControls.setMode('rotate');
        } else if (this.currentGizmoMode !== 'none') {
          this.transformControls.setMode(this.currentGizmoMode);
        }
      }
    } else {
      this.transformControls.detach();
    }

    if (this.onJointSelected) {
      this.onJointSelected(jointId);
    }
  }

  public setGizmoMode(mode: GizmoMode): void {
    this.currentGizmoMode = mode;
    if (mode === 'none') {
      this.transformControls.detach();
    } else if (mode === 'translate') {
      const attachedObj = this.transformControls.object;
      const jointId = attachedObj?.name.replace('joint_', '') as JointId | undefined;
      if (!jointId || (jointId !== 'pelvis' && jointId !== 'root')) {
        this.selectJoint('pelvis');
      }
      this.transformControls.setMode('translate');
    } else {
      this.transformControls.setMode(mode);
      if (!this.transformControls.object && this.rig.jointNodes.has('pelvis')) {
        this.selectJoint('pelvis');
      }
    }
  }

  public setGizmoSpace(space: TransformSpace): void {
    this.transformControls.setSpace(space);
  }

  public applyPose(poseData: Record<string, { rotation: { x: number; y: number; z: number; w: number }; position?: { x: number; y: number; z: number } }>): void {
    this.velocityY = 0;
    Object.entries(poseData).forEach(([jointKey, val]) => {
      const jointId = jointKey as JointId;
      if (val.rotation) {
        const q = new THREE.Quaternion(val.rotation.x, val.rotation.y, val.rotation.z, val.rotation.w);
        this.rig.setJointRotation(jointId, q, true);
      }
      if (val.position && jointId === 'pelvis') {
        this.rig.setJointPosition(jointId, new THREE.Vector3(val.position.x, val.position.y, val.position.z));
      }
    });
    if (this.isFloorSolid) {
      this.rig.clampToFloor();
    }
    this.rig.rootGroup.updateMatrixWorld(true);
  }
  public toggleWireframe(): boolean {
    this.isWireframe = !this.isWireframe;
    const handleSet = new Set(this.rig.hitHandles.values());
    this.rig.rootGroup.traverse((child) => {
      if (child instanceof THREE.Mesh && !handleSet.has(child)) {
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => {
            m.wireframe = this.isWireframe;
          });
        } else if (child.material) {
          child.material.wireframe = this.isWireframe;
        }
      }
    });
    return this.isWireframe;
  }

  public toggleGizmoVisibility(): boolean {
    this.gizmosVisible = !this.gizmosVisible;
    this.rig.setHandlesVisible(this.gizmosVisible);
    return this.gizmosVisible;
  }

  public toggleGravity(): boolean {
    this.isGravityEnabled = !this.isGravityEnabled;
    this.velocityY = 0;
    return this.isGravityEnabled;
  }

  public dropToFloor(): void {
    this.velocityY = 0;
    this.rig.dropToFloor();
  }

  private startLoop = (): void => {
    let lastTime = performance.now();

    const render = () => {
      if (this.isDisposed) return;
      this.animFrameId = requestAnimationFrame(render);
      const now = performance.now();
      const rawDt = (now - lastTime) / 1000;
      lastTime = now;
      const dt = Math.min(rawDt, 0.05);

      const isTransforming = this.transformControls.dragging;
      const pelvis = this.rig.jointNodes.get('pelvis');
      const activeJointId = isTransforming && this.transformControls.object
        ? (this.transformControls.object.name.replace('joint_', '') as JointId)
        : null;

      if (pelvis) {
        // Perform 2 physics substeps for rock-solid stability and zero tunneling
        const substeps = 2;
        const subDt = dt / substeps;

        for (let step = 0; step < substeps; step++) {
          this.rig.rootGroup.updateMatrixWorld(true);

          if (this.isGravityEnabled) {
            // 1. Joint sag dynamics
            this.rig.applyGravitySag(subDt, activeJointId);
            this.rig.rootGroup.updateMatrixWorld(true);

            // 2. Linear core gravity & velocity
            if (!isTransforming || activeJointId !== 'pelvis') {
              this.velocityY += this.gravityAccel * subDt;
              this.velocityY *= Math.exp(-this.airResistance * subDt);
              this.velocityY = Math.max(this.velocityY, -20.0);

              pelvis.position.y += this.velocityY * subDt;
              this.rig.rootGroup.updateMatrixWorld(true);

              const currentLowest = this.rig.getLowestY();
              if (this.isFloorSolid && currentLowest <= 0.0005) {
                pelvis.position.y -= currentLowest;
                this.rig.rootGroup.updateMatrixWorld(true);

                if (this.velocityY < 0) {
                  if (Math.abs(this.velocityY) < 0.25) {
                    this.velocityY = 0;
                  } else {
                    this.velocityY = -this.velocityY * this.bounceRestitution;
                  }
                }
              }
            }
          } else if (this.isFloorSolid && (!isTransforming || activeJointId !== 'pelvis')) {
            const lowest = this.rig.getLowestY();
            if (lowest < 0) {
              pelvis.position.y -= lowest;
              this.rig.rootGroup.updateMatrixWorld(true);
            }
            this.velocityY = 0;
          }
        }
      }

      this.orbitControls.update();
      this.renderer.render(this.scene, this.camera);
    };
    render();
  };

  public dispose(): void {
    this.isDisposed = true;
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    
    window.removeEventListener('resize', this.onWindowResize);
    this.renderer.domElement.removeEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.removeEventListener('pointermove', this.onPointerMove);

    this.transformControls.dispose();
    this.orbitControls.dispose();
    this.rig.dispose();
    this.gridHelper.geometry.dispose();
    (this.gridHelper.material as THREE.Material).dispose();
    this.shadowPlane.geometry.dispose();
    (this.shadowPlane.material as THREE.Material).dispose();
    this.floorMesh.geometry.dispose();
    (this.floorMesh.material as THREE.Material).dispose();

    this.renderer.dispose();
    if (this.renderer.domElement.parentElement) {
      this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
    }
  }
}
