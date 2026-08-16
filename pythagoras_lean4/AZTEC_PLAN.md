# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: Aztec Software Project  
> **Status**: Active / Synced with Codebase  
> **Last Updated**: 2026-08-16 13:32:53  
> **Files Indexed**: 34 total source files  

---

## 📐 Architecture & Technology Stack
- **Ecosystem**: Vite 5 + React 18 + TypeScript + TailwindCSS
- **Atomic Directory Discipline**:
  - `src/atoms/` — Single-purpose UI primitives (<= 60 lines)
  - `src/components/` — Composite UI panels & containers (<= 120 lines)
  - `src/hooks/` — Dedicated React state & behavioral hooks (<= 80 lines)
  - `src/engine/` — Pure domain logic, math, algorithms (<= 150 lines, zero UI imports)
  - `src/store/` — State slices & persistence (<= 100 lines)
  - `src/types/` — TypeScript interfaces & contracts (<= 100 lines)

### Key Architectural Decisions (ADRs)
- **[ADR-01]**: Atomic modular architecture with strict 150-line ceiling per file.
- **[ADR-02]**: Separation of concerns between UI components and domain calculation engine.

---

## 🗺️ Phased Implementation Roadmap

### Phase 1: Core Foundation & Configuration
- [x] Initial build configuration & toolchain (`package.json`, `tsconfig.json`, `vite.config.ts`)
- [x] Styling foundation & design tokens (`tailwind.config.js`, `src/index.css`)
- [x] Base atomic primitives & layout scaffolding

### Phase 2: Domain Implementation & State Flow
- [x] Core domain components & view coordinators
- [x] State management & custom hooks integration

### Phase 3: Validation, Self-Healing & Verification
- [x] Automated test suite passing
- [x] Zero TypeScript compiler & lint errors
- [x] Live development server verified

---

## 📁 File & Module Index

| File | Layer | Responsibility |
| :--- | :--- | :--- |
| `index.html` | Source | Module implementation for index |
| `package.json` | Config / Build | Node dependencies & scripts manifest |
| `postcss.config.js` | Source | Module implementation for postcss.config |
| `src/App.test.tsx` | Test Suite | Unit tests for App |
| `src/App.tsx` | Coordinator | Main application coordinator & view shell |
| `src/atoms/Badge.tsx` | Atom (UI Primitive) | Atomic UI primitive for Badge |
| `src/atoms/Button.tsx` | Atom (UI Primitive) | Atomic UI primitive for Button |
| `src/atoms/Card.tsx` | Atom (UI Primitive) | Atomic UI primitive for Card |
| `src/atoms/Slider.tsx` | Atom (UI Primitive) | Atomic UI primitive for Slider |
| `src/atoms/Toggle.tsx` | Atom (UI Primitive) | Atomic UI primitive for Toggle |
| `src/components/DissectionCanvas.tsx` | Component (Composite) | Composite panel for DissectionCanvas |
| `src/components/GeometryControls.tsx` | Component (Composite) | Composite panel for GeometryControls |
| `src/components/Header.tsx` | Component (Composite) | Composite panel for Header |
| `src/components/LeanCodeGenerator.tsx` | Component (Composite) | Composite panel for LeanCodeGenerator |
| `src/components/ProofTreeVisualizer.tsx` | Component (Composite) | Composite panel for ProofTreeVisualizer |
| `src/components/TacticStateExplorer.tsx` | Component (Composite) | Composite panel for TacticStateExplorer |
| `src/constants/leanPresets.ts` | Constants (Config) | Static configuration constants for leanPresets |
| `src/constants/pythagorasData.ts` | Constants (Config) | Static configuration constants for pythagorasData |
| `src/engine/geometryEngine.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for geometryEngine |
| `src/engine/leanKernelSimulator.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for leanKernelSimulator |
| `src/engine/proofExporter.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for proofExporter |
| `src/hooks/useDissectionAnimation.ts` | Hook (State/Behavior) | React state management hook for useDissectionAnimation |
| `src/hooks/useProofStore.ts` | Hook (State/Behavior) | React state management hook for useProofStore |
| `src/index.css` | Source | Tailwind base directives & global design tokens |
| `src/main.tsx` | Coordinator | React DOM entry root & style bootstrap |
| `src/store/proofStore.ts` | Store (State Slice) | Global state slice for proofStore |
| `src/types/geometry.ts` | Types (Interfaces) | Type definitions & data contracts for geometry |
| `src/types/lean.ts` | Types (Interfaces) | Type definitions & data contracts for lean |
| `src/types/proofState.ts` | Types (Interfaces) | Type definitions & data contracts for proofState |
| `src/utils/cryptoHash.ts` | Utils (Pure Helpers) | Module implementation for cryptoHash |
| `src/utils/sanitizer.ts` | Utils (Pure Helpers) | Module implementation for sanitizer |
| `tailwind.config.js` | Config / Build | Tailwind CSS utility & theme configuration |
| `tsconfig.json` | Config / Build | TypeScript strict compiler options |
| `vite.config.ts` | Config / Build | Vite dev server & build bundler configuration |

---

## 📝 Change Log & Iteration History
- **2026-08-16 13:33:18** — Automated Self-Healing Build Fix (2 files repaired).
- **2026-08-16 13:32:53** — Incremental Edit: "Add an interactive animation speed multiplier slider to GeometryControls" (Modified: src/components/GeometryControls.tsx, src/components/GeometryControls.tsx, src/components/GeometryControls.tsx, src/store/proofStore.ts).
- **2026-08-16 13:30:14** — Codebase Synchronization (Indexed 34 files).
