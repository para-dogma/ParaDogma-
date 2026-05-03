"""
DOGMA Agent Framework -- multi-role agent system.

Provides specialised AI agents (Planner, Coder, Reviewer, Tester) that
communicate through DogmaNode transport and share experience via a
shared SkillLibrary.  Responses are compressed with DogmaCompressor to
keep inter-agent traffic lightweight.
"""

from agents.base import BaseAgent
from agents.roles import Planner, Coder, Reviewer, Tester
from agents.controller import Controller

__all__ = [
    "BaseAgent",
    "Planner",
    "Coder",
    "Reviewer",
    "Tester",
    "Controller",
]
