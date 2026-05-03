"""
Controller -- central dispatcher that manages the task queue, routes
packets between agents via DogmaNode and keeps an execution log.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from hierarchical.node import (
    DogmaNode,
    HierarchicalAgent,
    Result,
    SkillLibrary,
    Task,
)
from hierarchical.planner import Planner

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Single record in the controller's execution log."""

    task_id: str
    agent_name: str
    action: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "detail": self.detail,
        }


class Controller:
    """Orchestrates the full lifecycle of tasks across a pool of agents.

    Responsibilities
    ----------------
    * Maintain a FIFO task queue.
    * Use the ``Planner`` to decompose incoming tasks.
    * Route subtasks to the right worker agent.
    * Collect and aggregate results.
    * Persist completed skills back to the ``SkillLibrary``.
    * Keep a structured execution log.
    """

    def __init__(
        self,
        planner: Planner,
        agents: Dict[str, HierarchicalAgent],
        skill_library: SkillLibrary | None = None,
    ) -> None:
        self.planner = planner
        self.agents = dict(agents)
        self.skill_library = skill_library or SkillLibrary()
        self._queue: Deque[Task] = deque()
        self._log: List[LogEntry] = []

    # -- queue management --------------------------------------------------

    def enqueue(self, task: Task) -> None:
        """Add *task* to the back of the queue."""
        self._queue.append(task)
        self._record(task.task_id, "Controller", "enqueued", task.description)
        logger.info("[Controller] Enqueued task: %s", task.description)

    # -- main processing loop ----------------------------------------------

    def run(self) -> List[Result]:
        """Process every task in the queue and return aggregated results."""
        all_results: List[Result] = []

        while self._queue:
            task = self._queue.popleft()
            self._record(task.task_id, "Controller", "processing", task.description)

            result = self._process_task(task)
            all_results.append(result)

            # Persist the final aggregated result as a new skill.
            self.skill_library.store(task.description, result.content)
            self._record(task.task_id, "Controller", "stored_skill", task.description)

        return all_results

    # -- internal helpers --------------------------------------------------

    def _process_task(self, task: Task) -> Result:
        """Decompose *task*, dispatch subtasks, aggregate results."""
        subtasks = self.planner.decompose(task)
        self._record(task.task_id, self.planner.name, "decomposed", f"{len(subtasks)} subtask(s)")

        results: List[Result] = []
        phase_agent_map = self._build_phase_map()

        for subtask in subtasks:
            phase = subtask.metadata.get("phase", "")
            agent = phase_agent_map.get(phase)
            if agent is None:
                # Fall back to the planner itself.
                agent = self.planner

            result = self.planner.assign(subtask, agent)
            results.append(result)
            self._record(subtask.task_id, agent.name, "completed", subtask.description)

        aggregated = self.planner.aggregate(results)
        self._record(task.task_id, self.planner.name, "aggregated", f"{len(results)} result(s)")
        return aggregated

    def _build_phase_map(self) -> Dict[str, HierarchicalAgent]:
        """Map canonical phase names to registered agents."""
        mapping: Dict[str, HierarchicalAgent] = {}
        name_phase = {
            "coder": "implementation",
            "reviewer": "review",
            "tester": "testing",
        }
        for agent_name, agent in self.agents.items():
            phase = name_phase.get(agent_name.lower())
            if phase:
                mapping[phase] = agent
        return mapping

    def _record(self, task_id: str, agent_name: str, action: str, detail: str = "") -> None:
        entry = LogEntry(task_id=task_id, agent_name=agent_name, action=action, detail=detail)
        self._log.append(entry)

    # -- accessors ---------------------------------------------------------

    @property
    def log(self) -> List[LogEntry]:
        return list(self._log)

    @property
    def pending_count(self) -> int:
        return len(self._queue)
