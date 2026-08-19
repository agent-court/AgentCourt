"""
AgentCourt SDK: Trust-minimized AI neural dispute arbitration on Base.
"""

from .client import AgentCourtClient
from .arbitrator import arbitrate_task
from .vector_precedents import find_relevant_precedents, record_new_precedent

__version__ = "0.1.0"
__all__ = ["AgentCourtClient", "arbitrate_task", "find_relevant_precedents", "record_new_precedent"]
