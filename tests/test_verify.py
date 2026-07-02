import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from receipts.data import Transcript
from receipts.models import Evidence, Synthesis, Theme
from receipts.verify import (
    MISATTRIBUTED, UNVERIFIED, VERIFIED, match_score, verify_synthesis,
)

TRANSCRIPTS = [
    Transcript(
        id="P01",
        participant="Maya",
        text="[maya] Honestly the biggest problem is I can never find past research. "
             "I redid a study last quarter that a teammate had already done.",
    ),
    Transcript(
        id="P02",
        participant="Dev",
        text="[dev] Leadership just doesn't trust our insights. They always ask "
             "where the number came from and I can't point them to the transcript.",
    ),
]


def test_match_score_verbatim_vs_absent():
    assert match_score("I can never find past research", TRANSCRIPTS[0].text) >= 0.97
    assert match_score("our onboarding flow is too slow", TRANSCRIPTS[0].text) < 0.8


def test_verify_labels_each_quote():
    synthesis = Synthesis(themes=[
        Theme(
            title="Rediscovery",
            summary="Past research is hard to find.",
            evidence=[
                Evidence(transcript_id="P01", speaker="Maya",
                         quote="I can never find past research"),
                Evidence(transcript_id="P01", speaker="Maya",
                         quote="we should just delete the whole repository"),
                Evidence(transcript_id="P01", speaker="Maya",
                         quote="Leadership just doesn't trust our insights"),
            ],
        )
    ])

    report = verify_synthesis(synthesis, TRANSCRIPTS)
    statuses = [e.status for e in report.themes[0].evidence]

    assert statuses[0] == VERIFIED, statuses
    assert statuses[1] == UNVERIFIED, statuses
    assert statuses[2] == MISATTRIBUTED, statuses
    assert report.themes[0].evidence[2].found_in == "P02"

    assert 0.30 <= report.grounded_score <= 0.40, report.grounded_score


if __name__ == "__main__":
    test_match_score_verbatim_vs_absent()
    test_verify_labels_each_quote()
    print("All verification tests passed.")
