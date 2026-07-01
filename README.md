# 🧾 Receipts

Turn a pile of user-interview transcripts into a themed insights report where
**every insight carries a verified, source-linked quote** — and anything the
model can't back up gets flagged instead of shipped.

Built as a demo for Great Question. Their product turns scattered customer
research into trustworthy insights, and two of the hard AI problems they call
out are *semantic synthesis across many interviews* and *evaluation frameworks*.
Receipts is a small, honest take on exactly that seam.

---

## The idea in one line

An LLM is great at spotting themes and lousy at being trusted. So let the model
propose themes and quotes, then **verify every quote against the source text
with plain code** and score how much of the output is actually grounded.

```
transcripts ──▶ Claude (themes + claimed quotes) ──▶ verifier (deterministic) ──▶ report
                     structured output                 checks every quote          grounded %
```

## What it does

1. **Ingests** a folder of `.txt` interview transcripts.
2. **Synthesizes** 4–7 recurring themes with Claude (`messages.parse` +
   structured outputs), forcing each theme to cite verbatim quotes with a
   `transcript_id`.
3. **Verifies** every quote against the actual transcript with deterministic
   string matching — sorting each into `verified`, `paraphrased`,
   `misattributed`, or `not found`.
4. **Reports** a **grounded score** (what fraction of insights are backed by
   real, correctly-attributed evidence) and renders an HTML dashboard with a red
   flag on anything unverified.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...     # see .env.example
python run.py                            # writes report.html
open report.html
```

Optional UI:

```bash
pip install -r requirements-app.txt
streamlit run app.py
```

Prove the verifier works without spending a token:

```bash
python tests/test_verify.py
```

The sample transcripts in `data/transcripts/` are **synthetic** (I wrote them),
deliberately about the pain of *finding and trusting past research* — which is
Great Question's own problem space.

---

## Design decisions (the interesting part)

**Why verify quotes with code instead of native API citations.** The Messages
API has a citations feature, but it's incompatible with structured JSON output —
and, more importantly, citations tell you *where* a model pointed, not *whether
it told the truth*. Receipts needs the second thing. So the model returns
`{transcript_id, quote}` as structured data and a separate layer checks the quote
actually exists in that transcript. That check is the product.

**Why the verifier is not another LLM.** You don't grade a model's faithfulness
with the same model — that just launders the hallucination. `verify.py` is
`difflib` and string normalization: word-level, order-aware matching against the
cited source. It's boring on purpose. Boring is auditable.

**Why four failure modes, not a boolean.** "Not grounded" hides useful
structure. A *paraphrase* is a style problem; a *misattributed* quote (real
words, wrong person) is a trust problem; a *not-found* quote is a hallucination.
The verifier even re-searches the other transcripts, so it can say "this quote is
fabricated" vs "this quote is real but you attributed it to P01, it's actually
P02." That distinction is what a researcher actually needs.

**The grounded score is the headline.** One number a PM can trust at a glance:
verified counts fully, a paraphrase counts half, a fabrication counts zero.

## What breaks at real scale (and what I'd build next)

- **8 transcripts fit in one context window; 10,000 interview-hours don't.** The
  synthesis step would become retrieve-then-synthesize: embed transcript chunks,
  pull the candidates relevant to each emerging theme, and synthesize over those.
  The verification layer doesn't change at all — that's the nice part of keeping
  it separate and deterministic.
- **Exact-ish matching is a floor, not a ceiling.** I'd add span offsets so each
  quote deep-links to its exact moment in the transcript/recording, and track
  quote *coverage* (are we citing a representative spread of participants, or the
  same two loud ones?).
- **Grounding is table stakes; the harder eval is "is this theme the right
  theme?"** That one probably does need a model-in-the-loop judge with a rubric,
  run against a labeled set — which is the kind of eval framework I'd want to
  build with you.

---

*Built by Krishna Harish. Transcripts are synthetic; the verification is real.*
