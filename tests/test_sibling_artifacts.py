"""Optional integration tests against actual sibling models, not copied fixtures.

Run with the four local sibling packages installed; absent packages skip only
these integration tests. Native artifact JSON remains usable without siblings.
"""

from datetime import datetime, timezone

import pytest

from agenticops_control_tower.adapters import summarize_evidence
from agenticops_control_tower.models.evidence import EvidenceLink


def test_lens_native_run() -> None:
    lens = pytest.importorskip("agenticlens")
    run = lens.Run(application_name="app", status="failed")
    link = EvidenceLink(
        agent_id="a",
        source="agenticlens",
        source_version=lens.__version__,
        artifact_type="run",
        artifact_ref="run:" + run.run_id,
        run_id=run.run_id,
        observed_at=datetime.now(timezone.utc),
    )
    result = summarize_evidence(link, run.model_dump(mode="json"))
    assert result.availability == "available"
    assert result.details["status"] == "failed"


def test_evals_report_and_gate() -> None:
    evals = pytest.importorskip("agentic_evals")
    from agentic_evals.models import EvaluationReport, EvaluationSummary

    report = EvaluationReport(
        suite_name="suite",
        suite_version="1",
        cases=[],
        summary=EvaluationSummary(
            total_cases=0,
            passed_cases=0,
            failed_cases=0,
            pass_rate=0,
            average_score=0,
            average_latency_ms=0,
        ),
    )
    decision = evals.evaluate_gate(report, evals.GateConfig())
    link = EvidenceLink(
        agent_id="a",
        source="agentic-evals",
        source_version=evals.__version__,
        artifact_type="evaluation_report",
        artifact_ref="eval:suite:1",
        observed_at=report.created_at,
    )
    result = summarize_evidence(
        link, report.model_dump(mode="json"), gate=decision.model_dump(mode="json")
    )
    assert result.availability == "available"
    assert result.details["gate"]["passed"] is False
    assert result.details["summary"]["total_cases"] == 0


def test_sidecar_native_decision() -> None:
    sidecar = pytest.importorskip("agentic_sidecar")
    from agentic_sidecar.core.decision import Decision

    decision = Decision(status="BLOCK", risk="HIGH", reason="source policy")
    link = EvidenceLink(
        agent_id="a",
        source="agentic-sidecar",
        source_version=sidecar.__version__,
        artifact_type="decision",
        artifact_ref="decision:1",
        observed_at=datetime.now(timezone.utc),
    )
    result = summarize_evidence(link, decision.model_dump(mode="json"))
    assert result.availability == "available"
    assert result.details["status"] == "BLOCK"


def test_chaos_native_report() -> None:
    chaos = pytest.importorskip("agentic_chaos")
    from agentic_chaos.models.report import ChaosReport

    report = ChaosReport(
        name="experiment",
        start_time=datetime.now(timezone.utc),
        chaos_events=[{"fault": "injected timeout"}],
    )
    link = EvidenceLink(
        agent_id="a",
        source="agentic-chaos",
        source_version=chaos.__version__,
        artifact_type="chaos_report",
        artifact_ref="chaos:" + report.id,
        observed_at=report.start_time,
    )
    result = summarize_evidence(link, report.model_dump(mode="json"))
    assert result.availability == "available"
    assert result.details["event_count"] == 1
    assert result.details["completed"] is False
