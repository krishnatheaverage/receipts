"""The schema Claude fills in. These are the *claims* the model makes; nothing
here is trusted until verify.py checks each quote against the source text.

Kept deliberately flat and constraint-free: the structured-outputs API rejects
things like minLength/maxLength, and messages.parse() enforces the shape."""

from pydantic import BaseModel


class Evidence(BaseModel):
    transcript_id: str  # which transcript the quote came from
    speaker: str        # who said it
    quote: str          # copied verbatim from the transcript (we verify this)


class Theme(BaseModel):
    title: str
    summary: str            # one-sentence finding
    evidence: list[Evidence]


class Synthesis(BaseModel):
    themes: list[Theme]
