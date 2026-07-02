from pydantic import BaseModel


class Evidence(BaseModel):
    transcript_id: str
    speaker: str
    quote: str


class Theme(BaseModel):
    title: str
    summary: str
    evidence: list[Evidence]


class Synthesis(BaseModel):
    themes: list[Theme]
