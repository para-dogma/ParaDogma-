"""
Hierarchical AI -- complete agent ecosystem with 7 specialised roles.

Built on the DOGMA stack: Compressor, Transport (DogmaNode) and Skill Library.
"""

from hierarchical.node import HierarchicalAgent
from hierarchical.planner import Planner
from hierarchical.workers import Coder, Reviewer, Tester, Documenter, SecurityGuard, DevOps
from hierarchical.controller import Controller

__all__ = [
    "HierarchicalAgent",
    "Planner",
    "Coder",
    "Reviewer",
    "Tester",
    "Documenter",
    "SecurityGuard",
    "DevOps",
    "Controller",
]
