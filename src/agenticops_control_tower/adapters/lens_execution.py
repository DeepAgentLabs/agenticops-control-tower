"""Optional Lens-owned verification, never trust caller-supplied verification claims."""

from typing import Any


def summarize_execution(
    artifact: dict[str, Any], *, trusted_keys: dict[str, bytes], expected_run_id: str
) -> dict[str, Any]:
    try:
        from agenticlens.integrity.execution import ExecutionBundle, execution_summary
    except ImportError:
        return {
            "verification": {
                "status": "unknown",
                "authenticated": False,
                "reason": "Optional Lens execution verifier unavailable",
            },
            "causal_links": [],
        }
    try:
        return dict(
            execution_summary(
                ExecutionBundle.model_validate(artifact),
                trusted_keys=trusted_keys,
                expected_run_id=expected_run_id,
            )
        )
    except (ValueError, TypeError, KeyError):
        return {
            "verification": {
                "status": "failed",
                "authenticated": False,
                "reason": "Invalid Lens execution bundle",
            },
            "causal_links": [],
        }
