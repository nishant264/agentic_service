"""
Streamlit Web UI for Autonomous Backend Architecture Swarm
==========================================================
Run the 3-agent pipeline from your browser with real-time
progress tracking and downloadable log artifacts.

Usage:
    streamlit run swarm_ui.py
"""

import os
import time

import streamlit as st

from backend_swarm import agency, product_manager, systems_architect, devops_engineer
from swarm_logger import SwarmRun, extract_context


# ── Page config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Backend Architecture Swarm",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Agent status badges */
    .status-waiting {
        color: #6b7280;
        font-size: 0.85rem;
    }
    .status-running {
        color: #3b82f6;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-complete {
        color: #22c55e;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-error {
        color: #ef4444;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .agent-card {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state ────────────────────────────────────────────────────────

def init_state():
    if "run_history" not in st.session_state:
        st.session_state.run_history = []
    if "api_key_set" not in st.session_state:
        st.session_state.api_key_set = False


init_state()


# ── Sidebar ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🔑 API Configuration")

    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Free key from console.groq.com — used only for this session.",
        placeholder="gsk-...",
    )

    if groq_api_key:
        # Configure Groq as the LLM backend
        os.environ["OPENAI_API_KEY"] = groq_api_key
        os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
        st.session_state.api_key_set = True
        st.success("✅ Groq configured!")
    else:
        st.session_state.api_key_set = False
        st.info("Enter your Groq API key to proceed.")
        st.markdown(
            "[Get a free key →](https://console.groq.com/keys)",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 📁 Run History")

    show_history = st.checkbox("Show past runs", value=False)
    if show_history and st.session_state.run_history:
        for i, entry in enumerate(st.session_state.run_history, 1):
            with st.expander(f"Run {i} — {entry['project'][:40]}..."):
                st.markdown(f"**Steps:** {entry['steps']}")
                st.markdown(f"**Time:** {entry['duration']:.1f}s")
                st.markdown(f"**Errors:** {'⚠️ ' + str(entry['errors']) if entry['errors'] else '✅ None'}")
                if entry.get("transcript_path"):
                    st.markdown(f"📄 `{entry['transcript_path']}`")
    elif show_history:
        st.caption("No runs yet.")

    if st.button("Clear History", use_container_width=True):
        st.session_state.run_history = []
        st.rerun()


# ── Main content ─────────────────────────────────────────────────────────

st.title("🤖 Autonomous Backend Architecture Swarm")
st.markdown(
    "Three AI agents collaborate to turn a product idea into "
    "a complete backend plan — **requirements → architecture → deployment**."
)

# Agent info bar
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.info("**📋 Product Manager**\n\nFeatures, roles, acceptance criteria")
with col_b:
    st.info("**🏗️ Systems Architect**\n\nServices, APIs, data models, tech stack")
with col_c:
    st.info("**⚙️ DevOps Engineer**\n\nCI/CD, infrastructure, monitoring")

st.markdown("---")

# ── Input ────────────────────────────────────────────────────────────────

idea = st.text_area(
    "Describe your product idea",
    height=120,
    placeholder=(
        "e.g., Build a task management SaaS platform where teams can create "
        "projects, assign tasks, track progress with Kanban boards, "
        "and get automated status reports via email."
    ),
    help="Be as specific as possible about the features and users.",
)

run_button = st.button(
    "🚀 Run Swarm",
    type="primary",
    use_container_width=True,
    disabled=not (st.session_state.api_key_set and idea.strip()),
)

st.markdown("---")

# ── Results area ─────────────────────────────────────────────────────────

results_placeholder = st.empty()

if run_button and st.session_state.api_key_set and idea.strip():
    with results_placeholder.container():
        st.markdown("## 📊 Pipeline Progress")
        progress_bar = st.progress(0, text="Initializing...")

        # Status placeholders for each agent
        status_cols = st.columns(3)

        def status_html(agent, emoji, status_text, css_class):
            return f"<div class='agent-card'><strong>{emoji} {agent}</strong><br><span class='{css_class}'>{status_text}</span></div>"

        pm_status = status_cols[0].empty()
        arch_status = status_cols[1].empty()
        devops_status = status_cols[2].empty()

        pm_status.markdown(status_html("Product Manager", "📋", "⏳ Waiting...", "status-waiting"), unsafe_allow_html=True)
        arch_status.markdown(status_html("Systems Architect", "🏗️", "⏳ Waiting...", "status-waiting"), unsafe_allow_html=True)
        devops_status.markdown(status_html("DevOps Engineer", "⚙️", "⏳ Waiting...", "status-waiting"), unsafe_allow_html=True)

        run = SwarmRun(idea.strip())

        # ── Step 1: Product Manager ────────────────────────────────────
        progress_bar.progress(10, text="Step 1/3: Product Manager is working...")
        pm_status.markdown(status_html("Product Manager", "📋", "🔄 Running...", "status-running"), unsafe_allow_html=True)

        pm_message = (
            f"You are the Product Manager. Here is the product idea:\n\n"
            f"{idea.strip()}\n\n"
            f"Call the 'define_requirements' tool now with complete details.\n"
            f"Extract the project name, description, features, user roles,\n"
            f"data entities, and acceptance criteria from the idea above."
        )

        pm_error = None
        t0 = time.time()
        try:
            pm_raw = agency.get_response_sync(
                message=pm_message,
                recipient_agent=product_manager,
            )
            pm_response = str(pm_raw.final_output)
            duration = time.time() - t0
            run.log_step("Product Manager", 1, pm_message, pm_response, duration)
            pm_status.markdown(status_html("Product Manager", "📋", f"✅ Complete ({duration:.1f}s)", "status-complete"), unsafe_allow_html=True)
        except Exception as e:
            duration = time.time() - t0
            pm_error = str(e)
            run.log_error(1, "Product Manager", pm_error)
            pm_status.markdown(status_html("Product Manager", "📋", f"❌ Error: {pm_error}", "status-error"), unsafe_allow_html=True)

        # ── Step 2: Systems Architect ──────────────────────────────────
        if not pm_error:
            progress_bar.progress(40, text="Step 2/3: Systems Architect is working...")
            arch_status.markdown(status_html("Systems Architect", "🏗️", "🔄 Running...", "status-running"), unsafe_allow_html=True)

            arch_message = (
                f"You are the Systems Architect. The Product Manager has defined the\n"
                f"requirements and stored them in shared context.\n\n"
                f"Read the requirements from context and call the 'design_architecture'\n"
                f"tool now with your complete architecture design.\n\n"
                f"Product idea for reference:\n{idea.strip()}"
            )

            arch_error = None
            t0 = time.time()
            try:
                arch_raw = agency.get_response_sync(
                    message=arch_message,
                    recipient_agent=systems_architect,
                )
                arch_response = str(arch_raw.final_output)
                duration = time.time() - t0
                run.log_step("Systems Architect", 2, arch_message, arch_response, duration)
                arch_status.markdown(status_html("Systems Architect", "🏗️", f"✅ Complete ({duration:.1f}s)", "status-complete"), unsafe_allow_html=True)
            except Exception as e:
                duration = time.time() - t0
                arch_error = str(e)
                run.log_error(2, "Systems Architect", arch_error)
                arch_status.markdown(status_html("Systems Architect", "🏗️", f"❌ Error: {arch_error}", "status-error"), unsafe_allow_html=True)
        else:
            arch_error = "Skipped — previous step failed"
            arch_status.markdown(status_html("Systems Architect", "🏗️", "⏭️ Skipped", "status-waiting"), unsafe_allow_html=True)

        # ── Step 3: DevOps Engineer ────────────────────────────────────
        if not pm_error and not arch_error:
            progress_bar.progress(70, text="Step 3/3: DevOps Engineer is working...")
            devops_status.markdown(status_html("DevOps Engineer", "⚙️", "🔄 Running...", "status-running"), unsafe_allow_html=True)

            devops_message = (
                f"You are the DevOps Engineer. The Systems Architect has designed the\n"
                f"architecture and stored it in shared context.\n\n"
                f"Read the architecture from context and call the 'plan_deployment'\n"
                f"tool now with your complete deployment plan.\n\n"
                f"Product idea for reference:\n{idea.strip()}"
            )

            devops_error = None
            t0 = time.time()
            try:
                devops_raw = agency.get_response_sync(
                    message=devops_message,
                    recipient_agent=devops_engineer,
                )
                devops_response = str(devops_raw.final_output)
                duration = time.time() - t0
                run.log_step("DevOps Engineer", 3, devops_message, devops_response, duration)
                devops_status.markdown(status_html("DevOps Engineer", "⚙️", f"✅ Complete ({duration:.1f}s)", "status-complete"), unsafe_allow_html=True)
            except Exception as e:
                duration = time.time() - t0
                devops_error = str(e)
                run.log_error(3, "DevOps Engineer", devops_error)
                devops_status.markdown(status_html("DevOps Engineer", "⚙️", f"❌ Error: {devops_error}", "status-error"), unsafe_allow_html=True)
        else:
            devops_error = "Skipped — previous step failed"
            devops_status.markdown(status_html("DevOps Engineer", "⚙️", "⏭️ Skipped", "status-waiting"), unsafe_allow_html=True)

        # ── Save logs ──────────────────────────────────────────────────
        progress_bar.progress(95, text="Saving logs...")
        transcript_path = run.save_transcript()
        context = extract_context(agency)
        context_path = None
        if context:
            context_path = run.save_context(context)

        progress_bar.progress(100, text="✅ Pipeline complete!")

        # ── Display results ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## 📄 Pipeline Results")

        with st.expander("📋 Product Manager — Requirements", expanded=bool(not pm_error)):
            if pm_error:
                st.error(pm_error)
            else:
                st.markdown(pm_response)

        with st.expander("🏗️ Systems Architect — Architecture Design", expanded=bool(not arch_error and not pm_error)):
            if arch_error:
                st.error(arch_error)
            else:
                st.markdown(arch_response)

        with st.expander("⚙️ DevOps Engineer — Deployment Plan", expanded=bool(not devops_error and not arch_error and not pm_error)):
            if devops_error:
                st.error(devops_error)
            else:
                st.markdown(devops_response)

        # ── Context snapshot ───────────────────────────────────────────
        if context:
            st.markdown("---")
            st.markdown("## 📦 Shared Context Snapshot")
            tab1, tab2, tab3 = st.tabs([
                "📋 Product Requirements",
                "🏗️ Architecture Design",
                "⚙️ Deployment Plan",
            ])
            with tab1:
                if "product_requirements" in context:
                    st.json(context["product_requirements"])
                else:
                    st.caption("Not available.")
            with tab2:
                if "architecture_design" in context:
                    st.json(context["architecture_design"])
                else:
                    st.caption("Not available.")
            with tab3:
                if "deployment_plan" in context:
                    st.json(context["deployment_plan"])
                else:
                    st.caption("Not available.")

        # ── Download section ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 💾 Download Logs")

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            with open(transcript_path) as f:
                st.download_button(
                    label="📄 Download Transcript (.txt)",
                    data=f.read(),
                    file_name=f"swarm_transcript_{run.run_id}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        with col_dl2:
            if context_path:
                with open(context_path) as f:
                    st.download_button(
                        label="📦 Download Context (.json)",
                        data=f.read(),
                        file_name=f"swarm_context_{run.run_id}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

        # ── Run summary ────────────────────────────────────────────────
        total_time = sum(s["duration_seconds"] for s in run.steps)
        st.markdown("---")
        st.markdown(
            f"**Pipeline complete** — {len(run.steps)} steps in {total_time:.1f}s. "
            f"{'⚠️ ' + str(len(run.errors)) + ' error(s)' if run.errors else '✅ No errors.'}"
        )

        # ── Store in history ──────────────────────────────────────────
        st.session_state.run_history.append({
            "project": idea.strip(),
            "steps": len(run.steps),
            "duration": total_time,
            "errors": len(run.errors),
            "transcript_path": transcript_path,
        })

else:
    if not st.session_state.api_key_set:
        results_placeholder.info("👈 Enter your OpenAI API key in the sidebar to begin.")
    elif not idea.strip():
        results_placeholder.info("📝 Describe a product idea above, then click **Run Swarm**.")
