"""
Tests for the DOGMA Agent Framework.

Covers: agent initialisation, skill enrichment, response compression,
task decomposition, assignment, aggregation, role-specific execution,
transport and the full controller lifecycle.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base import (
    BaseAgent,
    DogmaCompressor,
    DogmaNode,
    Result,
    SkillLibrary,
    Task,
)
from agents.roles import Planner, Coder, Reviewer, Tester
from agents.controller import Controller


# ---- 1. Agent initialisation --------------------------------------------

def test_agent_init():
    agent = BaseAgent(name="A")
    assert agent.name == "A"
    assert isinstance(agent.compressor, DogmaCompressor)
    assert isinstance(agent.node, DogmaNode)
    assert isinstance(agent.skill_library, SkillLibrary)
    assert agent.task_log == []


# ---- 2. Skill enrichment ------------------------------------------------

def test_enrich_with_matching_skill():
    lib = SkillLibrary()
    lib.store("sorting", "Use quicksort for large arrays")
    agent = BaseAgent(name="A", skill_library=lib)

    task = Task(description="Write a sorting algorithm")
    enriched = agent.enrich_with_skills(task)

    assert len(enriched.enriched_skills) == 1
    assert enriched.enriched_skills[0]["skill"] == "sorting"


def test_enrich_no_match():
    lib = SkillLibrary()
    lib.store("database", "Use connection pooling")
    agent = BaseAgent(name="A", skill_library=lib)

    task = Task(description="Write a sorting algorithm")
    enriched = agent.enrich_with_skills(task)
    assert enriched.enriched_skills == []


# ---- 3. Response compression --------------------------------------------

def test_compress_response():
    compressor = DogmaCompressor(ratio=0.5)
    agent = BaseAgent(name="A", compressor=compressor)

    result = Result(task_id="t1", agent_name="A", content="X" * 100)
    compressed = agent.compress_response(result)

    assert compressed.compressed is True
    assert len(compressed.content) == 50


def test_compress_idempotent():
    agent = BaseAgent(name="A")
    result = Result(task_id="t1", agent_name="A", content="hello", compressed=True)
    out = agent.compress_response(result)
    assert out.content == "hello"


# ---- 4. Transport -------------------------------------------------------

def test_send_result_via_transport():
    sender = BaseAgent(name="S")
    receiver = BaseAgent(name="R")

    result = Result(task_id="t1", agent_name="S", content="payload")
    sender.send_result(result, receiver)

    messages = receiver.node.receive()
    assert len(messages) == 1
    assert messages[0]["from"] == "S"
    assert messages[0]["payload"]["content"] == "payload"


# ---- 5. Planner decompose -----------------------------------------------

def test_planner_decompose():
    planner = Planner()
    subtasks = planner.decompose(Task(description="Build API"))

    assert len(subtasks) == 3
    phases = {st.metadata["phase"] for st in subtasks}
    assert phases == {"implementation", "review", "testing"}


# ---- 6. Planner assign + aggregate --------------------------------------

def test_planner_assign_aggregate():
    planner = Planner()
    coder = Coder()

    subtask = Task(description="Implement X", metadata={"parent_task_id": "root", "phase": "implementation"})
    result = planner.assign(subtask, coder)

    assert result.agent_name == "Coder"
    aggregated = planner.aggregate([result])
    assert "[Coder]" in aggregated.content


# ---- 7. Coder execution -------------------------------------------------

def test_coder_execute():
    coder = Coder(compressor=DogmaCompressor(ratio=1.0))
    result = coder.receive_task(Task(description="sorting function"))
    assert result.agent_name == "Coder"
    assert "def solution" in result.content


# ---- 8. Reviewer execution ----------------------------------------------

def test_reviewer_execute():
    reviewer = Reviewer(compressor=DogmaCompressor(ratio=1.0))
    result = reviewer.receive_task(Task(description="sorting function"))
    assert result.agent_name == "Reviewer"
    assert "APPROVED" in result.content


# ---- 9. Tester execution ------------------------------------------------

def test_tester_execute():
    tester = Tester(compressor=DogmaCompressor(ratio=1.0))
    result = tester.receive_task(Task(description="sorting function"))
    assert result.agent_name == "Tester"
    assert "def test_basic" in result.content


# ---- 10. Full controller cycle -------------------------------------------

def test_full_controller_cycle():
    lib = SkillLibrary()
    planner = Planner(skill_library=lib)
    coder = Coder(skill_library=lib)
    reviewer = Reviewer(skill_library=lib)

    controller = Controller(planner=planner, agents={"Coder": coder, "Reviewer": reviewer}, skill_library=lib)

    task = Task(description="Write a sorting function")
    controller.enqueue(task)
    assert controller.pending_count == 1

    results = controller.run()

    assert controller.pending_count == 0
    assert len(results) == 1
    assert results[0].agent_name == "Planner"
    assert "Write a sorting function" in lib.skills
    assert len(controller.log) >= 4
