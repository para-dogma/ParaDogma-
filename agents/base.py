"""
BaseAgent -- foundation class for every agent in the DOGMA Agent Framework.

Integrates three core DOGMA components:

* **DogmaCompressor** -- semantic compression for compact inter-agent messages.
* **DogmaNode** -- transport layer that routes packets between agents.
* **SkillLibrary** -- shared store of reusable skills and past experiences.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DOGMA component stubs -- same public API as the real implementations so
# that downstream code works unchanged once the real modules are plugged in.
# ---------------------------------------------------------------------------

class DogmaCompressor:
    """Semantic compressor that shrinks text while preserving meaning."""

    def __init__(self, ratio: float = 0.5) -> None:
        self.ratio = ratio

    def compress(self, text: str) -> str:
        if not text:
            return text
        target_len = max(1, int(len(text) * self.ratio))
        compressed = text[:target_len]
        logger.debug("Compressed %d chars -> %d chars", len(text), len(compressed))
        return compressed


class DogmaNode:
    """Transport node for routing packets between agents."""

    def __init__(self, node_id: Optional[str] = None) -> None:
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self._inbox: List[Dict[str, Any]] = []

    def send(self, packet: Dict[str, Any], target: "DogmaNode") -> None:
        envelope = {
            "from": self.node_id,
            "to": target.node_id,
            "payload": packet,
        }
        target._inbox.append(envelope)
        logger.debug("DogmaNode %s -> %s", self.node_id, target.node_id)

    def receive(self) -> List[Dict[str, Any]]:
        messages = list(self._inbox)
        self._inbox.clear()
        return messages


class SkillLibrary:
    """Persistent store of reusable skills and experiences."""

    def __init__(self) -> None:
        self._skills: Dict[str, Any] = {}

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Bidirectional substring match: skill-name in query or query in skill-name."""
        results: List[Dict[str, Any]] = []
        q = query.lower()
        for key, value in self._skills.items():
            k = key.lower()
            if q in k or k in q:
                results.append({"skill": key, "data": value})
        return results

    def store(self, name: str, data: Any) -> None:
        self._skills[name] = data
        logger.debug("Skill stored: %s", name)

    @property
    def skills(self) -> Dict[str, Any]:
        return dict(self._skills)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A unit of work that flows through the agent pipeline."""

    description: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    enriched_skills: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "metadata": self.metadata,
            "enriched_skills": self.enriched_skills,
        }


@dataclass
class Result:
    """Output produced by an agent for a given task."""

    task_id: str
    agent_name: str
    content: str
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "content": self.content,
            "compressed": self.compressed,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# BaseAgent
# ---------------------------------------------------------------------------

class BaseAgent:
    """Foundation class for every DOGMA agent.

    Subclasses override ``execute(task)`` to provide role-specific behaviour.
    """

    def __init__(
        self,
        name: str,
        compressor: Optional[DogmaCompressor] = None,
        node: Optional[DogmaNode] = None,
        skill_library: Optional[SkillLibrary] = None,
    ) -> None:
        self.name = name
        self.compressor = compressor or DogmaCompressor()
        self.node = node or DogmaNode(node_id=name)
        self.skill_library = skill_library or SkillLibrary()
        self._task_log: List[Task] = []

    # -- public API --------------------------------------------------------

    def receive_task(self, task: Task) -> Result:
        """Accept a task, enrich it, execute and compress the result."""
        logger.info("[%s] Received task: %s", self.name, task.description)
        self._task_log.append(task)

        enriched = self.enrich_with_skills(task)
        result = self.execute(enriched)
        return self.compress_response(result)

    def enrich_with_skills(self, task: Task) -> Task:
        """Attach matching skills from the SkillLibrary to *task*."""
        hits = self.skill_library.search(task.description)
        if hits:
            task.enriched_skills = hits
            logger.info("[%s] Enriched with %d skill(s)", self.name, len(hits))
        return task

    def compress_response(self, result: Result) -> Result:
        """Compress the result content via DogmaCompressor."""
        if result.compressed:
            return result
        result.content = self.compressor.compress(result.content)
        result.compressed = True
        return result

    def send_result(self, result: Result, target: "BaseAgent") -> None:
        """Ship *result* to *target* agent through DogmaNode transport."""
        self.node.send(result.to_dict(), target.node)
        logger.info("[%s] Sent result to %s", self.name, target.name)

    # -- hook for subclasses -----------------------------------------------

    def execute(self, task: Task) -> Result:
        """Override in subclasses to provide role-specific logic."""
        return Result(
            task_id=task.task_id,
            agent_name=self.name,
            content=f"[{self.name}] executed: {task.description}",
        )

    @property
    def task_log(self) -> List[Task]:
        return list(self._task_log)
