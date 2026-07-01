"""Render a VerificationReport as a self-contained HTML dashboard. This is what
you screenshot for the Loom: themes, quotes, source badges, and a red flag on
anything the verifier couldn't back up."""

from __future__ import annotations

import html

from .verify import (
    BAD_SOURCE, LOOSE, MISATTRIBUTED, UNVERIFIED, VERIFIED, VerificationReport,
)

_STATUS_LABEL = {
    VERIFIED: "verified",
    LOOSE: "paraphrased",
    MISATTRIBUTED: "misattributed",
    UNVERIFIED: "not found",
    BAD_SOURCE: "bad source",
}

_STATUS_COLOR = {
    VERIFIED: "#1a7f4b",
    LOOSE: "#b7791f",
    MISATTRIBUTED: "#c05621",
    UNVERIFIED: "#c53030",
    BAD_SOURCE: "#c53030",
}


def _pill(status: str) -> str:
    color = _STATUS_COLOR.get(status, "#666")
    label = _STATUS_LABEL.get(status, status)
    return (
        f'<span class="pill" style="background:{color}1a;color:{color};'
        f'border:1px solid {color}55">{label}</span>'
    )


def render_html(report: VerificationReport, subtitle: str = "") -> str:
    grounded = round(report.grounded_score * 100)
    grounded_color = "#1a7f4b" if grounded >= 85 else "#b7791f" if grounded >= 60 else "#c53030"

    theme_html = []
    for theme in report.themes:
        ev_html = []
        for e in theme.evidence:
            source = html.escape(e.cited_id)
            if e.status == MISATTRIBUTED and e.found_in:
                source = f"{source} &rarr; actually {html.escape(e.found_in)}"
            ev_html.append(
                f'<li class="evidence">'
                f'<div class="quote">&ldquo;{html.escape(e.quote)}&rdquo;</div>'
                f'<div class="meta">{_pill(e.status)}'
                f'<span class="src">{html.escape(e.speaker)} &middot; {source}</span>'
                f'<span class="score">match {round(e.score * 100)}%</span></div>'
                f"</li>"
            )
        tscore = round(theme.grounded_score * 100)
        theme_html.append(
            f'<section class="theme">'
            f'<div class="theme-head"><h2>{html.escape(theme.title)}</h2>'
            f'<span class="theme-score">{tscore}% grounded</span></div>'
            f'<p class="summary">{html.escape(theme.summary)}</p>'
            f'<ul>{"".join(ev_html)}</ul>'
            f"</section>"
        )

    c = report.counts
    breakdown = (
        f'<span style="color:{_STATUS_COLOR[VERIFIED]}">{c[VERIFIED]} verified</span> &middot; '
        f'<span style="color:{_STATUS_COLOR[LOOSE]}">{c[LOOSE]} paraphrased</span> &middot; '
        f'<span style="color:{_STATUS_COLOR[MISATTRIBUTED]}">{c[MISATTRIBUTED]} misattributed</span> &middot; '
        f'<span style="color:{_STATUS_COLOR[UNVERIFIED]}">'
        f'{c[UNVERIFIED] + c[BAD_SOURCE]} not found</span>'
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Receipts</title>
<style>
  :root {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  body {{ margin:0; background:#f6f7f9; color:#1a202c; }}
  .wrap {{ max-width:820px; margin:0 auto; padding:48px 24px 80px; }}
  header h1 {{ font-size:34px; margin:0 0 4px; letter-spacing:-.02em; }}
  header p {{ color:#718096; margin:0 0 28px; }}
  .scorecard {{ background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:24px 28px; margin-bottom:32px; display:flex; align-items:baseline; gap:20px; }}
  .big {{ font-size:52px; font-weight:700; line-height:1; color:{grounded_color}; }}
  .scorecard .label {{ font-size:14px; color:#718096; }}
  .scorecard .breakdown {{ margin-top:6px; font-size:13px; }}
  .theme {{ background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:22px 26px; margin-bottom:18px; }}
  .theme-head {{ display:flex; justify-content:space-between; align-items:baseline; }}
  .theme h2 {{ font-size:19px; margin:0; }}
  .theme-score {{ font-size:12px; color:#718096; white-space:nowrap; }}
  .summary {{ color:#4a5568; margin:8px 0 16px; }}
  ul {{ list-style:none; padding:0; margin:0; }}
  .evidence {{ border-left:3px solid #e2e8f0; padding:4px 0 4px 14px; margin:14px 0; }}
  .quote {{ font-size:15px; line-height:1.5; }}
  .meta {{ margin-top:7px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .pill {{ font-size:11px; font-weight:600; padding:2px 9px; border-radius:20px;
    text-transform:uppercase; letter-spacing:.03em; }}
  .src {{ font-size:13px; color:#718096; }}
  .score {{ font-size:12px; color:#a0aec0; margin-left:auto; }}
  footer {{ margin-top:36px; font-size:12px; color:#a0aec0; text-align:center; }}
</style></head>
<body><div class="wrap">
  <header><h1>Receipts</h1><p>{html.escape(subtitle)}</p></header>
  <div class="scorecard">
    <div class="big">{grounded}%</div>
    <div><div class="label">of insights are backed by verified, correctly-attributed quotes</div>
      <div class="breakdown">{breakdown} &middot; {report.total} total</div></div>
  </div>
  {"".join(theme_html)}
  <footer>Every quote checked against the source transcript by deterministic string
  matching &mdash; no model grades its own homework.</footer>
</div></body></html>"""


def write_report(path: str, report: VerificationReport, subtitle: str = "") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_html(report, subtitle))
