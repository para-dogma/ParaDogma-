#!/usr/bin/env python3
"""
Demo: Planner, Coder and Reviewer collaborate on "write a sorting function".

Flow
----
1. Planner decomposes the task into subtasks.
2. Coder writes code.
3. Reviewer reviews it.
4. Final result is stored in the Skill Library.

Run with::

    python -m agents.demo
"""

from __future__ import annotations

import logging
import sys

from agents.base import SkillLibrary, Task
from agents.roles import Planner, Coder, Reviewer
from agents.controller import Controller


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger(__name__)

    # Shared skill library with one seed skill.
    skill_library = SkillLibrary()
    skill_library.store("sorting", "Use Timsort for nearly-sorted data.")

    # Create agents.
    planner = Planner(name="Planner", skill_library=skill_library)
    coder = Coder(name="Coder", skill_library=skill_library)
    reviewer = Reviewer(name="Reviewer", skill_library=skill_library)

    # Controller wires everything together.
    controller = Controller(
        planner=planner,
        agents={"Coder": coder, "Reviewer": reviewer},
        skill_library=skill_library,
    )

    task = Task(description="Write a sorting function")
    controller.enqueue(task)

    log.info("=" * 60)
    log.info("DOGMA Agent Framework -- demo start")
    log.info("=" * 60)

    results = controller.run()

    log.info("=" * 60)
    log.info("Results:")
    log.info("=" * 60)
    for r in results:
        log.info("Task %s aggregated by %s:", r.task_id, r.agent_name)
        for line in r.content.splitlines():
            log.info("  %s", line)

    log.info("=" * 60)
    log.info("Execution log (%d entries):", len(controller.log))
    log.info("=" * 60)
    for entry in controller.log:
        log.info("  [%s] %s -- %s: %s", entry.task_id, entry.agent_name, entry.action, entry.detail)

    log.info("=" * 60)
    log.info("Skill Library (%d skills):", len(skill_library.skills))
    log.info("=" * 60)
    for name, data in skill_library.skills.items():
        log.info("  %s: %s", name, str(data)[:80])


if __name__ == "__main__":
    main()
