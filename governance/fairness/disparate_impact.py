"""
Disparate-impact screening for any agent that FLAGS or RANKS people or cases —
prior-authorization recommendations, utilization-management criteria evaluation,
care-management risk stratification, and payment-integrity claim flagging.

Algorithmic bias in utilization management and risk scoring is an active
regulatory and litigation concern (CMS guidance that AI must not discriminate in
Medicare Advantage coverage decisions; Section 1557 nondiscrimination; state UM
laws). This control implements the EEOC "four-fifths rule": if the selection
(flag) rate for any group is less than 80% of the rate for the highest-selected
group, the screen is flagged for human review. An anomaly is never proof; this
control exists so a model that disproportionately flags a protected group is
caught before any adverse action — which the platform never automates anyway
(issue_determination is withheld from every agent).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DisparateImpactReport:
    selection_rates: Dict[str, float] = field(default_factory=dict)
    most_selected_group: str = ""
    impact_ratios: Dict[str, float] = field(default_factory=dict)
    flagged_groups: List[str] = field(default_factory=list)

    @property
    def passes_four_fifths(self) -> bool:
        return not self.flagged_groups


def four_fifths(selected: Dict[str, int], totals: Dict[str, int]) -> DisparateImpactReport:
    rep = DisparateImpactReport()
    for g, total in totals.items():
        rep.selection_rates[g] = (selected.get(g, 0) / total) if total else 0.0
    if not rep.selection_rates:
        return rep
    rep.most_selected_group = max(rep.selection_rates, key=rep.selection_rates.get)
    top = rep.selection_rates[rep.most_selected_group] or 1e-9
    for g, rate in rep.selection_rates.items():
        ratio = rate / top
        rep.impact_ratios[g] = round(ratio, 3)
        if ratio < 0.8:
            rep.flagged_groups.append(g)
    return rep
