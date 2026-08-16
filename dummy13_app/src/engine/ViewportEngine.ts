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
  private isWireframe: boolean = false;

  // Callbacks to React UI (throttled/transient)
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

    // Studio Lighting
    this.setupLighting();

    // Studio Environment Grid & Floor
    this.gridHelper = new THREE.GridHelper(10, 20, 0x3b82f6, 0x27272a);
    this.gridHelper.position.y = 0;
    this.scene.add(this.gridHelper);

    const shadowGeo = new THREE.PlaneGeometry(10, 10);
    const shadowMat = new THREE.ShadowMaterial({ opacity: 0.45 });
    this.shadowPlane = new THREE.Mesh(shadowGeo, shadowMat);
    this.shadowPlane.rotation.x = -Math.PI / 2;
    this.shadowPlane.receiveShadow = true;
    this.scene.add(this.shadowPlane);

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

    const rimLight = new THREE.DirectionalLight(0xec4899, 0.5);
    rimLight.position.set(0, 3, -4);
    this.scene.add(rimLight);
  }

  private bindEvents(): void {
    const dom = this.renderer.domElement;

    this.transformControls.addEventListener('dragging-changed', (event) => {
      this.orbitControls.enabled = !event.value;
    });

    this.transformControls.addEventListener('change', () => {
      const attachedObj = this.transformControls.object;
      if (attachedObj && attachedObj.name.startsWith('joint_')) {
        const jointId = attachedObj.name.replace('joint_', '') as JointId;
        const def = JOINT_DEFINITIONS[jointId];
        if (def) {
          // Re-clamp directly in transient frame loop
          this.rig.setJointRotation(jointId, attachedObj.quaternion);
          if (this.onJointChanged) {
            this.onJointChanged(jointId, attachedObj.quaternion);
          }
        }
      }
    });

    dom.addEventListener('pointerdown', this.onPointerDown);
    dom.addEventListener('pointermove', this.onPointerMove);
    window.addEventListener('resize', this.onWindowResize);

    // WebGL Context Loss Handlers
    dom.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    });
    dom.addEventListener('webglcontextrestored', () => {
      this.startLoop();
    });
  }

  private onPointerDown = (event: MouseEvent): void => {
    // Raycast only if not already interacting with TransformControls
    if (this.transformControls.dragging) return;
    if (event.button !== 0) return; // Left-click only

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
      }
    } else {
      this.transformControls.detach();
    }

    if (this.onJointSelected) {
      this.onJointSelected(jointId);
    }
  }

  public setGizmoMode(mode: GizmoMode): void {
    if (mode === 'none') {
      this.transformControls.detach();
    } else {
      this.transformControls.setMode(mode);
      if (this.rig.jointNodes.has('pelvis') && !this.transformControls.object) {
        this.selectJoint('pelvis');
      }
    }
  }

  public setGizmoSpace(space: TransformSpace): void {
    this.transformControls.setSpace(space);
  }

  public applyPose(poseData: Record<string, { rotation: { x: number; y: number; z: number; w: number }; position?: { x: number; y: number; z: number } }>): void {
    Object.entries(poseData).forEach(([jointKey, val]) => {
      const jointId = jointKey as JointId;
      if (val.rotation) {
        const q = new THREE.Quaternion(val.rotation.x, val.rotation.y, val.rotation.z, val.rotation.w);
        this.rig.setJointRotation(jointId, q);
      }
      if (val.position && jointId === 'pelvis') {
        this.rig.setJointPosition(jointId, new THREE.Vector3(val.position.x, val.position.y, val.position.z));
      }
    });
  }

  public toggleWireframe(): boolean {
    this.isWireframe = !this.isWireframe;
    const handleSet = new Set(this.rig.hitHandles.values());
    this.rig.rootGroup.traverse((child) => {
      if (child instanceof THREE.Mesh && !handleSet.has(child)) {
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => {
            if ('wireframe' in m) (m as THREE.MeshStandardMaterial).wireframe = this.isWireframe;
          });
        } else if (child.material && 'wireframe' in child.material) {
          (child.material as THREE.MeshStandardMaterial).wireframe = this.isWireframe;
        }
      }
    });
    return this.isWireframe;
  }

  public captureScreenshot(): string {
    this.renderer.render(this.scene, this.camera);
    return this.renderer.domElement.toDataURL('image/png');
  }

  private startLoop = (): void => {
    const render = () => {
      if (this.isDisposed) return;
      this.animFrameId = requestAnimationFrame(render);
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

    this.renderer.dispose();
    if (this.renderer.domElement.parentElement) {
      this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
    }
  }
}
