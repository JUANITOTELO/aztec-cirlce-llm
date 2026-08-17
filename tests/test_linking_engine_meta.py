import os
import tempfile
import pytest
from aztec_circle.engine.linking_engine import LinkingEngine, FullstackAuditReport, DependencyGraph


def test_audit_fullstack_persistence_detects_gap_and_media_fallbacks():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock fullstack project with IndexedDB, PHP backend, but no sync engine, and an img without onError
        src_dir = os.path.join(tmpdir, "src", "components")
        backend_dir = os.path.join(tmpdir, "backend")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(backend_dir, exist_ok=True)

        # 1. Frontend component with <img> without onError
        comp_file = os.path.join(src_dir, "ProductCard.tsx")
        with open(comp_file, "w", encoding="utf-8") as f:
            f.write("""import React from 'react';
export const ProductCard = ({ product }) => {
  return (
    <div>
      <img src={product.image} alt={product.name} />
      <span>{product.name}</span>
    </div>
  );
};
""")

        # 2. Dexie table
        db_file = os.path.join(tmpdir, "src", "db", "dexie.ts")
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        with open(db_file, "w", encoding="utf-8") as f:
            f.write("import Dexie from 'dexie'; export class AppDB extends Dexie {}")

        # 3. Backend PHP entry
        php_file = os.path.join(backend_dir, "index.php")
        with open(php_file, "w", encoding="utf-8") as f:
            f.write("<?php echo json_encode(['status' => 'ok']);")

        engine = LinkingEngine()
        graph = engine.build_graph(tmpdir)
        audit = engine.audit_fullstack_persistence(tmpdir, graph)

        assert isinstance(audit, FullstackAuditReport)
        assert audit.is_linked is False
        assert len(audit.missing_media_fallbacks) > 0
        assert any("ProductCard.tsx" in m for m in audit.missing_media_fallbacks)
        assert len(audit.unpersisted_client_mutations) > 0
        assert len(audit.recommendations) >= 2


def test_audit_fullstack_persistence_clean_when_sync_and_onerror_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "src", "components")
        engine_dir = os.path.join(tmpdir, "src", "engine")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(engine_dir, exist_ok=True)

        # 1. Component with onError
        comp_file = os.path.join(src_dir, "ProductCard.tsx")
        with open(comp_file, "w", encoding="utf-8") as f:
            f.write("""import React from 'react';
export const ProductCard = ({ product }) => {
  return (
    <div>
      <img src={product.image} alt={product.name} onError={(e) => { e.currentTarget.style.display = 'none'; }} />
    </div>
  );
};
""")

        # 2. Backend sync engine present
        sync_file = os.path.join(engine_dir, "backendSyncEngine.ts")
        with open(sync_file, "w", encoding="utf-8") as f:
            f.write("export class BackendSyncEngine { static sync() {} }")

        engine = LinkingEngine()
        graph = engine.build_graph(tmpdir)
        audit = engine.audit_fullstack_persistence(tmpdir, graph)

        assert audit.is_linked is True
        assert len(audit.missing_media_fallbacks) == 0
        assert len(audit.unpersisted_client_mutations) == 0
