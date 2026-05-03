"""
Hierarchical AI - Multi-agent platform built on the DOGMA stack.

Combines DOGMA Compressor, Transport (DogmaNode) and Skill Library
into a unified system of hierarchical agents that decompose complex
tasks, execute them in parallel and compress results for efficient
inter-agent communication.
"""

from hierarchical.node import HierarchicalAgent
from hierarchical.planner import Planner
from hierarchical.worker import Coder, Reviewer, Tester
from hierarchical.controller import Controller

__all__ = [
    "HierarchicalAgent",
    "Planner",
    "Coder",
    "Reviewer",
    "Tester",
    "Controller",
]
