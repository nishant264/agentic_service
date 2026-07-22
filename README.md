# 🤖 Autonomous Backend Architecture Swarm

A **multi-agent AI system** that takes a product idea and autonomously produces a complete backend plan — from feature requirements through system architecture to deployment infrastructure — using three coordinated AI agents.

Built with [Agency Swarm](https://github.com/airi-oss/agency-swarm), this project demonstrates **structured multi-agent orchestration** with dependency-gated task handoffs, shared context state, and full conversation logging.

---

## 🏗️ Architecture

```
                   ┌──────────────┐
                   │  Product Idea │
                   └──────┬───────┘
                          │
          ┌───────────────▼────────────────┐
          │   Product Manager              │
          │   Tool: DefineRequirements     │
          │   Stores → product_requirements│
          └───────────────┬────────────────┘
                          │  Dependency: PM must complete
          ┌───────────────▼────────────────┐
          │   Systems Architect            │
          │   Tool: DesignArchitecture     │
          │   Stores → architecture_design │
          └───────────────┬────────────────┘
                          │  Dependency: Architect must complete
          ┌───────────────▼────────────────┐
          │   DevOps Engineer              │
          │   Tool: PlanDeployment         │
          │   Stores → deployment_plan     │
          └───────────────┬────────────────┘
                          │
          ┌───────────────▼────────────────┐
          │   ✅ Final Deliverable         │
          │   Full spec + architecture +   │
          │   deployment plan              │
          └────────────────────────────────┘
```

### The Three Agents

| Agent | Role | Owns | Temperature |
|---|---|---|---|
| **Product Manager** | Defines *what* to build | Features, user stories, acceptance criteria | 0.4 |
| **Systems Architect** | Designs *how* to build it | Service boundaries, API contracts, data models | 0.5 |
| **DevOps Engineer** | Plans *how* to ship & run it | CI/CD, infrastructure, monitoring | 0.3 |

### Key Design Principle

Each agent has **three layers** in its prompt:
1. **Persona** — who it is (sets expertise)
2. **Responsibilities** — what it owns (defines scope)
3. **Constraints** — what it's **NOT** allowed to do (prevents stepping on other agents)

The constraints are what make multi-agent systems work — they're guardrails that keep each agent in its lane.

---

## 📁 Project Files

| File | Purpose |
|---|---|
| `backend_swarm.py` | Agent definitions, Pydantic-validated tools, and Agency orchestration |
| `run_swarm.py` | CLI entry point — runs the pipeline with real-time output |
| `swarm_logger.py` | Conversation logger — saves full transcripts and context snapshots |
| `agency.py` | Original 5-agent Streamlit app (legacy) |
| `requirements.txt` | Python dependencies |
| `swarm_logs/` | Run artifacts (auto-generated) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
export OPENAI_API_KEY='sk-...'

# 3. Run the swarm
python run_swarm.py
```

Then paste a product idea when prompted (e.g., *"Build a task management SaaS with Kanban boards and automated reporting"*). Press **Ctrl+D** (macOS/Linux) or **Ctrl+Z** (Windows) when done.

The agents will run in sequence and print their outputs in real time.

---

## 📊 Logging & Debugging

Every run saves two files to `swarm_logs/`:

```
swarm_logs/
├── 20260722_153042_transcript.txt    # Full conversation log
└── 20260722_153042_context.json       # Final structured data
```

### Transcript Example

```
======================================================================
  AUTONOMOUS BACKEND ARCHITECTURE SWARM
  Run ID : 20260722_153042
======================================================================

PRODUCT IDEA:
Build a task management SaaS platform...

----------------------------------------------------------------------
STEP 1: Product Manager (12.4s)
----------------------------------------------------------------------
PROMPT SENT:
You are the Product Manager...

AGENT RESPONSE:
Requirements defined for 'TaskManager Pro'...
```

### Context Snapshot Example (`context.json`)

```json
{
  "product_requirements": {
    "project_name": "TaskManager Pro",
    "core_features": ["Kanban board", "Task assignment", "Reporting"],
    "user_roles": ["admin", "team_member", "viewer"],
    ...
  },
  "architecture_design": {
    "architecture_pattern": "microservices",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
    ...
  },
  "deployment_plan": {
    "ci_cd_tool": "GitHub Actions",
    "cloud_provider": "AWS",
    ...
  }
}
```

---

## 🧠 What This Demonstrates

| Skill | How This Project Proves It |
|---|---|
| **Multi-Agent Orchestration** | Three agents with coordinated pipeline execution via Agency Swarm |
| **Structured Task Handoffs** | Each agent's output is Pydantic-validated and stored in shared context with dependency checks |
| **State Management** | Tools read/write to shared context with idempotency guards |
| **Prompt Engineering** | Each agent has a persona + responsibilities + constraints (not one giant prompt) |
| **Error Handling** | Dependency validation raises clear errors; partial transcript saves on failure |
| **Observability** | Full conversation logging with timing, transcripts, and context snapshots |

---

## 📚 The 5 Phases (How This Was Built)

This project was built following a structured curriculum:

1. **Prerequisites & File Tour** — Understanding agent roles, task delegation, and frameworks
2. **Defining the Agents** — Writing system prompts with personas and constraints
3. **Defining the Tasks** — Creating Pydantic-validated tools with dependency gates
4. **The Orchestration Pipeline** — Wiring agents into an Agency with communication flows
5. **Execution & Logging** — Running the pipeline and capturing conversation transcripts

---

## 🔧 Requirements

```
python-dotenv==1.1.1
agency-swarm==1.7.0
streamlit
```

---

## 📄 License

This project is for learning and demonstration purposes.
