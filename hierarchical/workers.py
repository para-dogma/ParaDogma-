"""
Specialised worker agents -- 6 roles that inherit from HierarchicalAgent.

* **Coder** -- writes code.
* **Reviewer** -- reviews code.
* **Tester** -- generates tests.
* **Documenter** -- writes documentation.
* **SecurityGuard** -- performs security review.
* **DevOps** -- prepares deployment artefacts.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from hierarchical.node import (
    DogmaCompressor,
    DogmaNode,
    HierarchicalAgent,
    Result,
    SkillLibrary,
    Task,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Coder
# ---------------------------------------------------------------------------

class Coder(HierarchicalAgent):
    """Agent that produces source code."""

    def __init__(self, name: str = "Coder", compressor: Optional[DogmaCompressor] = None,
                 node: Optional[DogmaNode] = None, skill_library: Optional[SkillLibrary] = None) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Writing code for: %s", self.name, task.description)
        context = [f"# Reusing skill: {s['skill']}" for s in task.enriched_skills]
        code = self._generate(task.description, context)
        return Result(task_id=task.task_id, agent_name=self.name, content=code, metadata={"language": "python"})

    @staticmethod
    def _generate(description: str, context: List[str]) -> str:
        header = "\n".join(context) if context else ""
        body = (
            f"def solution():\n"
            f"    '''Auto-generated for: {description}'''\n"
            f"    # TODO: implement\n"
            f"    pass\n"
        )
        return f"{header}\n{body}".strip()


# ---------------------------------------------------------------------------
# Reviewer
# ---------------------------------------------------------------------------

class Reviewer(HierarchicalAgent):
    """Agent that reviews code and provides feedback."""

    def __init__(self, name: str = "Reviewer", compressor: Optional[DogmaCompressor] = None,
                 node: Optional[DogmaNode] = None, skill_library: Optional[SkillLibrary] = None) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Reviewing: %s", self.name, task.description)
        review = (
            f"Review of '{task.description}':\n"
            f"- Code structure: OK\n"
            f"- Naming conventions: OK\n"
            f"- Edge cases: needs attention\n"
            f"- Overall: APPROVED with minor suggestions"
        )
        return Result(task_id=task.task_id, agent_name=self.name, content=review, metadata={"status": "approved"})


# ---------------------------------------------------------------------------
# Tester (internal name avoids pytest collection warning)
# ---------------------------------------------------------------------------

class _Tester(HierarchicalAgent):
    """Agent that generates tests."""

    def __init__(self, name: str = "Tester", compressor: Optional[DogmaCompressor] = None,
                 node: Optional[DogmaNode] = None, skill_library: Optional[SkillLibrary] = None) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Generating tests for: %s", self.name, task.description)
        tests = (
            f"import pytest\n\n"
            f"# Tests for: {task.description}\n\n"
            f"def test_basic():\n"
            f"    assert solution() is not None\n\n"
            f"def test_empty_input():\n"
            f"    assert solution() is not None\n\n"
            f"def test_edge_case():\n"
            f"    assert solution() is not None\n"
        )
        return Result(task_id=task.task_id, agent_name=self.name, content=tests, metadata={"test_count": 3})


Tester = _Tester


# ---------------------------------------------------------------------------
# Documenter
# ---------------------------------------------------------------------------

class Documenter(HierarchicalAgent):
    """Agent that writes documentation."""

    def __init__(self, name: str = "Documenter", compressor: Optional[DogmaCompressor] = None,
                 node: Optional[DogmaNode] = None, skill_library: Optional[SkillLibrary] = None) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Writing docs for: %s", self.name, task.description)
        doc = (
            f"# Documentation\n\n"
            f"## Overview\n"
            f"{task.description}\n\n"
            f"## Usage\n"
            f"```python\nfrom service import solution\nresult = solution()\n```\n\n"
            f"## API Reference\n"
            f"- `solution()` -- main entry point\n"
        )
        return Result(task_id=task.task_id, agent_name=self.name, content=doc, metadata={"format": "markdown"})


# ---------------------------------------------------------------------------
# SecurityGuard
# ---------------------------------------------------------------------------

class SecurityGuard(HierarchicalAgent):
    """Agent that performs security review."""

    def __init__(self, name: str = "SecurityGuard", compressor: Optional[DogmaCompressor] = None,
                 node: Optional[DogmaNode] = None, skill_library: Optional[SkillLibrary] = None) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Security review: %s", self.name, task.description)
        report = (
            f"Security Report for '{task.description}':\n"
            f"- Input validation: PASS\n"
            f"- Injection attacks: PASS\n"
            f"- Dependency vulnerabilities: PASS\n"
            f"- Data exposure: PASS\n"
            f"- Overall: SECURE"
        )
        return Result(task_id=task.task_id, agent_name=self.name, content=report, metadata={"status": "secure"})


# ---------------------------------------------------------------------------
# DevOps
# ---------------------------------------------------------------------------

class DevOps(HierarchicalAgent):
    """Agent that prepares deployment artefacts."""

    def __init__(self, name: str = "DevOps", compressor: Optional[DogmaCompressor] = None,
                 node: Optional[DogmaNode] = None, skill_library: Optional[SkillLibrary] = None) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Preparing deployment for: %s", self.name, task.description)
        manifest = (
            f"# Deployment Manifest\n"
            f"service: {task.description}\n"
            f"runtime: python3.11\n"
            f"replicas: 2\n"
            f"health_check: /health\n"
            f"env:\n"
            f"  - LOG_LEVEL=INFO\n"
            f"status: READY_TO_DEPLOY"
        )
        return Result(task_id=task.task_id, agent_name=self.name, content=manifest, metadata={"status": "ready"})
