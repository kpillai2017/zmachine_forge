"""zbuilder - the agentic BUILD workflow that produces zforge.

See docs/DESIGN.md and the proforma in the parent folder. The workflow is a
deterministic orchestrator driving four LLM agents (Spec Analyst, Architect,
Implementer, Reviewer) plus a tool-driven Verifier.
"""
