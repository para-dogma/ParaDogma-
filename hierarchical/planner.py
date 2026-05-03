"""
Planner agent -- decomposes complex tasks into subtasks and assigns them
to worker agents.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from hierarchical.node import (
    HierarchicalAgent,
    DogmaCompressor,
    DogmaNode,
    Result,
    SkillLibrary,
    Task,
)

logger = logging.getLogger(__name__)


class Planner(HierarchicalAgent):
    """High-level orchestrator that breaks tasks down and fans them out."""

    def __init__(
        self,
        name: str = "Planner",
        compressor: DogmaCompressor | None = None,
        node: DogmaNode | None = None,
        skill_library: SkillLibrary | None = None,
    ) -> None:
        super().__init__(name=name, compressor=compressor, node=node, skill_library=skill_library)
        self._results: Dict[str, List[Result]] = {}

    # -- planner-specific API ----------------------------------------------

    def decompose(self, task: Task) -> List[Task]:
        """Split *task* into a list of smaller subtasks.

        The default strategy produces three canonical phases:
        implementation, review and testing.  Subclasses (or future LLM
        integration) can override this with smarter decomposition.
        """
        description = task.description
        subtasks = [
            Task(
                description=f"Implement: {description}",
                metadata={"parent_task_id": task.task_id, "phase": "implementation"},
            ),
            Task(
                description=f"Review: {description}",
                metadata={"parent_task_id": task.task_id, "phase": "review"},
            ),
            Task(
                description=f"Test: {description}",
                metadata={"parent_task_id": task.task_id, "phase": "testing"},
            ),
        ]
        logger.info(
            "[%s] Decomposed '%s' into %d subtask(s)",
            self.name,
            description,
            len(subtasks),
        )
        return subtasks

    def assign(self, subtask: Task, agent: HierarchicalAgent) -> Result:
        """Send *subtask* to *agent* and collect the result."""
        logger.info("[%s] Assigning '%s' -> %s", self.name, subtask.description, agent.name)
        result = agent.receive_task(subtask)

        parent_id = subtask.metadata.get("parent_task_id", subtask.task_id)
        self._results.setdefault(parent_id, []).append(result)

        # Transport the result back to ourselves for auditing.
        agent.send_result(result, self)
        return result

    def aggregate(self, results: List[Result]) -> Result:
        """Merge a list of sub-results into one combined result."""
        combined_content = "\n---\n".join(
            f"[{r.agent_name}] {r.content}" for r in results
        )
        aggregated = Result(
            task_id=results[0].task_id if results else "unknown",
            agent_name=self.name,
            content=combined_content,
            metadata={"sub_results": len(results)},
        )
        logger.info("[%s] Aggregated %d result(s)", self.name, len(results))
        return aggregated

    # -- override base execute to run the full plan cycle ------------------

    def execute(self, task: Task) -> Result:
        """Default execution just returns a planning summary."""
        return Result(
            task_id=task.task_id,
            agent_name=self.name,
            content=f"[{self.name}] planned: {task.description}",
        )

    @property
    def collected_results(self) -> Dict[str, List[Result]]:
        return dict(self._results)
