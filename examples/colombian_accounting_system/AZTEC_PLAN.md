# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: Aztec Software Project  
> **Status**: Active / Synced with Codebase  
> **Last Updated**: 2026-08-16 14:55:06  
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
| `index.html` | Source | Module implementation for index |
| `package.json` | Config / Build | Node dependencies & scripts manifest |
| `postcss.config.js` | Source | Module implementation for postcss.config |
| `src/App.test.tsx` | Test Suite | Unit tests for App |
| `src/App.tsx` | Coordinator | Main application coordinator & view shell |
| `src/atoms/Badge.tsx` | Atom (UI Primitive) | Atomic UI primitive for Badge |
| `src/atoms/Button.tsx` | Atom (UI Primitive) | Atomic UI primitive for Button |
| `src/components/Header.tsx` | Component (Composite) | Composite panel for Header |
| `src/components/IncomeStatementReport.tsx` | Component (Composite) | Composite panel for IncomeStatementReport |
| `src/components/PucExplorer.tsx` | Component (Composite) | Composite panel for PucExplorer |
| `src/components/TaxCalculatorPanel.tsx` | Component (Composite) | Composite panel for TaxCalculatorPanel |
| `src/components/TrialBalanceReport.tsx` | Component (Composite) | Composite panel for TrialBalanceReport |
| `src/components/VoucherComposer.tsx` | Component (Composite) | Composite panel for VoucherComposer |
| `src/components/VoucherHistoryTable.tsx` | Component (Composite) | Composite panel for VoucherHistoryTable |
| `src/constants/pucColombia.ts` | Constants (Config) | Static configuration constants for pucColombia |
| `src/engine/balanceCalculator.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for balanceCalculator |
| `src/engine/financialStatements.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for financialStatements |
| `src/engine/taxSettlementEngine.ts` | Engine (Domain Logic) | Pure mathematical & domain algorithms for taxSettlementEngine |
| `src/index.css` | Source | Tailwind base directives & global design tokens |
| `src/main.tsx` | Coordinator | React DOM entry root & style bootstrap |
| `src/store/accountingStore.ts` | Store (State Slice) | Global state slice for accountingStore |
| `src/store/authStore.ts` | Store (State Slice) | Global state slice for authStore |
| `src/types/accounting.ts` | Types (Interfaces) | Type definitions & data contracts for accounting |
| `src/types/auth.ts` | Types (Interfaces) | Type definitions & data contracts for auth |
| `src/types/puc.ts` | Types (Interfaces) | Type definitions & data contracts for puc |
| `src/types/tax.ts` | Types (Interfaces) | Type definitions & data contracts for tax |
| `src/utils/mathPrecision.ts` | Utils (Pure Helpers) | Module implementation for mathPrecision |
| `tailwind.config.js` | Config / Build | Tailwind CSS utility & theme configuration |
| `tsconfig.json` | Config / Build | TypeScript strict compiler options |
| `vite.config.ts` | Config / Build | Vite dev server & build bundler configuration |

---

## 📝 Change Log & Iteration History
- **2026-08-16 14:55:06** — Codebase Synchronization (Indexed 30 files).
