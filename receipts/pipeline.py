"""The LLM half of the pipeline: transcripts in, a Synthesis (themes + claimed
quotes) out. This step is *not* trusted for faithfulness -- verify.py is.

Uses the Messages API structured-outputs path (messages.parse with a Pydantic
schema) so the model is forced to return the exact shape we need, with the
transcript_id attached to every quote."""

from __future__ import annotations

import anthropic

from .data import Transcript
from .models import Synthesis

# Default to the most capable model; the synthesis quality is what a reviewer
# sees first. Swap to "claude-haiku-4-5" for cheaper/faster runs.
MODEL = "claude-opus-4-8"

SYSTEM = """You are a user-research analyst. You are given a set of user-interview \
transcripts. Identify the 4-7 most important recurring themes across them.

For every theme:
- Write a one-sentence, specific summary of the finding (not a vague label).
- Attach 2-4 pieces of evidence. Each piece of evidence MUST be a quote copied
  VERBATIM from one transcript: word for word, exactly as it appears, with no
  paraphrasing, cleanup, or stitching fragments together. Copy the exact substring.
- Record which transcript each quote came from (transcript_id) and who said it (speaker).

Rules:
- Never invent, paraphrase, or combine quotes. If you cannot find a verbatim quote
  to support a theme, use fewer pieces of evidence or drop the theme entirely.
- Only cite transcript_ids that were provided to you.
- Attribute each quote to the transcript it actually came from.
- Prefer quotes that express the theme in the participant's own words."""


def _format_transcripts(transcripts: list[Transcript]) -> str:
    blocks = []
    for t in transcripts:
        blocks.append(
            f'<transcript id="{t.id}">\n'
            f"Participant: {t.participant}\n\n"
            f"{t.text}\n"
            f"</transcript>"
        )
    return "\n\n".join(blocks)


def synthesize(
    transcripts: list[Transcript],
    model: str = MODEL,
    client: anthropic.Anthropic | None = None,
) -> Synthesis:
    client = client or anthropic.Anthropic()

    user = (
        "Here are the interview transcripts. Extract the recurring themes with "
        "verbatim, attributed quotes.\n\n" + _format_transcripts(transcripts)
    )

    resp = client.messages.parse(
        model=model,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_format=Synthesis,
    )

    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError("Model refused or returned no structured output.")

    return resp.parsed_output
