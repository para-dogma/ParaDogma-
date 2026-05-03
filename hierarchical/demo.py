#!/usr/bin/env python3
"""
Demo: three agents collaborate to solve "write a sorting function".

Flow
----
1. Planner decomposes the task into subtasks.
2. Coder writes the code.
3. Reviewer checks the code.
4. The final result is stored in the Skill Library.

Run with:
    python -m hierarchical.demo
"""

from __future__ import annotations

import logging
import sys

from hierarchical.node import SkillLibrary, Task
from hierarchical.planner import Planner
from hierarchical.worker import Coder, Reviewer
from hierarchical.controller import Controller


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger(__name__)

    # -- shared Skill Library ----------------------------------------------
    skill_library = SkillLibrary()
    # Seed one existing skill so enrichment has something to find.
    skill_library.store("sorting", "Use Timsort for nearly-sorted data.")

    # -- create agents -----------------------------------------------------
    planner = Planner(name="Planner", skill_library=skill_library)
    coder = Coder(name="Coder", skill_library=skill_library)
    reviewer = Reviewer(name="Reviewer", skill_library=skill_library)

    agents = {"Coder": coder, "Reviewer": reviewer}

    # -- controller --------------------------------------------------------
    controller = Controller(planner=planner, agents=agents, skill_library=skill_library)

    # -- enqueue the top-level task ----------------------------------------
    task = Task(description="Write a sorting function")
    controller.enqueue(task)

    log.info("=" * 60)
    log.info("Starting hierarchical execution")
    log.info("=" * 60)

    results = controller.run()

    # -- print results -----------------------------------------------------
    log.info("=" * 60)
    log.info("Execution complete -- results:")
    log.info("=" * 60)

    for result in results:
        log.info("Task %s aggregated by %s:", result.task_id, result.agent_name)
        for line in result.content.splitlines():
            log.info("  %s", line)

    # -- show execution log ------------------------------------------------
    log.info("=" * 60)
    log.info("Execution log (%d entries):", len(controller.log))
    log.info("=" * 60)
    for entry in controller.log:
        log.info(
            "  [%s] %s -- %s: %s",
            entry.task_id,
            entry.agent_name,
            entry.action,
            entry.detail,
        )

    # -- show skill library ------------------------------------------------
    log.info("=" * 60)
    log.info("Skill Library (%d skills):", len(skill_library.skills))
    log.info("=" * 60)
    for name, data in skill_library.skills.items():
        preview = str(data)[:80]
        log.info("  %s: %s", name, preview)


if __name__ == "__main__":
    main()
