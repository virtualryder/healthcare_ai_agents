# agent/persistence.py
"""Checkpointer for LangGraph (interrupt/resume HITL). In-memory for demo; swap for a
DynamoDB/Redis saver in production so a suspended payment-integrity review survives a restart."""
from __future__ import annotations


def get_checkpointer():
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
