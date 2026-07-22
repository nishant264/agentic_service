"""
Swarm Conversation Logger
=========================
Captures everything the agents say to each other so you can debug,
analyze, or replay a pipeline run.

Saves two artifacts per run in the `swarm_logs/` directory:
  1. <timestamp>_transcript.txt  — human-readable conversation log
  2. <timestamp>_context.json     — final shared context snapshot
"""

import json
import os
from datetime import datetime
from typing import Any


# ── Directory setup ──────────────────────────────────────────────────────

LOG_DIR = "swarm_logs"


def _ensure_log_dir():
    """Create the log directory if it doesn't exist."""
    os.makedirs(LOG_DIR, exist_ok=True)


def _timestamp() -> str:
    """Unique, sortable timestamp string used as a run ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ── Per-run state ────────────────────────────────────────────────────────

# Each pipeline execution produces one "run" that accumulates entries.
# Reset this at the start of a new pipeline.

class SwarmRun:
    """
    Tracks a single pipeline execution.

    Usage:
        run = SwarmRun()
        run.log_step(agent_name="Product Manager", message="...", response="...")
        run.save()
    """

    def __init__(self, product_idea: str):
        self.run_id = _timestamp()
        self.product_idea = product_idea
        self.steps: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []

    def log_step(
        self,
        agent_name: str,
        step_number: int,
        message: str,
        response: str,
        duration_seconds: float,
    ) -> None:
        """Record one agent interaction."""
        self.steps.append({
            "step": step_number,
            "agent": agent_name,
            "message_sent": message.strip(),
            "response_received": response.strip(),
            "duration_seconds": round(duration_seconds, 2),
        })

    def log_error(self, step: int, agent: str, error: str) -> None:
        """Record an error that occurred during a step."""
        self.errors.append({
            "step": step,
            "agent": agent,
            "error": str(error),
        })

    # ── Saving ────────────────────────────────────────────────────────

    def save_transcript(self) -> str:
        """Write a human-readable transcript of the conversation."""
        _ensure_log_dir()
        path = os.path.join(LOG_DIR, f"{self.run_id}_transcript.txt")

        lines = [
            "=" * 72,
            "  AUTONOMOUS BACKEND ARCHITECTURE SWARM",
            f"  Run ID : {self.run_id}",
            f"  Date   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 72,
            "",
            "PRODUCT IDEA:",
            self.product_idea.strip(),
            "",
        ]

        for step in self.steps:
            lines.append("-" * 72)
            lines.append(
                f"STEP {step['step']}: {step['agent']} "
                f"({step['duration_seconds']}s)"
            )
            lines.append("-" * 72)
            lines.append("PROMPT SENT:")
            lines.append(step["message_sent"])
            lines.append("")
            lines.append("AGENT RESPONSE:")
            lines.append(step["response_received"])
            lines.append("")

        if self.errors:
            lines.append("=" * 72)
            lines.append("  ERRORS ENCOUNTERED")
            lines.append("=" * 72)
            for err in self.errors:
                lines.append(f"  Step {err['step']} | {err['agent']}: {err['error']}")

        lines.append("=" * 72)
        lines.append("  END OF TRANSCRIPT")
        lines.append("=" * 72)

        with open(path, "w") as f:
            f.write("\n".join(lines))

        return path

    def save_context(self, context: dict[str, Any]) -> str:
        """Save the final shared context as a pretty-printed JSON file."""
        _ensure_log_dir()
        path = os.path.join(LOG_DIR, f"{self.run_id}_context.json")

        with open(path, "w") as f:
            json.dump(context, f, indent=2, default=str)

        return path

    def print_summary(self) -> None:
        """Print a quick summary of the run to the console."""
        print()
        print(f"  📁 Transcript saved → swarm_logs/{self.run_id}_transcript.txt")
        print(f"  📁 Context snapshot → swarm_logs/{self.run_id}_context.json")
        print()
        print(f"  Steps completed: {len(self.steps)}")
        total_time = sum(s["duration_seconds"] for s in self.steps)
        print(f"  Total duration : {total_time:.1f}s")
        if self.errors:
            print(f"  Errors         : {len(self.errors)} ⚠️")
        else:
            print(f"  Errors         : 0 ✅")


# ── Simple helper to extract context from the agency after a run ────────

def extract_context(agency: Any) -> dict[str, Any]:
    """
    Attempt to read known keys from the agency's shared context.

    Agency Swarm v1 stores shared state internally.  We read the keys
    that our tools set:
      - product_requirements
      - architecture_design
      - deployment_plan

    If the context isn't directly readable, returns an empty dict.
    """
    # The shared state is typically stored on the Agency instance.
    # Different Agency Swarm versions store it differently:
    #
    #   v1.6+ : agency.shared_state  (dict-like)
    #   v1.7+ : agency._shared_context  (internal)
    #
    # We try both, and fall back gracefully.
    known_keys = [
        "product_requirements",
        "architecture_design",
        "deployment_plan",
    ]

    context: dict[str, Any] = {}

    # Try to find the shared state
    shared = None
    if hasattr(agency, "shared_state"):
        shared = agency.shared_state
    elif hasattr(agency, "_shared_context"):
        shared = agency._shared_context

    if shared is not None and hasattr(shared, "get"):
        for key in known_keys:
            value = shared.get(key)
            if value is not None:
                context[key] = value

    return context
