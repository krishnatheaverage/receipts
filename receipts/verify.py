"""The part that matters: check every quote the model claimed against the actual
source transcripts. This is deterministic string matching, NOT another LLM call
-- you don't verify a model with the same model.

Each quote lands in one of five buckets:

  verified      quote appears (near-)verbatim in the cited transcript
  loose         quote is close but paraphrased / not verbatim
  misattributed quote isn't in the cited transcript, but IS in another one
  unverified    quote isn't in any transcript (fabricated)
  bad_source    the cited transcript_id doesn't exist

The "grounded score" is the headline number: what fraction of the insights are
actually backed by real, correctly-attributed evidence."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .data import Transcript
from .models import Synthesis

VERIFIED = "verified"
LOOSE = "loose"
MISATTRIBUTED = "misattributed"
UNVERIFIED = "unverified"
BAD_SOURCE = "bad_source"

# A quote scoring >= VERBATIM_THRESHOLD against a transcript is treated as a real
# quote from it; between LOOSE and VERBATIM it's a paraphrase.
VERBATIM_THRESHOLD = 0.97
LOOSE_THRESHOLD = 0.80


def _normalize(s: str) -> list[str]:
    """Lowercase, straighten smart quotes/dashes, drop punctuation, tokenize."""
    s = s.lower()
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "—": " ", "–": " ", "…": " ",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    s = re.sub(r"[^\w\s]", " ", s)
    return s.split()


def match_score(quote: str, source: str) -> float:
    """Fraction of the quote's words that appear, in order, in the source.
    1.0 == every word of the quote is present as an in-order run (verbatim)."""
    q = _normalize(quote)
    s = _normalize(source)
    if not q:
        return 0.0
    matcher = difflib.SequenceMatcher(None, s, q, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    return matched / len(q)


@dataclass
class VerifiedEvidence:
    speaker: str
    quote: str
    cited_id: str
    status: str
    score: float
    found_in: str | None = None  # populated for misattributed quotes


@dataclass
class VerifiedTheme:
    title: str
    summary: str
    evidence: list[VerifiedEvidence] = field(default_factory=list)

    @property
    def grounded_score(self) -> float:
        return _grounded([e for e in self.evidence])


@dataclass
class VerificationReport:
    themes: list[VerifiedTheme]
    counts: dict[str, int]
    total: int

    @property
    def grounded_score(self) -> float:
        return _grounded([e for t in self.themes for e in t.evidence])


def _grounded(evidence: list[VerifiedEvidence]) -> float:
    if not evidence:
        return 0.0
    # verified counts fully; a paraphrase counts half; everything else is zero.
    score = sum(1.0 if e.status == VERIFIED else 0.5 if e.status == LOOSE else 0.0
                for e in evidence)
    return score / len(evidence)


def _classify(quote: str, cited_id: str, sources: dict[str, str]) -> VerifiedEvidence:
    def best_other() -> tuple[str | None, float]:
        best_id, best = None, 0.0
        for tid, text in sources.items():
            if tid == cited_id:
                continue
            s = match_score(quote, text)
            if s > best:
                best_id, best = tid, s
        return best_id, best

    if cited_id not in sources:
        other_id, other = best_other()
        if other >= VERBATIM_THRESHOLD:
            return VerifiedEvidence("", quote, cited_id, MISATTRIBUTED, other, other_id)
        return VerifiedEvidence("", quote, cited_id, BAD_SOURCE, 0.0)

    score = match_score(quote, sources[cited_id])
    if score >= VERBATIM_THRESHOLD:
        return VerifiedEvidence("", quote, cited_id, VERIFIED, score)
    if score >= LOOSE_THRESHOLD:
        return VerifiedEvidence("", quote, cited_id, LOOSE, score)

    other_id, other = best_other()
    if other >= VERBATIM_THRESHOLD:
        return VerifiedEvidence("", quote, cited_id, MISATTRIBUTED, other, other_id)
    return VerifiedEvidence("", quote, cited_id, UNVERIFIED, score)


def verify_synthesis(
    synthesis: Synthesis, transcripts: list[Transcript]
) -> VerificationReport:
    sources = {t.id: t.text for t in transcripts}

    themes: list[VerifiedTheme] = []
    counts: dict[str, int] = {
        VERIFIED: 0, LOOSE: 0, MISATTRIBUTED: 0, UNVERIFIED: 0, BAD_SOURCE: 0
    }
    total = 0

    for theme in synthesis.themes:
        vt = VerifiedTheme(title=theme.title, summary=theme.summary)
        for ev in theme.evidence:
            result = _classify(ev.quote, ev.transcript_id, sources)
            result.speaker = ev.speaker
            vt.evidence.append(result)
            counts[result.status] += 1
            total += 1
        themes.append(vt)

    return VerificationReport(themes=themes, counts=counts, total=total)
