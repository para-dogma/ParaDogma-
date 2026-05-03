"""
Controller -- central dispatcher that manages the task queue, routes
packets between agents via DogmaNode and maintains an execution log.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional

from hierarchical.node import DogmaNode, HierarchicalAgent, Result, SkillLibrary, Task
from hierarchical.planner import Planner

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Single record in the controller execution log."""

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
    """Orchestrates tasks across a pool of specialised agents.

    * FIFO task queue.
    * Planner decomposes tasks; Controller routes subtasks to workers.
    * Aggregated results are persisted in the SkillLibrary.
    * Structured execution log.
    """

    # Map agent names (lowercase) to canonical phase names.
    _NAME_TO_PHASE = {
        "coder": "implementation",
        "reviewer": "review",
        "tester": "testing",
        "documenter": "documentation",
        "securityguard": "security",
        "devops": "devops",
    }

    def __init__(
        self,
        planner: Planner,
        agents: Dict[str, HierarchicalAgent],
        skill_library: Optional[SkillLibrary] = None,
    ) -> None:
        self.planner = planner
        self.agents = dict(agents)
        self.skill_library = skill_library or SkillLibrary()
        self._queue: Deque[Task] = deque()
        self._log: List[LogEntry] = []

    # -- queue management --------------------------------------------------

    def enqueue(self, task: Task) -> None:
        self._queue.append(task)
        self._record(task.task_id, "Controller", "enqueued", task.description)
        logger.info("[Controller] Enqueued: %s", task.description)

    # -- main loop ---------------------------------------------------------

    def run(self) -> List[Result]:
        all_results: List[Result] = []
        while self._queue:
            task = self._queue.popleft()
            self._record(task.task_id, "Controller", "processing", task.description)
            result = self._process(task)
            all_results.append(result)
            self.skill_library.store(task.description, result.content)
            self._record(task.task_id, "Controller", "stored_skill", task.description)
        return all_results

    # -- internals ---------------------------------------------------------

    def _process(self, task: Task) -> Result:
        subtasks = self.planner.decompose(task)
        self._record(task.task_id, self.planner.name, "decomposed", f"{len(subtasks)} subtask(s)")

        results: List[Result] = []
        phase_map = self._build_phase_map()

        for subtask in subtasks:
            phase = subtask.metadata.get("phase", "")
            agent = phase_map.get(phase, self.planner)
            result = self.planner.assign(subtask, agent)
            results.append(result)
            self._record(subtask.task_id, agent.name, "completed", subtask.description)

        aggregated = self.planner.aggregate(results)
        self._record(task.task_id, self.planner.name, "aggregated", f"{len(results)} result(s)")
        return aggregated

    def _build_phase_map(self) -> Dict[str, HierarchicalAgent]:
        mapping: Dict[str, HierarchicalAgent] = {}
        for name, agent in self.agents.items():
            phase = self._NAME_TO_PHASE.get(name.lower())
            if phase:
                mapping[phase] = agent
        return mapping

    def _record(self, task_id: str, agent_name: str, action: str, detail: str = "") -> None:
        self._log.append(LogEntry(task_id=task_id, agent_name=agent_name, action=action, detail=detail))

    @property
    def log(self) -> List[LogEntry]:
        return list(self._log)

    @property
    def pending_count(self) -> int:
        return len(self._queue)
