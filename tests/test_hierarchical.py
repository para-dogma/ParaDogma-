"""
Tests for the Hierarchical AI -- 7-role agent ecosystem.

12 tests covering: agent initialisation, skill enrichment, compression,
transport, decomposition, assignment/aggregation, all 6 workers and the
full controller lifecycle.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hierarchical.node import (
    DogmaCompressor,
    DogmaNode,
    HierarchicalAgent,
    Result,
    SkillLibrary,
    Task,
)
from hierarchical.planner import Planner
from hierarchical.workers import Coder, Reviewer, Tester, Documenter, SecurityGuard, DevOps
from hierarchical.controller import Controller


# ---- 1. Agent initialisation --------------------------------------------

def test_agent_init():
    agent = HierarchicalAgent(name="Agent")
    assert agent.name == "Agent"
    assert isinstance(agent.compressor, DogmaCompressor)
    assert isinstance(agent.node, DogmaNode)
    assert isinstance(agent.skill_library, SkillLibrary)
    assert agent.task_log == []


# ---- 2. Skill enrichment ------------------------------------------------

def test_enrich_with_matching_skill():
    lib = SkillLibrary()
    lib.store("compression", "Use zlib")
    agent = HierarchicalAgent(name="A", skill_library=lib)
    task = Task(description="Build a compression service")
    enriched = agent.enrich_with_skills(task)
    assert len(enriched.enriched_skills) == 1
    assert enriched.enriched_skills[0]["skill"] == "compression"


def test_enrich_no_match():
    lib = SkillLibrary()
    lib.store("database", "Use connection pooling")
    agent = HierarchicalAgent(name="A", skill_library=lib)
    task = Task(description="Build a compression service")
    enriched = agent.enrich_with_skills(task)
    assert enriched.enriched_skills == []


# ---- 3. Response compression --------------------------------------------

def test_compress_response():
    agent = HierarchicalAgent(name="A", compressor=DogmaCompressor(ratio=0.5))
    result = Result(task_id="t1", agent_name="A", content="X" * 100)
    compressed = agent.compress_response(result)
    assert compressed.compressed is True
    assert len(compressed.content) == 50


# ---- 4. Transport -------------------------------------------------------

def test_send_result_transport():
    sender = HierarchicalAgent(name="S")
    receiver = HierarchicalAgent(name="R")
    result = Result(task_id="t1", agent_name="S", content="payload")
    sender.send_result(result, receiver)
    messages = receiver.node.receive()
    assert len(messages) == 1
    assert messages[0]["from"] == "S"


# ---- 5. Planner decompose -----------------------------------------------

def test_planner_decompose_6_phases():
    planner = Planner()
    subtasks = planner.decompose(Task(description="Build API"))
    assert len(subtasks) == 6
    phases = {st.metadata["phase"] for st in subtasks}
    assert phases == {"implementation", "review", "testing", "documentation", "security", "devops"}


# ---- 6. Planner assign + aggregate --------------------------------------

def test_planner_assign_aggregate():
    planner = Planner()
    coder = Coder()
    subtask = Task(description="Implement X", metadata={"parent_task_id": "root", "phase": "implementation"})
    result = planner.assign(subtask, coder)
    assert result.agent_name == "Coder"
    aggregated = planner.aggregate([result])
    assert "[Coder]" in aggregated.content


# ---- 7-12. Individual worker execution -----------------------------------

def test_coder_execute():
    coder = Coder(compressor=DogmaCompressor(ratio=1.0))
    result = coder.receive_task(Task(description="compression service"))
    assert result.agent_name == "Coder"
    assert "def solution" in result.content


def test_reviewer_execute():
    reviewer = Reviewer(compressor=DogmaCompressor(ratio=1.0))
    result = reviewer.receive_task(Task(description="compression service"))
    assert result.agent_name == "Reviewer"
    assert "APPROVED" in result.content


def test_tester_execute():
    tester = Tester(compressor=DogmaCompressor(ratio=1.0))
    result = tester.receive_task(Task(description="compression service"))
    assert result.agent_name == "Tester"
    assert "def test_basic" in result.content


def test_documenter_execute():
    documenter = Documenter(compressor=DogmaCompressor(ratio=1.0))
    result = documenter.receive_task(Task(description="compression service"))
    assert result.agent_name == "Documenter"
    assert "Documentation" in result.content


def test_security_guard_execute():
    guard = SecurityGuard(compressor=DogmaCompressor(ratio=1.0))
    result = guard.receive_task(Task(description="compression service"))
    assert result.agent_name == "SecurityGuard"
    assert "SECURE" in result.content


def test_devops_execute():
    devops = DevOps(compressor=DogmaCompressor(ratio=1.0))
    result = devops.receive_task(Task(description="compression service"))
    assert result.agent_name == "DevOps"
    assert "READY_TO_DEPLOY" in result.content


# ---- 13. Full controller cycle -------------------------------------------

def test_full_cycle_7_agents():
    lib = SkillLibrary()
    planner = Planner(skill_library=lib)
    agents = {
        "Coder": Coder(skill_library=lib),
        "Reviewer": Reviewer(skill_library=lib),
        "Tester": Tester(skill_library=lib),
        "Documenter": Documenter(skill_library=lib),
        "SecurityGuard": SecurityGuard(skill_library=lib),
        "DevOps": DevOps(skill_library=lib),
    }
    controller = Controller(planner=planner, agents=agents, skill_library=lib)

    task = Task(description="Create a microservice for text compression")
    controller.enqueue(task)
    assert controller.pending_count == 1

    results = controller.run()

    assert controller.pending_count == 0
    assert len(results) == 1
    assert results[0].agent_name == "Planner"
    assert "Create a microservice for text compression" in lib.skills
    # 6 subtask completions + enqueue + processing + decomposed + aggregated + stored_skill
    assert len(controller.log) >= 10
