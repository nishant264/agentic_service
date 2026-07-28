"""
Groq API Compatibility Patch
=============================
Applied at import time by entry points (run_swarm.py, swarm_ui.py).

Fixes issues when using agency-swarm with Groq's API backend:

  1. InputTokensDetails version mismatch:
     openai-agents >= 0.6 requires a 'cache_write_tokens' field on
     InputTokensDetails, but agency-swarm==1.7.0 creates instances
     with only 'cached_tokens=0'.  We patch the dataclass to make
     the new field optional with a default of 0.

  2. OPENAI_BASE_URL is set to Groq's endpoint so that all OpenAI-
     compatible clients know where to route requests.

  3. Telemetry is disabled to prevent [non-fatal] tracing errors
     when an OpenAI-compatible base URL (Groq) is used.

Usage:
    # Must be the FIRST import in your entry point
    import _groq_patch

    # Then import the rest of the project
    from backend_swarm import agency
"""

import os

# ── Step 1: Set the API base URL to Groq ───────────────────────────────
# This must happen before any OpenAI client is created.
# The agents library and agency-swarm both read this environment variable.
os.environ.setdefault(
    "OPENAI_BASE_URL",
    "https://api.groq.com/openai/v1",
)

# ── Step 0: Disable OpenAI telemetry ────────────────────────────────────
# The Agents SDK sends traces to api.openai.com even when using a
# non-OpenAI base URL.  This causes noisy [non-fatal] 401 errors.
os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")

# ── Step 2: Fix InputTokensDetails compatibility ───────────────────────
# agency-swarm==1.7.0 uses openai-agents which has an InputTokensDetails
# dataclass. The library calls InputTokensDetails(cached_tokens=0) but
# newer versions of openai-agents require a 'cache_write_tokens' field.
#
# We monkey-patch __init__ to supply the default when it's missing.
try:
    from agents.usage import InputTokensDetails

    _original_init = InputTokensDetails.__init__

    def _patched_init(self, **data):
        if "cache_write_tokens" not in data:
            data["cache_write_tokens"] = 0
        _original_init(self, **data)

    InputTokensDetails.__init__ = _patched_init
except ImportError:
    pass  # agents library not installed
except Exception:
    pass  # Graceful fallback for any other incompatibility

# ── Step 3: Fix datamodel-code-generator for Python 3.14 ────────────────
# Python 3.14 isn't in datamodel_code_generator's PythonVersion enum yet.
# We scan sys.path for the module file and pre-load a patched version.
import sys as _sys

if _sys.version_info[:2] == (3, 14):
    _found = False
    try:
        import pathlib as _pathlib
        import types as _types

        for _p in _sys.path:
            _model_init = (
                _pathlib.Path(_p)
                / "datamodel_code_generator"
                / "model"
                / "__init__.py"
            )
            if _model_init.exists():
                _src = _model_init.read_text()
                # Add a _missing_ hook so PythonVersion("3.14") succeeds
                _src += """
try:
    PythonVersion("3.14")
except ValueError:
    if not hasattr(PythonVersion, "_missing_"):
        @classmethod
        def _missing_(cls, value):
            for member in cls:
                return member
            return None
        PythonVersion._missing_ = _missing_
        PythonVersion._value2member_map_["3.14"] = PythonVersion("3.12")
        PythonVersion._member_names_.append("3_14")
"""

                _mod = _types.ModuleType("datamodel_code_generator.model")
                _mod.__file__ = str(_model_init)
                _mod.__package__ = "datamodel_code_generator"
                _mod.__path__ = [str(_model_init.parent)]
                exec(compile(_src, str(_model_init), "exec"), _mod.__dict__)
                _sys.modules["datamodel_code_generator.model"] = _mod
                _found = True
                break
    except Exception:
        pass  # Fallback — error may surface later
