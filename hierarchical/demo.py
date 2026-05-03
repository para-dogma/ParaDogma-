#!/usr/bin/env python3
"""
Demo: 7 agents collaborate on "create a microservice for text compression".

Pipeline: Planner -> Coder -> Reviewer -> Tester -> Documenter -> SecurityGuard -> DevOps

Run with::

    python -m hierarchical.demo
"""

from __future__ import annotations

import logging
import sys

from hierarchical.node import SkillLibrary, Task
from hierarchical.planner import Planner
from hierarchical.workers import Coder, Reviewer, Tester, Documenter, SecurityGuard, DevOps
from hierarchical.controller import Controller


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger(__name__)

    # Shared skill library with seed skills.
    skill_library = SkillLibrary()
    skill_library.store("compression", "Use zlib for fast compression with reasonable ratios.")
    skill_library.store("microservice", "Keep endpoints stateless; use health checks.")

    # Create all agents.
    planner = Planner(name="Planner", skill_library=skill_library)
    coder = Coder(name="Coder", skill_library=skill_library)
    reviewer = Reviewer(name="Reviewer", skill_library=skill_library)
    tester = Tester(name="Tester", skill_library=skill_library)
    documenter = Documenter(name="Documenter", skill_library=skill_library)
    security = SecurityGuard(name="SecurityGuard", skill_library=skill_library)
    devops = DevOps(name="DevOps", skill_library=skill_library)

    agents = {
        "Coder": coder,
        "Reviewer": reviewer,
        "Tester": tester,
        "Documenter": documenter,
        "SecurityGuard": security,
        "DevOps": devops,
    }

    controller = Controller(planner=planner, agents=agents, skill_library=skill_library)

    task = Task(description="Create a microservice for text compression")
    controller.enqueue(task)

    log.info("=" * 70)
    log.info("Hierarchical AI -- 7-agent ecosystem demo")
    log.info("=" * 70)

    results = controller.run()

    # -- results -----------------------------------------------------------
    log.info("=" * 70)
    log.info("Aggregated results:")
    log.info("=" * 70)
    for r in results:
        log.info("Task %s aggregated by %s:", r.task_id, r.agent_name)
        for line in r.content.splitlines():
            log.info("  %s", line)

    # -- execution log -----------------------------------------------------
    log.info("=" * 70)
    log.info("Execution log (%d entries):", len(controller.log))
    log.info("=" * 70)
    for entry in controller.log:
        log.info("  [%s] %s -- %s: %s", entry.task_id, entry.agent_name, entry.action, entry.detail)

    # -- skill library -----------------------------------------------------
    log.info("=" * 70)
    log.info("Skill Library (%d skills):", len(skill_library.skills))
    log.info("=" * 70)
    for name, data in skill_library.skills.items():
        log.info("  %s: %s", name, str(data)[:80])


if __name__ == "__main__":
    main()
