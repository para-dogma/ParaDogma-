"""
Specialised agent roles built on top of BaseAgent.

* **Planner** -- decomposes tasks, assigns subtasks, manages SkillLibrary.
* **Coder** -- writes code.
* **Reviewer** -- reviews code.
* **Tester** -- generates tests.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from agents.base import (
    BaseAgent,
    DogmaCompressor,
    DogmaNode,
    Result,
    SkillLibrary,
    Task,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

class Planner(BaseAgent):
    """High-level orchestrator that splits tasks and fans them out."""

    def __init__(
        self,
        name: str = "Planner",
        compressor: Optional[DogmaCompressor] = None,
        node: Optional[DogmaNode] = None,
        skill_library: Optional[SkillLibrary] = None,
    ) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)
        self._results: Dict[str, List[Result]] = {}

    def decompose(self, task: Task) -> List[Task]:
        """Break *task* into implementation / review / testing subtasks."""
        subtasks = [
            Task(
                description=f"Implement: {task.description}",
                metadata={"parent_task_id": task.task_id, "phase": "implementation"},
            ),
            Task(
                description=f"Review: {task.description}",
                metadata={"parent_task_id": task.task_id, "phase": "review"},
            ),
            Task(
                description=f"Test: {task.description}",
                metadata={"parent_task_id": task.task_id, "phase": "testing"},
            ),
        ]
        logger.info("[%s] Decomposed '%s' into %d subtask(s)", self.name, task.description, len(subtasks))
        return subtasks

    def assign(self, subtask: Task, agent: BaseAgent) -> Result:
        """Dispatch *subtask* to *agent* and record the result."""
        logger.info("[%s] Assigning '%s' -> %s", self.name, subtask.description, agent.name)
        result = agent.receive_task(subtask)
        parent_id = subtask.metadata.get("parent_task_id", subtask.task_id)
        self._results.setdefault(parent_id, []).append(result)
        agent.send_result(result, self)
        return result

    def aggregate(self, results: List[Result]) -> Result:
        """Merge sub-results into a single combined result."""
        combined = "\n---\n".join(f"[{r.agent_name}] {r.content}" for r in results)
        aggregated = Result(
            task_id=results[0].task_id if results else "unknown",
            agent_name=self.name,
            content=combined,
            metadata={"sub_results": len(results)},
        )
        logger.info("[%s] Aggregated %d result(s)", self.name, len(results))
        return aggregated

    def execute(self, task: Task) -> Result:
        return Result(
            task_id=task.task_id,
            agent_name=self.name,
            content=f"[{self.name}] planned: {task.description}",
        )

    @property
    def collected_results(self) -> Dict[str, List[Result]]:
        return dict(self._results)


# ---------------------------------------------------------------------------
# Coder
# ---------------------------------------------------------------------------

class Coder(BaseAgent):
    """Agent that produces source code."""

    def __init__(
        self,
        name: str = "Coder",
        compressor: Optional[DogmaCompressor] = None,
        node: Optional[DogmaNode] = None,
        skill_library: Optional[SkillLibrary] = None,
    ) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)

    def execute(self, task: Task) -> Result:
        logger.info("[%s] Writing code for: %s", self.name, task.description)
        context = [f"# Reusing skill: {s['skill']}" for s in task.enriched_skills]
        code = self._generate_code(task.description, context)
        return Result(task_id=task.task_id, agent_name=self.name, content=code, metadata={"language": "python"})

    @staticmethod
    def _generate_code(description: str, context: List[str]) -> str:
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

class Reviewer(BaseAgent):
    """Agent that reviews code and provides feedback."""

    def __init__(
        self,
        name: str = "Reviewer",
        compressor: Optional[DogmaCompressor] = None,
        node: Optional[DogmaNode] = None,
        skill_library: Optional[SkillLibrary] = None,
    ) -> None:
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
# Tester
# ---------------------------------------------------------------------------

class _Tester(BaseAgent):
    """Agent that generates tests.

    Named ``_Tester`` internally to avoid pytest's ``Test*`` collection
    heuristic.  Re-exported as ``Tester`` in the package ``__init__``.
    """

    def __init__(
        self,
        name: str = "Tester",
        compressor: Optional[DogmaCompressor] = None,
        node: Optional[DogmaNode] = None,
        skill_library: Optional[SkillLibrary] = None,
    ) -> None:
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


# Public alias
Tester = _Tester
