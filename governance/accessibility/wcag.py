"""
Accessibility & health-literacy checks for AI-generated member/patient material.

Two obligations converge on patient- and member-facing output in healthcare:

  * ADA Title III / Section 504 and the HHS **Section 1557** nondiscrimination
    rule (45 CFR Part 92) — effective provisions phasing in through 2026–2027 —
    require effective communication and accessible web/mobile content, with the
    rule referencing WCAG 2.1 Level AA for patient-facing digital content and
    explicit requirements around the use of patient-care decision-support tools.
  * Health literacy — CMS and the Joint Commission expect member communications,
    denial/appeal notices, and patient instructions to be written at roughly a
    6th–8th grade reading level (plain-language standard).

Every agent's rendered member/patient text passes these deterministic checks,
which catch the most common WCAG AA failures and over-complex language before
content reaches a patient or member. This is a fast pre-flight, not a substitute
for full WCAG auditing (axe-core in CI, manual screen-reader testing) or a
qualified-interpreter language-access program.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

_IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
_ALT_RE = re.compile(r'\balt\s*=', re.I)
_H_RE = re.compile(r"<h([1-6])\b", re.I)
_LINK_TEXT_RE = re.compile(r"<a\b[^>]*>(.*?)</a>", re.I | re.S)
_VAGUE_LINKS = {"click here", "here", "read more", "link", "this"}


@dataclass
class AccessibilityReport:
    issues: List[str] = field(default_factory=list)

    @property
    def passes(self) -> bool:
        return not self.issues


def check_html(html: str) -> AccessibilityReport:
    rep = AccessibilityReport()
    if not html:
        return rep
    # 1.1.1 Non-text content: every <img> needs an alt attribute
    for img in _IMG_RE.findall(html):
        if not _ALT_RE.search(img):
            rep.issues.append(f"WCAG 1.1.1: <img> missing alt attribute: {img[:60]}")
    # 1.3.1 / 2.4.6 Heading order: no skipped levels
    levels = [int(m) for m in _H_RE.findall(html)]
    for prev, cur in zip(levels, levels[1:]):
        if cur > prev + 1:
            rep.issues.append(f"WCAG 1.3.1: heading level jumps from h{prev} to h{cur}")
    # 2.4.4 Link purpose: no vague link text
    for txt in _LINK_TEXT_RE.findall(html):
        clean = re.sub(r"<[^>]+>", "", txt).strip().lower()
        if clean in _VAGUE_LINKS:
            rep.issues.append(f"WCAG 2.4.4: non-descriptive link text {clean!r}")
    return rep


def check_plain_language(text: str, max_grade: float = 8.0) -> AccessibilityReport:
    """
    Flesch-Kincaid grade-level check (proxy for health literacy / plain language;
    CMS and the Joint Commission target ~6th-8th grade for patient material).
    Deterministic, dependency-free.
    """
    rep = AccessibilityReport()
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words_list = re.findall(r"[A-Za-z]+", text)
    words = max(1, len(words_list))

    def syllables(w: str) -> int:
        w = w.lower()
        groups = re.findall(r"[aeiouy]+", w)
        n = len(groups)
        if w.endswith("e") and n > 1:
            n -= 1
        return max(1, n)

    syl = sum(syllables(w) for w in words_list)
    grade = 0.39 * (words / sentences) + 11.8 * (syl / words) - 15.59
    if grade > max_grade:
        rep.issues.append(f"Health literacy: reading grade {grade:.1f} exceeds target {max_grade}")
    return rep
