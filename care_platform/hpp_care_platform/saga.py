"""
Durable saga with compensation — no half-finished journeys.

A journey is a sequence of Steps, each owning agent + a forward action and an optional
compensating action. The saga runs steps in order; if a step raises, it runs the
compensating actions of the already-completed steps **in reverse** (the saga pattern),
emitting a compliance event for every forward and compensating action. A step that
hits the human gate (PENDING_APPROVAL) suspends the journey — exactly like the
agent-level gate — rather than proceeding.

This is the in-process reference; the AWS-native form is a Step Functions state machine
(`aws-native-reference/care-platform/`) where compensation is a Catch→compensate path
and the human gate is a waitForTaskToken task.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .events import ComplianceEventBus


class JourneySuspended(Exception):
    """A step requires human approval; the journey is suspended (not failed)."""
    def __init__(self, step: str, message: str = "") -> None:
        super().__init__(message or f"journey suspended at {step}")
        self.step = step


@dataclass
class Step:
    name: str
    agent_id: str
    action: Callable[[Dict[str, Any]], Any]
    compensate: Optional[Callable[[Dict[str, Any]], Any]] = None


@dataclass
class SagaResult:
    completed: List[str] = field(default_factory=list)
    compensated: List[str] = field(default_factory=list)
    suspended_at: Optional[str] = None
    failed_at: Optional[str] = None
    status: str = "RUNNING"          # COMPLETED | SUSPENDED | COMPENSATED
    context: Dict[str, Any] = field(default_factory=dict)


class Saga:
    def __init__(self, name: str, steps: List[Step], bus: Optional[ComplianceEventBus] = None) -> None:
        self.name = name
        self.steps = steps
        self.bus = bus or ComplianceEventBus()

    def run(self, context: Dict[str, Any]) -> SagaResult:
        res = SagaResult(context=context)
        done: List[Step] = []
        for step in self.steps:
            try:
                step.action(context)
            except JourneySuspended as s:
                self.bus.emit(journey=self.name, step=step.name, agent_id=step.agent_id,
                              status="SUSPENDED", subject_ref=context.get("subject_ref", ""))
                res.suspended_at = s.step
                res.status = "SUSPENDED"
                return res
            except Exception as exc:  # forward step failed -> compensate in reverse
                self.bus.emit(journey=self.name, step=step.name, agent_id=step.agent_id,
                              status="FAILED", subject_ref=context.get("subject_ref", ""),
                              detail=type(exc).__name__)
                res.failed_at = step.name
                for prev in reversed(done):
                    if prev.compensate:
                        prev.compensate(context)
                        res.compensated.append(prev.name)
                        self.bus.emit(journey=self.name, step=prev.name, agent_id=prev.agent_id,
                                      status="COMPENSATED", subject_ref=context.get("subject_ref", ""))
                res.status = "COMPENSATED"
                return res
            done.append(step)
            res.completed.append(step.name)
            self.bus.emit(journey=self.name, step=step.name, agent_id=step.agent_id,
                          status="OK", subject_ref=context.get("subject_ref", ""))
        res.status = "COMPLETED"
        return res
