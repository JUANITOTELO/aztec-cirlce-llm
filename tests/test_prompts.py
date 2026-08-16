"""
Tests for prompt registry and template caching.
"""

import pytest
from aztec_circle.prompts.registry import get_raw_template, render


def test_render_all_standard_templates():
    templates = [
        "youth_chaos",
        "youth_advocate",
        "peer_drafter",
        "elder_security",
        "elder_structural",
    ]
    for name in templates:
        rendered = render(name)
        assert len(rendered) > 50
        assert "JSON" in rendered


def test_render_with_variables():
    rendered = render("peer_drafter_loop", loop_index="2")
    assert "Iteration 2" in rendered


def test_missing_template_raises_error():
    with pytest.raises(FileNotFoundError):
        get_raw_template("non_existent_prompt_template_xyz")
