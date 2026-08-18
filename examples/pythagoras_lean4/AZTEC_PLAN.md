# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: Aztec Software Project  
> **Status**: Active / Synced with Codebase  
> **Last Updated**: 2026-08-18 09:35:14  
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
| `src/engine/theorems/binomialTactics.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for binomialTactics |
| `src/engine/binomialEngine.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for binomialEngine |
| `src/constants/binomialPresets.ts` | Constants (Config) | Static configuration constants for binomialPresets |
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
- **2026-08-18 09:35:14** — Incremental Edit: "the Lean 4 Formal Specifications Dissection.lean result are swap, the pythagoras should be the binomial one and viceversa." (Modified: src/engine/proofExporter.ts, src/App.test.tsx).
- **2026-08-18 09:32:37** — Incremental Edit: "Minor Observations and Cleanups
Unused Hypotheses: The positivity hypotheses ha : a > 0, hb : b > 0, and hc : c > 0 are not used in the proof body. The algebraic identity holds over any commutative ring/field regardless of whether the numbers are positive, negative, or zero.

Tactic Simplification: ring handles both expansion steps, and linear_combination can solve the entire deduction directly in one line without intermediate have statements." (Modified: src/engine/proofExporter.ts).
- **2026-08-18 09:29:34** — Incremental Edit: "MathlibDemo.lean:4:41
Tactic state
1 goal
ℝ : Type u_1
a b : ℝ
ha : sorry
hb : sorry
⊢ sorry
Messages (2)
MathlibDemo.lean:4:5
failed to synthesize instance of type class
  HAdd ℝ ℝ ?m.20

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
Error code: lean.synthInstanceFailed
View explanation
MathlibDemo.lean:4:41
unsolved goals
ℝ : Type u_1
a b : ℝ
ha : sorry
hb : sorry
h_geom : sorry
⊢ sorry" (Modified: src/engine/proofExporter.ts).
- **2026-08-18 09:28:52** — Incremental Edit: "MathlibDemo.lean:6:6
Tactic state
1 goal
ℝ : Type u_1
a b : ℝ
ha : sorry
hb : sorry
h_geom : sorry
⊢ sorry
Messages (2)
MathlibDemo.lean:6:2
Try this:
  [apply] ring_nf
  
  The `ring` tactic failed to close the goal. Use `ring_nf` to obtain a normal form.
    
  Note that `ring` works primarily in *commutative* rings. If you have a noncommutative ring, abelian group or module, consider using `noncomm_ring`, `abel` or `module` instead.
MathlibDemo.lean:4:41
unsolved goals
ℝ : Type u_1
a b : ℝ
ha : sorry
hb : sorry
h_geom : sorry
⊢ sorry" (Modified: src/engine/proofExporter.ts, src/engine/theorems/binomialTactics.ts, src/engine/leanKernelSimulator.ts).
- **2026-08-18 09:27:55** — Incremental Edit: "on the binomial proof we get this MathlibDemo.lean:7:19
Tactic state
1 goal
ℝ : Type u_1
a b : ℝ
ha : sorry
hb : sorry
h_geom : sorry
⊢ sorry
Messages (1)
MathlibDemo.lean:7:2
linarith failed to find a contradiction
ℝ : Type u_1
a b : ℝ
ha : sorry
hb : sorry
h_geom : sorry
⊢ False

failed" (Modified: src/engine/proofExporter.ts, src/engine/theorems/binomialTactics.ts).
- **2026-08-18 09:21:23** — Incremental Edit: "now fix the binomial 2d render" (Modified: src/constants/binomialPresets.ts, src/engine/binomialEngine.ts).
- **2026-08-18 09:20:05** — Incremental Edit: "[plugin:vite:react-babel] /home/coorti/.aztec/pythagoras_lean4/src/components/DissectionCanvas.tsx: Expected corresponding JSX closing tag for <svg>. (112:6)
  115 | };
/home/coorti/.aztec/pythagoras_lean4/src/components/DissectionCanvas.tsx:112:6
110|  
111|          <p className="text-xs text-slate-400 mt-2 font-mono">{frame.description}</p>
112|        </div>
   |        ^
113|      </Card>
114|    );" (Modified: src/components/DissectionCanvas.tsx).
- **2026-08-18 09:19:29** — Incremental Edit: "the visuals aren't working, nothing is being rendered." (Modified: src/components/DissectionCanvas.tsx).
- **2026-08-18 09:18:43** — Automated Self-Healing Build Fix (2 files repaired).
- **2026-08-18 09:16:57** — Automated Self-Healing Build Fix (1 files repaired).
- **2026-08-18 09:16:24** — Incremental Edit: "Module Consensus: now let's add another proof but for the binomial expansion identity $(a + b)^2 = a^2 + 2ab + b^2$ via diagonal ($45^\circ$) slicing." (Modified: src/constants/binomialPresets.ts, src/engine/binomialEngine.ts, src/engine/theorems/binomialTactics.ts, src/types/proofState.ts, src/engine/geometryEngine.ts, src/engine/leanKernelSimulator.ts, src/store/proofStore.ts, src/hooks/useProofStore.ts, src/components/Header.tsx, src/components/GeometryControls.tsx, src/components/DissectionCanvas.tsx, src/engine/proofExporter.ts, src/components/LeanCodeGenerator.tsx, src/App.tsx, src/App.test.tsx).
- **2026-08-18 09:16:24** — Automated Self-Healing Build Fix (1 files repaired).
- **2026-08-18 09:11:47** — Incremental Edit: "the diagram isn't right displayed In the valid geometric proof of the Pythagorean theorem, the inner shape **must be a square**.

The image depicts a **misconfigured visual** where the corner cuts are mirrored rather than rotated cyclically. While the numerical equation at the bottom is mathematically true ($196 = 148 + 48$), the diagram does not match the formula.

---

### What the Diagram Actually Shows

In this image, the split points on the outer edges are arranged symmetrically rather than cyclically:

* **Two Small Triangles (Gold & Purple):** Isosceles right triangles with legs $2 \times 2$.
$$\text{Area} = 2 \times \left(\frac{1}{2} \times 2 \times 2\right) = 4$$


* **Two Large Triangles (Blue & Green):** Isosceles right triangles with legs $12 \times 12$.
$$\text{Area} = 2 \times \left(\frac{1}{2} \times 12 \times 12\right) = 144$$


* **Total Triangle Area:** $4 + 144 = 148 = a^2 + b^2$.
* **Inner Black Shape:** A **rectangle** (not a square) with dimensions $2\sqrt{2} \times 12\sqrt{2}$.
$$\text{Area} = (2\sqrt{2}) \times (12\sqrt{2}) = 48 = 2ab$$



---

### What the Pythagorean Proof Requires

To prove $a^2 + b^2 = c^2$, the four right triangles must be **identical** and rotated cyclically around the four corners:

* Each corner must have one right triangle with legs $a = 2$ and $b = 12$.
* The area of the four triangles combined is $4 \times \left(\frac{1}{2} \times 2 \times 12\right) = 48$.
* The four hypotenuses of length $c = \sqrt{2^2 + 12^2} \approx 12.166$ meet at right angles $(180^\circ - (\alpha + \beta) = 90^\circ)$, forming a **tilted central square** with area $c^2 = 148$.

---

### Why the Numbers Still Add Up

Both dissections partition the total area $(a + b)^2 = 196$ into the algebraic components $(a^2 + b^2) + 2ab$, but the visual roles are inverted:

| Dissection Component | Correct Pythagorean Dissection | Misconfigured Diagram Shown |
| --- | --- | --- |
| **Corner Triangles** | 4 congruent right triangles ($2ab = 48$) | 4 isosceles triangles ($a^2 + b^2 = 148$) |
| **Inner Shape** | **Square** of area $c^2 = a^2 + b^2 = 148$ | **Rectangle** of area $2ab = 48$ |
| **Total Area** | $(a + b)^2 = 196$ | $(a + b)^2 = 196$ |" (Modified: src/engine/geometryEngine.ts, src/App.test.tsx).
- **2026-08-16 13:33:18** — Automated Self-Healing Build Fix (2 files repaired).
- **2026-08-16 13:32:53** — Incremental Edit: "Add an interactive animation speed multiplier slider to GeometryControls" (Modified: src/components/GeometryControls.tsx, src/components/GeometryControls.tsx, src/components/GeometryControls.tsx, src/store/proofStore.ts).
- **2026-08-16 13:30:14** — Codebase Synchronization (Indexed 34 files).
