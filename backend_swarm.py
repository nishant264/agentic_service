"""
Autonomous Backend Architecture Swarm
========================================
Phase 5: Execution & Logging

Three agents wired into a sequential pipeline through Agency Swarm.
Run output is captured to swarm_logs/ for debugging.
Each agent has a structured tool that:
  1. Defines its output via Pydantic fields (guarantees format)
  2. Validates that the previous agent's work exists (dependency chain)
  3. Stores its output into shared context for the next agent

Pipeline flow: Product Manager → Systems Architect → DevOps Engineer
"""

from typing import Literal

from agency_swarm import Agent, Agency, BaseTool, ModelSettings
from pydantic import Field


# =============================================================================
# TOOL 1: Product Manager — DefineRequirements
# =============================================================================
# The PM's "task" is a tool that forces structured output.
# Every field below is typed & validated by Pydantic — no free-form text.
# The Systems Architect will read this exact structure.

class DefineRequirements(BaseTool):
    """
    Define product requirements: features, user stories, roles, and entities.
    This is the first tool called in the pipeline — it has no dependency.
    """

    project_name: str = Field(
        ..., description="Name of the project being analyzed"
    )
    project_description: str = Field(
        ..., description="High-level description and goals of the project"
    )
    core_features: str = Field(
        ..., description="Comma-separated list of core features to build (Must Have)"
    )
    user_roles: str = Field(
        ..., description="Comma-separated list of user roles the system must support"
    )
    data_entities: str = Field(
        ..., description="Comma-separated list of key data entities that need to be modeled"
    )
    acceptance_criteria: str = Field(
        ..., description="High-level acceptance criteria for the project"
    )
    nice_to_have_features: str = Field(
        "", description="Comma-separated list of nice-to-have features (optional)"
    )

    class ToolConfig:
        name = "define_requirements"
        description = "Defines structured product requirements for the project"
        one_call_at_a_time = True

    def run(self) -> str:
        """Stores requirements into shared context for the Systems Architect."""
        # Guard: prevent running this twice
        if self.context.get("product_requirements", None) is not None:
            return (
                "Requirements are already defined. "
                "Proceed with the next step in the pipeline."
            )

        requirements = {
            "project_name": self.project_name.strip(),
            "project_description": self.project_description.strip(),
            "core_features": [
                f.strip() for f in self.core_features.split(",") if f.strip()
            ],
            "user_roles": [
                r.strip() for r in self.user_roles.split(",") if r.strip()
            ],
            "data_entities": [
                e.strip() for e in self.data_entities.split(",") if e.strip()
            ],
            "acceptance_criteria": self.acceptance_criteria.strip(),
            "nice_to_have": [
                f.strip() for f in self.nice_to_have_features.split(",") if f.strip()
            ],
        }

        self.context.set("product_requirements", requirements)

        return (
            f"Requirements defined for '{self.project_name}'. "
            f"Total core features: {len(requirements['core_features'])}. "
            "Handing off to the Systems Architect."
        )


# =============================================================================
# TOOL 2: Systems Architect — DesignArchitecture
# =============================================================================
# The Architect's task. It REQUIRES that the PM's output exists.
# This is the dependency validation — the chain.

class DesignArchitecture(BaseTool):
    """
    Design the system architecture based on the Product Manager's requirements.
    Depends on 'product_requirements' being set in shared context.
    """

    architecture_pattern: Literal[
        "monolithic", "microservices", "serverless", "hybrid"
    ] = Field(..., description="Architecture pattern for the system")

    services: str = Field(
        ...,
        description=(
            "Description of service boundaries and what each service does. "
            "Format: 'ServiceName: responsibility | ServiceName: responsibility'"
        ),
    )
    api_contracts: str = Field(
        ...,
        description=(
            "Key API endpoints. "
            "Format: 'POST /resource — description | GET /resource — description'"
        ),
    )
    data_model: str = Field(
        ...,
        description=(
            "Data model overview: main entities, their relationships, "
            "and storage strategy (SQL vs NoSQL, etc.)"
        ),
    )
    tech_stack: str = Field(
        ...,
        description=(
            "Comma-separated list of recommended technologies "
            "(languages, frameworks, databases, message queues, etc.)"
        ),
    )
    scalability_notes: str = Field(
        "", description="Key scalability considerations and constraints"
    )

    class ToolConfig:
        name = "design_architecture"
        description = "Designs the system architecture from product requirements"
        one_call_at_a_time = True

    def run(self) -> str:
        """Stores architecture design into shared context for the DevOps Engineer."""
        # Dependency check: PM must have run first
        requirements = self.context.get("product_requirements", None)
        if requirements is None:
            raise ValueError(
                "Cannot design architecture without product requirements. "
                "Please ensure the Product Manager has defined requirements first "
                "using the 'define_requirements' tool."
            )

        # Guard: prevent running this twice
        if self.context.get("architecture_design", None) is not None:
            return (
                "Architecture is already designed. "
                "Proceed with the next step in the pipeline."
            )

        design = {
            "project_name": requirements["project_name"],
            "architecture_pattern": self.architecture_pattern,
            "services": [
                s.strip() for s in self.services.split("|") if s.strip()
            ],
            "api_contracts": [
                a.strip() for a in self.api_contracts.split("|") if a.strip()
            ],
            "data_model": self.data_model.strip(),
            "tech_stack": [
                t.strip() for t in self.tech_stack.split(",") if t.strip()
            ],
            "scalability_notes": self.scalability_notes.strip(),
        }

        self.context.set("architecture_design", design)

        return (
            f"Architecture designed for '{requirements['project_name']}'. "
            f"Pattern: {self.architecture_pattern}. "
            f"Total services: {len(design['services'])}. "
            "Handing off to the DevOps Engineer."
        )


# =============================================================================
# TOOL 3: DevOps Engineer — PlanDeployment
# =============================================================================
# The DevOps Engineer's task. Depends on the Architect's output.
# This is the terminal node — it produces the final deliverable.

class PlanDeployment(BaseTool):
    """
    Plan the deployment infrastructure and CI/CD pipeline.
    Depends on 'architecture_design' being set in shared context.
    """

    ci_cd_tool: str = Field(
        ..., description="CI/CD tool to use (e.g., GitHub Actions, GitLab CI, Jenkins)"
    )
    cloud_provider: str = Field(
        ..., description="Primary cloud provider (e.g., AWS, GCP, Azure, self-hosted)"
    )
    containerization: str = Field(
        ..., description="Container strategy (e.g., Docker, no containers)"
    )
    orchestration: str = Field(
        ...,
        description=(
            "Orchestration tool (e.g., Kubernetes, Docker Compose, "
            "AWS ECS, or 'none')"
        ),
    )
    monitoring_stack: str = Field(
        ...,
        description=(
            "Monitoring, logging, and alerting tools "
            "(e.g., Prometheus, Grafana, Datadog)"
        ),
    )
    environments: str = Field(
        ...,
        description=(
            "Deployment environments to set up "
            "(e.g., 'dev, staging, production')"
        ),
    )
    additional_notes: str = Field(
        "",
        description=(
            "Any additional DevOps considerations "
            "(disaster recovery, secrets management, cost estimates)"
        ),
    )

    class ToolConfig:
        name = "plan_deployment"
        description = "Plans the CI/CD and infrastructure deployment"
        one_call_at_a_time = True

    def run(self) -> str:
        """Stores deployment plan into shared context as the final output."""
        # Dependency check: Architect must have run first
        architecture = self.context.get("architecture_design", None)
        if architecture is None:
            raise ValueError(
                "Cannot plan deployment without an architecture design. "
                "Please ensure the Systems Architect has designed the architecture first "
                "using the 'design_architecture' tool."
            )

        # Guard: prevent running this twice
        if self.context.get("deployment_plan", None) is not None:
            return (
                "Deployment plan is already defined. "
                "The pipeline is complete."
            )

        plan = {
            "project_name": architecture["project_name"],
            "ci_cd_tool": self.ci_cd_tool,
            "cloud_provider": self.cloud_provider,
            "containerization": self.containerization,
            "orchestration": self.orchestration,
            "monitoring_stack": self.monitoring_stack,
            "environments": [
                e.strip() for e in self.environments.split(",") if e.strip()
            ],
            "additional_notes": self.additional_notes.strip(),
        }

        self.context.set("deployment_plan", plan)

        return (
            f"Deployment plan created for '{architecture['project_name']}'. "
            f"Cloud: {self.cloud_provider} | CI/CD: {self.ci_cd_tool} | "
            f"Orchestration: {self.orchestration}. "
            "Pipeline complete."
        )


# =============================================================================
# AGENTS (with tools and structured instructions)
# =============================================================================

product_manager = Agent(
    name="Product Manager",
    description=(
        "Expert product manager who translates business needs into "
        "clear, actionable technical requirements."
    ),
    instructions="""
You are a Product Manager for a backend system. Your ONLY job is to
call the 'define_requirements' tool with a complete set of requirements.
Do NOT write free-form analysis — use the tool.

YOUR WORKFLOW:
1. Read the user's product idea carefully.
2. Call the 'define_requirements' tool with all required fields filled in.
3. After the tool confirms, summarize the key decisions briefly.

RULES:
- Be specific in your feature names and descriptions.
- Identify real user roles (e.g., 'admin', 'customer', 'moderator').
- Identify the main data entities the system must track.
- DO NOT discuss technology, architecture, or deployment.
""",
    tools=[DefineRequirements],
    model_settings=ModelSettings(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        max_tokens=8192,
    ),
)


systems_architect = Agent(
    name="Systems Architect",
    description=(
        "Senior systems architect who designs scalable, maintainable "
        "backend architectures from product requirements."
    ),
    instructions="""
You are a Systems Architect. Your ONLY job is to call the
'design_architecture' tool once the Product Manager has finished.
Do NOT write free-form analysis — use the tool.

YOUR WORKFLOW:
1. Read the Product Manager's requirements from context.
2. Call the 'design_architecture' tool with your full design.
3. After the tool confirms, summarize the architecture briefly.

RULES:
- Choose the architecture pattern that best fits the requirements.
- Define clear service boundaries — each service should own its data.
- List concrete API endpoints, not vague descriptions.
- Recommend real technologies that fit the project.
- DO NOT plan CI/CD, infrastructure, or deployment.
""",
    tools=[DesignArchitecture],
    model_settings=ModelSettings(
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=8192,
    ),
)


devops_engineer = Agent(
    name="DevOps Engineer",
    description=(
        "Experienced DevOps engineer who designs CI/CD pipelines, "
        "infrastructure, and monitoring for backend systems."
    ),
    instructions="""
You are a DevOps Engineer. Your ONLY job is to call the
'plan_deployment' tool once the Systems Architect has finished.
Do NOT write free-form analysis — use the tool.

YOUR WORKFLOW:
1. Read the Systems Architect's design from context.
2. Call the 'plan_deployment' tool with your infrastructure plan.
3. After the tool confirms, summarize the deployment strategy briefly.

RULES:
- Choose real tools (e.g., 'Docker', 'Kubernetes', 'GitHub Actions').
- Match the infrastructure to the architecture (microservices → K8s, etc.).
- Be practical about monitoring and observability.
- DO NOT redesign the architecture or change the API contracts.
- DO NOT redefine product features.
""",
    tools=[PlanDeployment],
    model_settings=ModelSettings(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=8192,
    ),
)


# =============================================================================
# AGENCY: The Orchestrator
# =============================================================================
# The Agency is the runtime that manages:
#   - Shared context between agents (agents read/write via self.context)
#   - Tool execution (when an agent says "call tool X", Agency runs it)
#   - Communication flows (who can send messages to whom)
#   - Message routing between agents
#
# communication_flows are directional tuples: (sender, recipient).
# PM → Architect → DevOps defines the pipeline handoff chain.

agency = Agency(
    product_manager,
    systems_architect,
    devops_engineer,
    communication_flows=[
        (product_manager, systems_architect),
        (systems_architect, devops_engineer),
    ],
)
