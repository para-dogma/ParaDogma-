"""
Tests for the Hierarchical AI multi-agent platform.

Covers: agent initialisation, skill enrichment, response compression,
task decomposition, assignment, aggregation, worker execution,
controller lifecycle and the full end-to-end cycle.
"""

from __future__ import annotations

import sys
import os
import pytest

# Ensure the repo root is on sys.path so that ``import hierarchical`` works
# regardless of where pytest is invoked from.
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
from hierarchical.worker import Coder, Reviewer, Tester
from hierarchical.controller import Controller


# ---- 1. Agent initialisation --------------------------------------------

def test_agent_initialisation():
    agent = HierarchicalAgent(name="TestAgent")

    assert agent.name == "TestAgent"
    assert isinstance(agent.compressor, DogmaCompressor)
    assert isinstance(agent.node, DogmaNode)
    assert isinstance(agent.skill_library, SkillLibrary)
    assert agent.task_log == []


# ---- 2. Skill enrichment ------------------------------------------------

def test_enrich_with_skills():
    lib = SkillLibrary()
    lib.store("sorting", "Use quicksort for large arrays")
    agent = HierarchicalAgent(name="A", skill_library=lib)

    task = Task(description="Write a sorting algorithm")
    enriched = agent.enrich_with_skills(task)

    assert len(enriched.enriched_skills) == 1
    assert enriched.enriched_skills[0]["skill"] == "sorting"


def test_enrich_with_no_matching_skills():
    lib = SkillLibrary()
    lib.store("database", "Use connection pooling")
    agent = HierarchicalAgent(name="A", skill_library=lib)

    task = Task(description="Write a sorting algorithm")
    enriched = agent.enrich_with_skills(task)

    assert enriched.enriched_skills == []


# ---- 3. Response compression --------------------------------------------

def test_compress_response():
    compressor = DogmaCompressor(ratio=0.5)
    agent = HierarchicalAgent(name="A", compressor=compressor)

    result = Result(task_id="t1", agent_name="A", content="A" * 100)
    compressed = agent.compress_response(result)

    assert compressed.compressed is True
    assert len(compressed.content) == 50


def test_compress_already_compressed():
    agent = HierarchicalAgent(name="A")
    result = Result(task_id="t1", agent_name="A", content="short", compressed=True)
    out = agent.compress_response(result)
    # Content should stay unchanged.
    assert out.content == "short"


# ---- 4. Task decomposition (Planner) ------------------------------------

def test_planner_decompose():
    planner = Planner()
    task = Task(description="Build a REST API")
    subtasks = planner.decompose(task)

    assert len(subtasks) == 3
    phases = [st.metadata["phase"] for st in subtasks]
    assert "implementation" in phases
    assert "review" in phases
    assert "testing" in phases


# ---- 5. Planner assign + aggregate --------------------------------------

def test_planner_assign_and_aggregate():
    planner = Planner()
    coder = Coder()

    subtask = Task(description="Implement feature X", metadata={"parent_task_id": "root", "phase": "implementation"})
    result = planner.assign(subtask, coder)

    assert result.agent_name == "Coder"
    assert "root" in planner.collected_results

    aggregated = planner.aggregate([result])
    assert aggregated.agent_name == "Planner"
    assert "[Coder]" in aggregated.content


# ---- 6. Worker execution ------------------------------------------------

def test_coder_execute():
    coder = Coder()
    task = Task(description="sorting function")
    result = coder.receive_task(task)

    assert result.agent_name == "Coder"
    assert "def solution" in result.content


def test_reviewer_execute():
    # Use a high compression ratio so the review text is not truncated.
    reviewer = Reviewer(compressor=DogmaCompressor(ratio=1.0))
    task = Task(description="sorting function")
    result = reviewer.receive_task(task)

    assert result.agent_name == "Reviewer"
    assert "APPROVED" in result.content


def test_tester_execute():
    tester = Tester()
    task = Task(description="sorting function")
    result = tester.receive_task(task)

    assert result.agent_name == "Tester"
    assert "def test_basic" in result.content


# ---- 7. Full end-to-end cycle via Controller -----------------------------

def test_full_cycle_via_controller():
    skill_library = SkillLibrary()
    planner = Planner(skill_library=skill_library)
    coder = Coder(skill_library=skill_library)
    reviewer = Reviewer(skill_library=skill_library)

    controller = Controller(
        planner=planner,
        agents={"Coder": coder, "Reviewer": reviewer},
        skill_library=skill_library,
    )

    task = Task(description="Write a sorting function")
    controller.enqueue(task)

    assert controller.pending_count == 1

    results = controller.run()

    assert controller.pending_count == 0
    assert len(results) == 1
    assert results[0].agent_name == "Planner"

    # The skill should have been persisted.
    assert "Write a sorting function" in skill_library.skills

    # Execution log should contain entries.
    assert len(controller.log) >= 4
