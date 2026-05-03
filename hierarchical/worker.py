"""
Worker agents -- specialised executors that inherit from HierarchicalAgent.

* **Coder** -- writes code for a given task description.
* **Reviewer** -- reviews code and provides feedback.
* **Tester** -- generates tests for the supplied code.
"""

from __future__ import annotations

import logging

from hierarchical.node import (
    DogmaCompressor,
    DogmaNode,
    HierarchicalAgent,
    Result,
    SkillLibrary,
    Task,
)

logger = logging.getLogger(__name__)


class Coder(HierarchicalAgent):
    """Agent that produces source code for a given task."""

    def __init__(
        self,
        name: str = "Coder",
        compressor: DogmaCompressor | None = None,
        node: DogmaNode | None = None,
        skill_library: SkillLibrary | None = None,
    ) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        """Simulate code generation based on *task.description*."""
        logger.info("[%s] Writing code for: %s", self.name, task.description)

        # Use enriched skills as context if available.
        context_lines = []
        for skill in task.enriched_skills:
            context_lines.append(f"# Reusing skill: {skill['skill']}")

        code = self._generate_code(task.description, context_lines)

        return Result(
            task_id=task.task_id,
            agent_name=self.name,
            content=code,
            metadata={"language": "python"},
        )

    @staticmethod
    def _generate_code(description: str, context: list[str]) -> str:
        """Produce a simple code snippet.  In production this would call an
        LLM; here we return a deterministic stub so the demo is reproducible."""
        header = "\n".join(context) if context else ""
        body = (
            f"def solution():\n"
            f"    '''Auto-generated for: {description}'''\n"
            f"    # TODO: implement\n"
            f"    pass\n"
        )
        return f"{header}\n{body}".strip()


class Reviewer(HierarchicalAgent):
    """Agent that reviews code produced by a Coder."""

    def __init__(
        self,
        name: str = "Reviewer",
        compressor: DogmaCompressor | None = None,
        node: DogmaNode | None = None,
        skill_library: SkillLibrary | None = None,
    ) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Reviewing: %s", self.name, task.description)

        review = self._review(task.description)
        return Result(
            task_id=task.task_id,
            agent_name=self.name,
            content=review,
            metadata={"status": "approved"},
        )

    @staticmethod
    def _review(description: str) -> str:
        return (
            f"Review of '{description}':\n"
            f"- Code structure: OK\n"
            f"- Naming conventions: OK\n"
            f"- Edge cases: needs attention\n"
            f"- Overall: APPROVED with minor suggestions"
        )


class Tester(HierarchicalAgent):
    """Agent that generates tests for code."""

    def __init__(
        self,
        name: str = "Tester",
        compressor: DogmaCompressor | None = None,
        node: DogmaNode | None = None,
        skill_library: SkillLibrary | None = None,
    ) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Generating tests for: %s", self.name, task.description)

        tests = self._generate_tests(task.description)
        return Result(
            task_id=task.task_id,
            agent_name=self.name,
            content=tests,
            metadata={"test_count": 3},
        )

    @staticmethod
    def _generate_tests(description: str) -> str:
        return (
            f"import pytest\n\n"
            f"# Tests for: {description}\n\n"
            f"def test_basic():\n"
            f"    assert solution() is not None\n\n"
            f"def test_empty_input():\n"
            f"    assert solution() is not None\n\n"
            f"def test_edge_case():\n"
            f"    assert solution() is not None\n"
        )
