#!/usr/bin/env python3
"""
Orchestration Pipeline for Autonomous Backend Architecture Swarm
=================================================================
Phase 5: Execution & Logging

Runs the 3-agent pipeline and captures everything to disk for debugging:

    1. Product Manager   → calls DefineRequirements tool
    2. Systems Architect  → calls DesignArchitecture tool  (reads PM's output)
    3. DevOps Engineer    → calls PlanDeployment tool      (reads Architect's output)

Logs saved to swarm_logs/:
    <timestamp>_transcript.txt   → Full conversation log
    <timestamp>_context.json     → Final shared context snapshot

Usage:
    export GROQ_API_KEY='gsk-...'
    python run_swarm.py

    Then paste your product idea when prompted.
"""

import os
import sys
import time

# ── Configure Groq as the LLM backend ──────────────────────────────────
# Set the base URL before ANY imports that might create an OpenAI client.
# Agency Swarm creates its client lazily, but this ensures it's always set.
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

from backend_swarm import agency, product_manager, systems_architect, devops_engineer
from swarm_logger import SwarmRun, extract_context


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(product_idea: str, run: SwarmRun) -> None:
    """
    Execute the three-agent pipeline sequentially, logging each step.

    How handoffs work (this is the key concept):
      - Each agent is called via agency.get_response_sync() with a specific
        recipient_agent. The message tells the agent what to do.
      - Each agent calls its tool, which stores structured data into the
        Agency's shared context (self.context.set).
      - The NEXT agent's tool reads that data (self.context.get) and
        validates it exists before proceeding.
      - This is the "handoff" — not automatic, but explicit tool-based
        data passing through shared context.
    """

    # ── Step 1: Product Manager ────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  STEP 1: Product Manager — defining requirements...")
    print("=" * 72)

    pm_message = (
        f"You are the Product Manager. Here is the product idea:\n\n"
        f"{product_idea}\n\n"
        f"Call the 'define_requirements' tool now with complete details.\n"
        f"Extract the project name, description, features, user roles,\n"
        f"data entities, and acceptance criteria from the idea above."
    )

    t0 = time.time()
    try:
        pm_raw = agency.get_response_sync(
            message=pm_message,
            recipient_agent=product_manager,
        )
        pm_response = str(pm_raw.final_output)
        duration = time.time() - t0
        run.log_step("Product Manager", 1, pm_message, pm_response, duration)
        print(pm_response)
    except Exception as e:
        duration = time.time() - t0
        run.log_error(1, "Product Manager", str(e))
        raise

    # ── Step 2: Systems Architect ──────────────────────────────────────
    print("\n" + "=" * 72)
    print("  STEP 2: Systems Architect — designing architecture...")
    print("=" * 72)

    arch_message = (
        f"You are the Systems Architect. The Product Manager has defined the\n"
        f"requirements and stored them in shared context.\n\n"
        f"Read the requirements from context and call the 'design_architecture'\n"
        f"tool now with your complete architecture design.\n\n"
        f"Product idea for reference:\n{product_idea}"
    )

    t0 = time.time()
    try:
        arch_raw = agency.get_response_sync(
            message=arch_message,
            recipient_agent=systems_architect,
        )
        arch_response = str(arch_raw.final_output)
        duration = time.time() - t0
        run.log_step("Systems Architect", 2, arch_message, arch_response, duration)
        print(arch_response)
    except Exception as e:
        duration = time.time() - t0
        run.log_error(2, "Systems Architect", str(e))
        raise

    # ── Step 3: DevOps Engineer ────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  STEP 3: DevOps Engineer — planning deployment...")
    print("=" * 72)

    devops_message = (
        f"You are the DevOps Engineer. The Systems Architect has designed the\n"
        f"architecture and stored it in shared context.\n\n"
        f"Read the architecture from context and call the 'plan_deployment'\n"
        f"tool now with your complete deployment plan.\n\n"
        f"Product idea for reference:\n{product_idea}"
    )

    t0 = time.time()
    try:
        devops_raw = agency.get_response_sync(
            message=devops_message,
            recipient_agent=devops_engineer,
        )
        devops_response = str(devops_raw.final_output)
        duration = time.time() - t0
        run.log_step("DevOps Engineer", 3, devops_message, devops_response, duration)
        print(devops_response)
    except Exception as e:
        duration = time.time() - t0
        run.log_error(3, "DevOps Engineer", str(e))
        raise


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print()
    print("🚀  AUTONOMOUS BACKEND ARCHITECTURE SWARM")
    print("     Phase 5 — Execution & Logging")
    print()

    # ── API key check (Groq-first) ────────────────────────────────────
    groq_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not groq_key:
        print("❌  GROQ_API_KEY environment variable not set.")
        print()
        print("    Get a free key at https://console.groq.com/keys")
        print("    Then set it and try again:")
        print("    export GROQ_API_KEY='gsk-...'")
        print()
        sys.exit(1)

    # Set the Groq API key (BASE_URL already configured at module level)
    os.environ["OPENAI_API_KEY"] = groq_key

    # ── Get product idea ──────────────────────────────────────────────
    print("Product Idea (paste below, then Ctrl+D or Ctrl+Z when done):")
    print("-" * 72)
    product_lines = []
    try:
        while True:
            line = input()
            product_lines.append(line)
    except EOFError:
        pass

    if not product_lines or all(l.strip() == "" for l in product_lines):
        print("\nNo input provided. Using a demo idea.\n")
        product_idea = (
            "Build a task management SaaS platform where teams can create "
            "projects, assign tasks, track progress with Kanban boards, "
            "and get automated status reports via email."
        )
    else:
        product_idea = "\n".join(product_lines)

    print(f"\n📌  Analyzing: {product_idea[:80]}...\n")

    # ── Create a new run tracker ─────────────────────────────────────
    run = SwarmRun(product_idea)

    try:
        run_pipeline(product_idea, run)

        # ── Save everything to disk ───────────────────────────────────
        print("\n" + "=" * 72)
        print("  💾  SAVING LOGS...")
        print("=" * 72)

        transcript_path = run.save_transcript()
        context = extract_context(agency)
        if context:
            context_path = run.save_context(context)
            print(f"  → Context snapshot: {context_path}")
        else:
            print("  → (shared context not directly accessible for snapshot)")

        # ── Print summary ─────────────────────────────────────────────
        print("\n" + "=" * 72)
        print("  ✅  PIPELINE COMPLETE")
        print("=" * 72)
        run.print_summary()

    except Exception as e:
        # Even on failure, save what we have
        print(f"\n❌  Pipeline error: {e}")
        if run.steps:
            print("  → Saving partial transcript before exiting...")
            run.save_transcript()
        sys.exit(1)


if __name__ == "__main__":
    main()
