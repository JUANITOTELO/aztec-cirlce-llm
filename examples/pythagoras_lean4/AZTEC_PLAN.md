# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: Aztec Software Project  
> **Status**: Active / Synced with Codebase  
> **Last Updated**: 2026-08-18 15:52:10  
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
| `src/engine/gouguEngine.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for gouguEngine |
| `src/engine/theorems/gouguTactics.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for gouguTactics |
| `src/constants/gouguPresets.ts` | Constants (Config) | Static configuration constants for gouguPresets |
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
- **2026-08-18 15:52:10** — Incremental Edit: "Interactive Shell: ls" (Executed: ls).
- **2026-08-18 10:54:10** — Automated Self-Healing Build Fix (2 files repaired).
- **2026-08-18 10:53:42** — Incremental Edit: "[plugin:vite:esbuild] Transform failed with 1 error:
/home/coorti/.aztec/examples/pythagoras_lean4/src/engine/theorems/binomialTactics.ts:42:0: ERROR: Unexpected "}"
/home/coorti/.aztec/examples/pythagoras_lean4/src/engine/theorems/binomialTactics.ts:42:0
Unexpected "}"
40 |    });
41 |  }
42 |  }
   |  ^
43 |" (Modified: src/engine/theorems/binomialTactics.ts).
- **2026-08-18 10:53:32** — Incremental Edit: "on the binomial diagram we have this: Inaccuracies & Interface QuirksAngle Misnomer ("45° Diagonal Slicing"):The card titles the diagram 45° Diagonal Slicing. However, because $a = 6$ and $b = 3$, the diagonal slicing through each $6 \times 3$ rectangle is at $\arctan(3/6) \approx 26.6^\circ$ (or $63.4^\circ$), not $45^\circ$. The slice is only $45^\circ$ when $a = b$.Euclid II.4 vs. Diagonal Slicing:This diagram is the classical Euclidean / Yang Hui grid dissection (partitioning along the $x=a$ and $y=b$ coordinate lines into two squares and two rectangles). Diagonal slicing of the whole square refers to slicing corner-to-corner across the main diagonal.Simulated Lean State Explorer (UI Mockup Artifacts):The Tactic State Explorer and Proof Tactic Tree display UI mockups rather than raw Lean 4 Infoview outputs:h_geom : area((a+b)^2) = 81 uses high-level pseudocode rather than real Lean propositions.h_quads : a^2=36, b^2=9, 2ab=36 bundles multiple equations into a single comma-separated hypothesis type, which is invalid syntax in Lean 4.by geometr... in the proof tree is a placeholder rather than a standard Mathlib tactic." (Modified: src/components/DissectionCanvas.tsx, src/constants/binomialPresets.ts, src/engine/binomialEngine.ts, src/engine/theorems/binomialTactics.ts).
- **2026-08-18 10:44:54** — Incremental Edit: "translate the names of the gougu theorem to English" (Modified: src/constants/gouguPresets.ts, src/engine/theorems/gouguTactics.ts, src/engine/gouguEngine.ts, src/engine/gouguEngine.ts, src/engine/gouguEngine.ts, src/engine/gouguEngine.ts, src/components/GeometryControls.tsx, src/components/Header.tsx).
- **2026-08-18 10:44:01** — Automated Self-Healing Build Fix (1 files repaired).
- **2026-08-18 10:43:11** — Incremental Edit: "test the lean 4 formal proof" (Modified: src/App.test.tsx; Executed: npm test -- --run).
- **2026-08-18 10:42:04** — Incremental Edit: "[plugin:vite:react-babel] /home/coorti/.aztec/examples/pythagoras_lean4/src/components/LeanCodeGenerator.tsx: Unexpected token (65:2)
  67 |
/home/coorti/.aztec/examples/pythagoras_lean4/src/components/LeanCodeGenerator.tsx:65:2
63 |      </Card>
64 |    );
65 |    );
   |    ^
66 |  };
67 |" (Modified: src/components/LeanCodeGenerator.tsx).
- **2026-08-18 10:41:50** — Incremental Edit: "the gougu and pythagoras lean 4 specifications seems to be the same file making them wrong, they should be separate files" (Modified: src/engine/proofExporter.ts, src/components/LeanCodeGenerator.tsx).
- **2026-08-18 10:40:09** — Incremental Edit: "the lean 4 formal specification of the Gougu theorem is wrong" (Modified: src/engine/proofExporter.ts).
- **2026-08-18 10:38:04** — Incremental Edit: "The visual distortion in the first image is caused by **coordinate transformation and rotation bugs** when attempting to procedurally generate the classical Zhao Shuang Chord Diagram (*Zhao Shuang Xian Tu*).

While the underlying values ($a=3$, $b=12$, $(b-a)^2=81$, $c^2=153$) are mathematically consistent, the geometry engine misplaces the triangle vertices.

---

### Key Programming Bugs

* **Broken Cyclic Rotation ($90^\circ$ Transform):**
In the classical construction, all four right triangles (**朱实**) are identical copies rotated cyclically around the center by $0^\circ, 90^\circ, 180^\circ,$ and $270^\circ$. In the code, the rotation matrix or origin was applied inconsistently, causing each triangle to point in arbitrary orientations.
* **Chirality & Reflection Bug (Sign Errors):**
Triangles 2 and 4 appear reflected (mirrored across an axis) rather than rotated, flipping the positions of leg $a$ (勾) and leg $b$ (股).
* **Collinearity & Vertex-Sharing Failure:**
The inner square of side $(b - a)$ exists because along each side, the long leg of one triangle ($b$) overlaps the short leg of the next ($a$), leaving $b - a$ exposed ($12 - 3 = 9$). Because the vertices were computed with independent absolute offsets rather than chained collinear vectors, gaps and protruding "fins" (the red/orange slivers) were created.
* **Non-Square Outer Boundary:**
The four hypotenuses ($c$) must connect tip-to-tail to form a continuous, tilted outer square of area $c^2 = 153$. Due to misaligned vertices, the outer perimeter forms an irregular 8-sided polygon.

---

### Correct Coordinate Generation (Python / JavaScript Logic)

To draw this diagram correctly, center the diagram at the origin $(0, 0)$ and construct the 4 triangles using a single standard triangle rotated by $k \times 90^\circ$:

```python
import numpy as np

a = 3   # 勾 (Gou - short leg)
b = 12  # 股 (Gu - long leg)

# Center of the inner square is (0, 0)
d = (b - a) / 2  # half-width of the inner square (4.5)

# Vertices of the base triangle (in standard orientation)
# 1. Outer corner (right angle): (d + a, -d)
# 2. Inner corner: (d, -d)
# 3. Outer hypotenuse tip: (d, -d + b)
base_triangle = np.array([
    [ d + a, -d     ],
    [ d,     -d     ],
    [ d,     -d + b ]
])

# Generate all 4 triangles by rotating 0°, 90°, 180°, 270°
triangles = []
for k in range(4):
    theta = k * (np.pi / 2)
    rot_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    rotated_tri = base_triangle @ rot_matrix.T
    triangles.append(rotated_tri)

# Inner square vertices (黄方)
inner_square = np.array([
    [-d, -d],
    [ d, -d],
    [ d,  d],
    [-d,  d]
])

```

Applying this cyclic transform ensures the outer hypotenuses automatically form a closed, tilted square ($c^2 = 153$) enclosing the central $(b - a)^2$ square without overlaps or gaps." (Modified: src/engine/gouguEngine.ts, src/components/DissectionCanvas.tsx).
- **2026-08-18 10:28:46** — Incremental Edit: "chunk-RQRZJDNV.js?v=20ceec6f:21549 Download the React DevTools for a better development experience: https://reactjs.org/link/react-devtools
leanKernelSimulator.ts:26 Uncaught ReferenceError: a is not defined
    at leanKernelSimulator.ts:26:51
    at Array.map (<anonymous>)
    at LeanKernelSimulator.generateTactics (leanKernelSimulator.ts:25:20)
    at new ProofStore (proofStore.ts:14:41)
    at proofStore.ts:109:27" (Modified: src/engine/leanKernelSimulator.ts, src/store/proofStore.ts).
- **2026-08-18 10:28:10** — Automated Self-Healing Build Fix (1 files repaired).
- **2026-08-18 10:27:43** — Incremental Edit: "Module Consensus: let's add The Gougu Theorem too" (Modified: src/constants/gouguPresets.ts, src/engine/theorems/gouguTactics.ts, src/engine/gouguEngine.ts, src/types/proofState.ts, src/engine/geometryEngine.ts, src/engine/leanKernelSimulator.ts, src/store/proofStore.ts, src/components/Header.tsx, src/components/GeometryControls.tsx, src/components/LeanCodeGenerator.tsx, src/App.tsx).
- **2026-08-18 10:27:43** — Automated Self-Healing Build Fix (5 files repaired).
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
