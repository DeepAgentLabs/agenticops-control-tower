"""The standalone runbook walkthrough stays runnable without optional siblings."""

import runpy
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).parents[1] / "examples/runbook_recovery.py"


@pytest.mark.parametrize(
    ("options", "status", "drain_rollback"),
    [
        ({}, "resolved", "not_needed"),
        ({"fail_step": True}, "escalated", "succeeded"),
        ({"fail_verification": True}, "escalated", "not_needed"),
    ],
)
def test_runbook_walkthrough(tmp_path, options, status, drain_rollback):
    demo = runpy.run_path(str(EXAMPLE))
    result = demo["walkthrough"](tmp_path, **options)
    assert result["runbook"] == "staging.dependency_recovery@1.0.0"
    assert (result["status"], result["incident"]) == (status, status)
    assert result["steps"][0]["rollback"] == drain_rollback
    assert result["runtime"]["drained"] is False
    assert result["timeline"][0] == "runbook.previewed"
    assert result["timeline"][-1].startswith(
        "runbook.verification" if not options.get("fail_step") else "runbook.escalated"
    )
