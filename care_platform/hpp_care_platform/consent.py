"""
Consent ledger — AAL-gated, 42 CFR Part 2 aware.

Before a journey discloses or acts on sensitive data it records and checks consent.
Two properties matter:
  * **Assurance gating** — a sensitive-scope grant requires a minimum identity
    assurance level (AAL2); a weak session cannot authorize a sensitive disclosure.
  * **42 CFR Part 2** — SUD-related scopes are flagged; absent an explicit grant, the
    journey must escalate rather than proceed.

This is an in-memory reference ledger; production persists to a consent system of
record. The check is also enforced per-tool at the gateway (consent.check); this
ledger is the journey-level record + policy.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Dict, List

_SENSITIVE = {"42cfr_part2", "sud", "behavioral_health", "hiv", "reproductive"}


@dataclass
class ConsentGrant:
    subject_ref: str
    scope: str
    aal: str                       # e.g. AAL1, AAL2
    part2_sensitive: bool
    granted: bool
    ts: str = field(default_factory=lambda: _dt.datetime.now(_dt.timezone.utc).isoformat())


class ConsentLedger:
    def __init__(self) -> None:
        self._grants: List[ConsentGrant] = []

    def record(self, *, subject_ref: str, scope: str, aal: str = "AAL2", granted: bool = True) -> ConsentGrant:
        g = ConsentGrant(subject_ref=subject_ref, scope=scope, aal=aal,
                         part2_sensitive=scope.lower() in _SENSITIVE, granted=granted)
        self._grants.append(g)
        return g

    def permits(self, *, subject_ref: str, scope: str, aal: str = "AAL2") -> bool:
        sensitive = scope.lower() in _SENSITIVE
        for g in reversed(self._grants):
            if g.subject_ref == subject_ref and g.scope == scope:
                if not g.granted:
                    return False
                if sensitive and (g.aal != "AAL2" or aal != "AAL2"):
                    return False  # sensitive scope demands AAL2 at grant and at use
                return True
        # no explicit grant: deny sensitive, allow routine treatment/payment/operations
        return not sensitive and scope in {"treatment_payment_operations", "status_lookup"}
