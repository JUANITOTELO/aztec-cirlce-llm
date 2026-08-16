"""
Unit tests for hybrid fullstack ecosystem detection and auto-proxy scaffolding.
"""

import json
import os
import tempfile
import pytest

from aztec_circle.engine.scaffolder import (
    detect_project_ecosystem,
    scaffold_project,
    VITE_CONFIG_TS_PROXY,
    SRC_TEST_SETUP_TS,
)


def test_detect_project_ecosystem_php_react():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create React frontend files
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump({"name": "test-app", "dependencies": {"react": "^18.0.0"}}, f)
        
        # Create PHP backend file
        backend_dir = os.path.join(tmpdir, "backend")
        os.makedirs(backend_dir, exist_ok=True)
        with open(os.path.join(backend_dir, "index.php"), "w") as f:
            f.write("<?php echo 'api';")

        eco = detect_project_ecosystem(tmpdir)
        assert eco == "php_react"


def test_detect_project_ecosystem_python_react():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create React frontend files
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump({"name": "test-app", "dependencies": {"react": "^18.0.0"}}, f)
        
        # Create Python server file
        with open(os.path.join(tmpdir, "server.py"), "w") as f:
            f.write("print('server')")

        eco = detect_project_ecosystem(tmpdir)
        assert eco == "python_react"


def test_detect_project_ecosystem_lean4_react():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump({"name": "test-app", "dependencies": {"react": "^18.0.0"}}, f)
        with open(os.path.join(tmpdir, "lakefile.lean"), "w") as f:
            f.write("import Lake\nopen Lake DSL")

        eco = detect_project_ecosystem(tmpdir)
        assert eco == "lean4_react"


def test_scaffold_project_injects_proxy_and_test_setup_for_php_react():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal PHP + React structure
        backend_dir = os.path.join(tmpdir, "backend")
        os.makedirs(backend_dir, exist_ok=True)
        with open(os.path.join(backend_dir, "index.php"), "w") as f:
            f.write("<?php echo 'ok';")

        src_dir = os.path.join(tmpdir, "src")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(src_dir, "App.tsx"), "w") as f:
            f.write("export default function App() { return <div>App</div>; }")

        res = scaffold_project(tmpdir)
        assert res.project_type == "php_react"

        # Verify vite.config.ts has proxy
        vite_cfg = os.path.join(tmpdir, "vite.config.ts")
        assert os.path.exists(vite_cfg)
        with open(vite_cfg, "r") as f:
            content = f.read()
            assert "proxy" in content
            assert "http://127.0.0.1:8000" in content

        # Verify src/test/setup.ts is created
        setup_file = os.path.join(tmpdir, "src", "test", "setup.ts")
        assert os.path.exists(setup_file)
        with open(setup_file, "r") as f:
            assert "@testing-library/react" in f.read()
