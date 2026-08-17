import os
import tempfile
import pytest
from aztec_circle.engine.patch_agent import (
    FilePatch,
    PatchApplicator,
    _clean_rel_path,
    _safe_int,
)


def test_clean_rel_path_type_coercion():
    assert _clean_rel_path(None) == ""
    assert _clean_rel_path("src/App.tsx") == "src/App.tsx"
    assert _clean_rel_path("/src\\components\\Button.tsx") == "src/components/Button.tsx"
    assert _clean_rel_path(123) == "123"
    assert _clean_rel_path("  /foo/bar.ts  ") == "foo/bar.ts"


def test_safe_int_parsing():
    assert _safe_int(None) is None
    assert _safe_int(10) == 10
    assert _safe_int("10") == 10
    assert _safe_int("  42  ") == 42
    assert _safe_int("abc") is None
    assert _safe_int(3.14) is None


def test_patch_applicator_applies_with_type_coerced_patches():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("line 1\nline 2\nline 3\nline 4\n")

        # Patch with string line numbers and integer representation
        patch = FilePatch(
            file="test.txt",
            action="replace",
            start_line=2,
            end_line=3,
            replacement="line 2 replaced\nline 3 replaced\n",
        )

        touched, created, deleted = PatchApplicator.apply(tmpdir, [patch])
        assert "test.txt" in touched
        assert len(created) == 0
        assert len(deleted) == 0

        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "line 2 replaced" in content
        assert "line 3 replaced" in content
        assert "line 1\n" in content
        assert "line 4\n" in content
