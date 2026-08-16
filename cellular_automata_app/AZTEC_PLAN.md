# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: Aztec Software Project  
> **Status**: Active / Synced with Codebase  
> **Last Updated**: 2026-08-16 14:45:31  
> **Files Indexed**: 30 total source files  

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
| `src/hooks/useCanvasPan.ts` | Hook (State/Behavior) | React state management hook for useCanvasPan |
| `index.html` | Source | Module implementation for index |
| `package.json` | Config / Build | Node dependencies & scripts manifest |
| `postcss.config.js` | Source | Module implementation for postcss.config |
| `src/App.test.tsx` | Test Suite | Unit tests for App |
| `src/App.tsx` | Coordinator | Main application coordinator & view shell |
| `src/atoms/Badge.tsx` | Atom (UI Primitive) | Atomic UI primitive for Badge |
| `src/atoms/Button.tsx` | Atom (UI Primitive) | Atomic UI primitive for Button |
| `src/atoms/Select.tsx` | Atom (UI Primitive) | Atomic UI primitive for Select |
| `src/atoms/Slider.tsx` | Atom (UI Primitive) | Atomic UI primitive for Slider |
| `src/components/MetricsBar.tsx` | Component (Composite) | Composite panel for MetricsBar |
| `src/components/SimulationCanvas.tsx` | Component (Composite) | Composite panel for SimulationCanvas |
| `src/components/Toolbar.tsx` | Component (Composite) | Composite panel for Toolbar |
| `src/constants/config.ts` | Constants (Config) | Static configuration constants for config |
| `src/constants/presets.ts` | Constants (Config) | Static configuration constants for presets |
| `src/engine/rules/gameOfLife.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for gameOfLife |
| `src/engine/rules/langtonsAnt.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for langtonsAnt |
| `src/engine/rules/rule110.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for rule110 |
| `src/engine/simulation.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for simulation |
| `src/engine/worker.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for worker |
| `src/hooks/useCanvasInput.ts` | Hook (State/Behavior) | React state management hook for useCanvasInput |
| `src/hooks/useResizeObserver.ts` | Hook (State/Behavior) | React state management hook for useResizeObserver |
| `src/hooks/useSimulationWorker.ts` | Hook (State/Behavior) | React state management hook for useSimulationWorker |
| `src/index.css` | Source | Tailwind base directives & global design tokens |
| `src/main.tsx` | Coordinator | React DOM entry root & style bootstrap |
| `src/types/simulation.ts` | Types (Interfaces) | Type definitions & data contracts for simulation |
| `src/utils/geometry.ts` | Utils (Pure Helpers) | Module implementation for geometry |
| `tailwind.config.js` | Config / Build | Tailwind CSS utility & theme configuration |
| `tsconfig.json` | Config / Build | TypeScript strict compiler options |
| `tsconfig.node.json` | Source | Module implementation for tsconfig.node |
| `vite.config.ts` | Config / Build | Vite dev server & build bundler configuration |

---

## 📝 Change Log & Iteration History
- **2026-08-16 14:45:38** — Automated Self-Healing Build Fix (1 files repaired).
- **2026-08-16 14:45:31** — Incremental Edit: "also panning feature" (Modified: src/hooks/useCanvasPan.ts, src/hooks/useCanvasInput.ts, src/components/SimulationCanvas.tsx, src/components/SimulationCanvas.tsx).
- **2026-08-16 14:44:21** — Automated Self-Healing Build Fix (1 files repaired).
- **2026-08-16 14:44:14** — Incremental Edit: "now, allow zooming in or out with control and wheel" (Modified: src/components/SimulationCanvas.tsx, src/components/SimulationCanvas.tsx, src/components/SimulationCanvas.tsx, src/components/SimulationCanvas.tsx).
- **2026-08-16 14:39:22** — Incremental Edit: "Look, the cells are of the size of actual pixels they are too tiny, it must be responsive though" (Modified: src/components/SimulationCanvas.tsx, src/App.tsx).
- **2026-08-16 14:37:17** — Incremental Edit: "make the resolution adjustable and production ready" (Modified: src/constants/config.ts, src/components/Toolbar.tsx, src/App.tsx, src/components/SimulationCanvas.tsx).
- **2026-08-16 14:35:51** — Incremental Edit: "nothing seems to happen on the app, fix it following the plan" (Modified: src/hooks/useSimulationWorker.ts, src/components/SimulationCanvas.tsx, src/App.tsx).
- **2026-08-16 14:06:48** — Codebase Synchronization (Indexed 30 files).
