"""
Multi-Agent System for Mathematics Teaching & Didactic Engineering
"""

from math_teaching_agents.profile import (
    load_profile,
    save_profile,
    get_profile_path,
    run_init_wizard,
    inject_profile_into_prompt,
)

__version__ = "0.6.0"
__author__ = "Math Teaching Agents Contributors"

__all__ = [
    "load_profile",
    "save_profile",
    "get_profile_path",
    "run_init_wizard",
    "inject_profile_into_prompt",
]
