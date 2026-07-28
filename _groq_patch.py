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
# We use a MetaPathFinder to intercept the import and patch the module.
import sys as _sys

if _sys.version_info[:2] == (3, 14):
    import importlib.abc as _abc
    import importlib.machinery as _mach
    import pathlib as _pl

    class _DCMFixer(_abc.MetaPathFinder):
        def find_spec(self, fullname, _path, _target=None):
            if fullname != "datamodel_code_generator.model":
                return None

            for _p in _sys.path:
                _init = _pl.Path(_p) / "datamodel_code_generator" / "model" / "__init__.py"
                if _init.exists():
                    _src = _init.read_text()

                    # Inject _missing_ into the PythonVersion class body
                    # Find "class PythonVersion(" and add _missing_ right before
                    # the next top-level statement
                    _cls_marker = "class PythonVersion("
                    _cls_idx = _src.find(_cls_marker)
                    if _cls_idx >= 0:
                        _after_header = _src.find("\n", _cls_idx) + 1
                        # Find next line that starts at column 0 (end of class body)
                        _rest = _src[_after_header:]
                        _next_top = -1
                        for _i, _ch in enumerate(_rest):
                            if _ch == "\n" and _i + 1 < len(_rest) and _rest[_i + 1] not in (" ", "\t", "\n", "#"):
                                _next_top = _after_header + _i + 1
                                break
                        if _next_top > 0:
                            _inject = (
                                "\n"
                                "    @classmethod\n"
                                '    def _missing_(cls, value):\n'
                                "        for member in cls:\n"
                                "            return member\n"
                                "        return None\n"
                                "\n"
                            )
                            _src = _src[:_next_top] + _inject + _src[_next_top:]

                    # Wrap the crashing DEFAULT_TARGET line in try/except
                    _old_line = 'DEFAULT_TARGET_PYTHON_VERSION = PythonVersion(f"{sys.version_info.major}.{sys.version_info.minor}")'
                    _new_block = (
                        "try:\n"
                        f"    {_old_line}\n"
                        'except ValueError:\n'
                        "    DEFAULT_TARGET_PYTHON_VERSION = '3.12'\n"
                    )
                    _src = _src.replace(_old_line, _new_block)

                    return _mach.ModuleSpec(
                        fullname,
                        _PatchedLoader(_init, _src),
                        is_package=True,
                    )
            return None

    class _PatchedLoader(_abc.Loader):
        def __init__(self, path, patched_source):
            self.path = path
            self.patched_source = patched_source

        def create_module(self, spec):
            return None  # Use default module creation

        def exec_module(self, module):
            exec(compile(self.patched_source, str(self.path), "exec"), module.__dict__)

    _sys.meta_path.insert(0, _DCMFixer())
