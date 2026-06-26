# agent/persistence.py
"""Checkpointer for LangGraph (enables interrupt/resume HITL). In-memory for demo;
swap for a DynamoDB/Redis saver in production so a suspended human-gate (a denials
specialist reviewing an appeal) survives a process restart."""
from __future__ import annotations


def get_checkpointer():
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
