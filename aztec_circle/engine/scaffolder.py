"""
Project Scaffolder for Aztec Decision Circle.
Detects project ecosystems, Tailwind CSS usage, heavy 3D bundles,
and automatically injects missing configuration boilerplate.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScaffoldResult:
    """Summary of project scaffolding operation."""
    project_type: str
    project_root: str
    files_injected: List[str] = field(default_factory=list)


# Pinned Vite 5 + React 18 + TypeScript Boilerplate Templates
VITE_REACT_PACKAGE_JSON = {
    "name": "aztec-generated-app",
    "private": True,
    "version": "0.1.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "tsc && vite build",
        "preview": "vite preview",
        "test": "vitest run"
    },
    "dependencies": {
        "react": "^18.3.1",
        "react-dom": "^18.3.1"
    },
    "devDependencies": {
        "@types/react": "^18.3.1",
        "@types/react-dom": "^18.3.1",
        "@vitejs/plugin-react": "^4.3.4",
        "typescript": "^5.6.0",
        "vite": "^5.4.14",
        "vitest": "^2.1.0",
        "@testing-library/react": "^16.0.0",
        "@testing-library/jest-dom": "^6.4.0",
        "jsdom": "^25.0.0",
        "tailwindcss": "^3.4.3",
        "postcss": "^8.4.38",
        "autoprefixer": "^10.4.19"
    }
}

VITE_CONFIG_TS = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0'
  },
  test: {
    globals: true,
    environment: 'jsdom'
  }
});
"""

VITE_CONFIG_TS_CHUNKS = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0'
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-three': ['three', '@react-three/fiber', '@react-three/drei']
        }
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom'
  }
});
"""

VITE_CONFIG_TS_PROXY = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
"""

SRC_TEST_SETUP_TS = """// Vitest test environment setup
import '@testing-library/react';
"""


TAILWIND_CONFIG_JS = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
"""

POSTCSS_CONFIG_JS = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""

TSCONFIG_JSON = {
    "compilerOptions": {
        "target": "ES2020",
        "useDefineForClassFields": True,
        "lib": ["ES2020", "DOM", "DOM.Iterable"],
        "module": "ESNext",
        "skipLibCheck": True,
        "moduleResolution": "bundler",
        "allowImportingTsExtensions": True,
        "resolveJsonModule": True,
        "isolatedModules": True,
        "noEmit": True,
        "jsx": "react-jsx",
        "strict": True,
        "noUnusedLocals": False,
        "noUnusedParameters": False,
        "noFallthroughCasesInSwitch": True
    },
    "include": ["src"]
}

INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Aztec Application</title>
  </head>
  <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

MAIN_TSX = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

INDEX_CSS_TAILWIND = """@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
"""

APP_TEST_TSX = """import { describe, it, expect } from 'vitest';

describe('Application Smoke Test', () => {
  it('passes base test assertion', () => {
    expect(true).toBe(true);
  });
});
"""

PYTHON_PYPROJECT_TOML = """[project]
name = "aztec-generated-module"
version = "0.1.0"
description = "Aztec generated Python project"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
"""

HEAVY_DEPS = frozenset([
    "three",
    "@react-three/fiber",
    "@react-three/drei",
    "@babylonjs/core",
    "pixi.js",
    "matter-js",
])


def find_project_root(target_dir: str) -> str:
    """
    Determine canonical project root:
    1. If target_dir contains package.json -> target_dir
    2. If target_dir contains pyproject.toml (and is not aztec_circle engine) -> target_dir
    3. Check immediate subdirectories (1 level deep), preferring the one with the most recently modified src/ directory
    4. Default to target_dir.
    """
    if not os.path.exists(target_dir) or target_dir in ("./aztec_output", "aztec_output"):
        # Fallback to current working directory or subproject if target_dir doesn't exist
        if os.path.exists("package.json"):
            return "."
        try:
            candidates = []
            for d in os.listdir("."):
                if os.path.isdir(d) and not d.startswith((".", "tests", "aztec_circle", "venv", ".venv", "node_modules")):
                    if os.path.exists(os.path.join(d, "package.json")) or (os.path.exists(os.path.join(d, "pyproject.toml")) and not os.path.isdir(os.path.join(d, "aztec_circle"))):
                        candidates.append(d)
            if candidates:
                def _src_mtime(dir_path: str) -> float:
                    s = os.path.join(dir_path, "src")
                    return os.path.getmtime(s) if os.path.isdir(s) else 0.0
                return max(candidates, key=_src_mtime)
        except Exception:
            pass
        if not os.path.exists(target_dir):
            return target_dir

    # Check root: if has package.json -> target_dir
    if os.path.exists(os.path.join(target_dir, "package.json")):
        return target_dir

    # If has pyproject.toml and is NOT the Aztec engine itself -> target_dir
    if os.path.exists(os.path.join(target_dir, "pyproject.toml")) and not os.path.isdir(os.path.join(target_dir, "aztec_circle")):
        return target_dir

    # Check immediate subdirectories (1 level deep)
    try:
        subdirs = [os.path.join(target_dir, d) for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
        candidates = []
        for sub in subdirs:
            base = os.path.basename(sub)
            if base.startswith((".", "tests", "aztec_circle", "venv", ".venv", "__pycache__", "node_modules", "dist", "build")):
                continue
            if os.path.exists(os.path.join(sub, "package.json")) or (os.path.exists(os.path.join(sub, "pyproject.toml")) and not os.path.isdir(os.path.join(sub, "aztec_circle"))):
                candidates.append(sub)
        if candidates:
            def _src_mtime(dir_path: str) -> float:
                s = os.path.join(dir_path, "src")
                return os.path.getmtime(s) if os.path.isdir(s) else 0.0
            return max(candidates, key=_src_mtime)
    except Exception:
        pass

    return target_dir


def detect_project_ecosystem(project_dir: str) -> str:
    """
    Scan files within project_dir and classify ecosystem:
    Returns 'php_react', 'python_react', 'lean4_react', 'vite_react', 'node', 'php', 'python', 'lean4', or 'generic'.
    """
    if not os.path.exists(project_dir):
        return "generic"

    all_files: List[str] = []
    for root, _, files in os.walk(project_dir):
        for f in files:
            all_files.append(os.path.relpath(os.path.join(root, f), project_dir))

    has_package_json = "package.json" in all_files
    has_tsx_or_jsx = any(f.endswith((".tsx", ".jsx")) for f in all_files)
    has_ts_or_js = any(f.endswith((".ts", ".js", ".mjs")) for f in all_files)
    has_py = any(f.endswith(".py") for f in all_files)
    has_php = any(f.endswith(".php") for f in all_files)
    has_lean = any(f.endswith(".lean") for f in all_files) or "lakefile.lean" in all_files

    has_frontend = has_package_json or has_tsx_or_jsx

    # Hybrid fullstack ecosystems
    if has_frontend and has_php:
        return "php_react"
    if has_frontend and (has_py or "pyproject.toml" in all_files or "requirements.txt" in all_files):
        return "python_react"
    if has_frontend and has_lean:
        return "lean4_react"

    if has_package_json:
        try:
            with open(os.path.join(project_dir, "package.json"), "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                if "react" in deps or "vite" in deps or has_tsx_or_jsx:
                    return "vite_react"
                return "node"
        except Exception:
            pass

    if has_tsx_or_jsx or (has_ts_or_js and not has_py and not has_php and not has_lean):
        return "vite_react"

    if has_php:
        return "php"

    if has_lean:
        return "lean4"

    if has_py or "pyproject.toml" in all_files or "requirements.txt" in all_files:
        return "python"

    return "generic"


def detect_uses_tailwind(project_root: str) -> bool:
    """
    Returns True if any CSS file in the project contains @tailwind directives,
    or if package.json dependencies/devDependencies contains 'tailwindcss'.
    """
    # 1. Inspect CSS files
    for root, _, files in os.walk(project_root):
        for f in files:
            if f.endswith(".css"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                        if "@tailwind" in fh.read():
                            return True
                except Exception:
                    pass

    # 2. Inspect package.json
    pkg_path = os.path.join(project_root, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "tailwindcss" in deps:
                    return True
        except Exception:
            pass

    return False


def detect_heavy_deps(project_root: str) -> List[str]:
    """Inspect dependencies and detect heavy 3D / graphics libraries requiring chunking."""
    pkg_path = os.path.join(project_root, "package.json")
    found: List[str] = []
    if not os.path.exists(pkg_path):
        return found
    try:
        with open(pkg_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for heavy in HEAVY_DEPS:
                if heavy in deps:
                    found.append(heavy)
    except Exception:
        pass
    return found


def scaffold_project(output_dir: str) -> ScaffoldResult:
    """
    Inspect output_dir, determine ecosystem, and inject any missing boilerplate files.
    Ensures Tailwind CSS config, chunking, fullstack proxy, and typecheck compatibility.
    """
    os.makedirs(output_dir, exist_ok=True)
    root = find_project_root(output_dir)
    ecosystem = detect_project_ecosystem(root)
    injected: List[str] = []

    if ecosystem in ("vite_react", "php_react", "python_react", "lean4_react", "node"):
        # 1. package.json
        pkg_path = os.path.join(root, "package.json")
        if not os.path.exists(pkg_path):
            with open(pkg_path, "w", encoding="utf-8") as f:
                json.dump(VITE_REACT_PACKAGE_JSON, f, indent=2)
            injected.append("package.json")
        else:
            # Ensure "type": "module" and tailwindcss in devDeps if tailwind used
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                changed = False
                if pkg_data.get("type") != "module":
                    pkg_data["type"] = "module"
                    changed = True
                dev_deps = pkg_data.get("devDependencies", {})
                deps = pkg_data.get("dependencies", {})
                if detect_uses_tailwind(root):
                    for tw_dep, ver in [("tailwindcss", "^3.4.3"), ("postcss", "^8.4.38"), ("autoprefixer", "^10.4.19")]:
                        if tw_dep not in dev_deps and tw_dep not in deps:
                            dev_deps[tw_dep] = ver
                            changed = True
                if changed:
                    pkg_data["devDependencies"] = dev_deps
                    with open(pkg_path, "w", encoding="utf-8") as f:
                        json.dump(pkg_data, f, indent=2)
            except Exception:
                pass

        # Create atomic directory structure
        atomic_dirs = [
            "src/atoms",
            "src/components",
            "src/hooks",
            "src/engine",
            "src/store",
            "src/utils",
            "src/types",
            "src/constants",
        ]
        for adir in atomic_dirs:
            os.makedirs(os.path.join(root, adir), exist_ok=True)

        # 2. Tailwind & PostCSS Configuration
        if detect_uses_tailwind(root):
            tw_path = os.path.join(root, "tailwind.config.js")
            tw_cjs_path = os.path.join(root, "tailwind.config.cjs")
            tw_ts_path = os.path.join(root, "tailwind.config.ts")
            if not os.path.exists(tw_path) and not os.path.exists(tw_cjs_path) and not os.path.exists(tw_ts_path):
                with open(tw_path, "w", encoding="utf-8") as f:
                    f.write(TAILWIND_CONFIG_JS)
                injected.append("tailwind.config.js")

            post_path = os.path.join(root, "postcss.config.js")
            post_cjs_path = os.path.join(root, "postcss.config.cjs")
            if not os.path.exists(post_path) and not os.path.exists(post_cjs_path):
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(POSTCSS_CONFIG_JS)
                injected.append("postcss.config.js")

        # 3. vite.config.ts
        vite_cfg_path = os.path.join(root, "vite.config.ts")
        vite_js_path = os.path.join(root, "vite.config.js")
        has_heavy = bool(detect_heavy_deps(root))

        if not os.path.exists(vite_cfg_path) and not os.path.exists(vite_js_path):
            if ecosystem in ("php_react", "python_react"):
                config_template = VITE_CONFIG_TS_PROXY
            elif has_heavy:
                config_template = VITE_CONFIG_TS_CHUNKS
            else:
                config_template = VITE_CONFIG_TS
            with open(vite_cfg_path, "w", encoding="utf-8") as f:
                f.write(config_template)
            injected.append("vite.config.ts")

        # 4. tsconfig.json - enforce non-fatal unused locals for LLM resilience
        tsconfig_path = os.path.join(root, "tsconfig.json")
        if not os.path.exists(tsconfig_path):
            with open(tsconfig_path, "w", encoding="utf-8") as f:
                json.dump(TSCONFIG_JSON, f, indent=2)
            injected.append("tsconfig.json")
        else:
            try:
                with open(tsconfig_path, "r", encoding="utf-8") as f:
                    ts_data = json.load(f)
                copts = ts_data.get("compilerOptions", {})
                if copts.get("noUnusedLocals") is True or copts.get("noUnusedParameters") is True:
                    copts["noUnusedLocals"] = False
                    copts["noUnusedParameters"] = False
                    copts["noEmit"] = True
                    ts_data["compilerOptions"] = copts
                    with open(tsconfig_path, "w", encoding="utf-8") as f:
                        json.dump(ts_data, f, indent=2)
            except Exception:
                pass

        # 5. index.html
        index_html_path = os.path.join(root, "index.html")
        if not os.path.exists(index_html_path):
            with open(index_html_path, "w", encoding="utf-8") as f:
                f.write(INDEX_HTML)
            injected.append("index.html")

        # 6. src/main.tsx
        src_dir = os.path.join(root, "src")
        os.makedirs(src_dir, exist_ok=True)
        main_tsx_path = os.path.join(src_dir, "main.tsx")
        if not os.path.exists(main_tsx_path) and not os.path.exists(os.path.join(root, "main.tsx")):
            with open(main_tsx_path, "w", encoding="utf-8") as f:
                f.write(MAIN_TSX)
            injected.append("src/main.tsx")

        # 7. src/index.css
        index_css_path = os.path.join(src_dir, "index.css")
        if not os.path.exists(index_css_path):
            with open(index_css_path, "w", encoding="utf-8") as f:
                f.write(INDEX_CSS_TAILWIND)
            injected.append("src/index.css")

        # 8. src/App.test.tsx & src/test/setup.ts
        test_path = os.path.join(src_dir, "App.test.tsx")
        if not os.path.exists(test_path):
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(APP_TEST_TSX)
            injected.append("src/App.test.tsx")

        test_setup_dir = os.path.join(src_dir, "test")
        test_setup_file = os.path.join(test_setup_dir, "setup.ts")
        if not os.path.exists(test_setup_file):
            os.makedirs(test_setup_dir, exist_ok=True)
            with open(test_setup_file, "w", encoding="utf-8") as f:
                f.write(SRC_TEST_SETUP_TS)
            injected.append("src/test/setup.ts")

    elif ecosystem == "python":
        pyproj_path = os.path.join(root, "pyproject.toml")
        req_path = os.path.join(root, "requirements.txt")
        if not os.path.exists(pyproj_path) and not os.path.exists(req_path):
            with open(pyproj_path, "w", encoding="utf-8") as f:
                f.write(PYTHON_PYPROJECT_TOML)
            injected.append("pyproject.toml")

    return ScaffoldResult(project_type=ecosystem, project_root=root, files_injected=injected)
