"""
Planner agent -- decomposes complex tasks into subtasks and assigns them
to the full roster of specialised worker agents.
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

# Canonical phases in execution order.
PHASES = [
    "implementation",
    "review",
    "testing",
    "documentation",
    "security",
    "devops",
]


class Planner(HierarchicalAgent):
    """High-level orchestrator that breaks tasks down and fans them out."""

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
        """Split *task* into one subtask per phase."""
        phase_labels = {
            "implementation": "Implement",
            "review": "Review",
            "testing": "Test",
            "documentation": "Document",
            "security": "Security-check",
            "devops": "Deploy",
        }
        subtasks = [
            Task(
                description=f"{phase_labels[phase]}: {task.description}",
                metadata={"parent_task_id": task.task_id, "phase": phase},
            )
            for phase in PHASES
        ]
        logger.info("[%s] Decomposed '%s' into %d subtask(s)", self.name, task.description, len(subtasks))
        return subtasks

    def assign(self, subtask: Task, agent: HierarchicalAgent) -> Result:
        """Dispatch *subtask* to *agent* and collect the result."""
        logger.info("[%s] Assigning '%s' -> %s", self.name, subtask.description, agent.name)
        result = agent.receive_task(subtask)
        parent_id = subtask.metadata.get("parent_task_id", subtask.task_id)
        self._results.setdefault(parent_id, []).append(result)
        agent.send_result(result, self)
        return result

    def aggregate(self, results: List[Result]) -> Result:
        """Merge sub-results into one combined result."""
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
