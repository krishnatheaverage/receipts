from dataclasses import dataclass
from pathlib import Path


@dataclass
class Transcript:
    id: str
    participant: str
    text: str


def load_transcripts(directory: str | Path) -> list[Transcript]:
    directory = Path(directory)
    transcripts: list[Transcript] = []

    for path in sorted(directory.glob("*.txt")):
        raw = path.read_text(encoding="utf-8").strip()
        lines = raw.splitlines()

        participant = path.stem
        body_start = 0
        for i, line in enumerate(lines):
            if line.lower().startswith("participant:"):
                participant = line.split(":", 1)[1].strip()
                body_start = i + 1
                break

        text = "\n".join(lines[body_start:]).strip()
        transcripts.append(Transcript(id=path.stem, participant=participant, text=text))

    if not transcripts:
        raise FileNotFoundError(f"No .txt transcripts found in {directory}")
    return transcripts
