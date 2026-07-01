"""Optional Streamlit UI for Receipts.

    pip install -r requirements-app.txt
    streamlit run app.py

Paste transcripts (or use the bundled samples), and see themes with a verified
quote under each insight and a live grounded score.
"""

from __future__ import annotations

import streamlit as st

from receipts.data import Transcript, load_transcripts
from receipts.pipeline import MODEL, synthesize
from receipts.verify import (
    BAD_SOURCE, LOOSE, MISATTRIBUTED, UNVERIFIED, VERIFIED, verify_synthesis,
)

_ICON = {
    VERIFIED: "✅", LOOSE: "🟡", MISATTRIBUTED: "🟠",
    UNVERIFIED: "🔴", BAD_SOURCE: "🔴",
}

st.set_page_config(page_title="Receipts", page_icon="🧾")
st.title("🧾 Receipts")
st.caption("Research synthesis where every insight carries a verified, source-linked quote.")

model = st.text_input("Model", MODEL)

if st.button("Use bundled sample transcripts"):
    st.session_state["transcripts"] = load_transcripts("data/transcripts")

if "transcripts" in st.session_state:
    transcripts = st.session_state["transcripts"]
    st.success(f"Loaded {len(transcripts)} transcripts.")

    if st.button("Synthesize + verify", type="primary"):
        with st.spinner("Extracting themes and checking every quote..."):
            synthesis = synthesize(transcripts, model=model)
            report = verify_synthesis(synthesis, transcripts)

        grounded = round(report.grounded_score * 100)
        st.metric("Grounded score", f"{grounded}%",
                  help="Fraction of insights backed by verified, correctly-attributed quotes")
        c = report.counts
        st.write(
            f"✅ {c[VERIFIED]} verified · 🟡 {c[LOOSE]} paraphrased · "
            f"🟠 {c[MISATTRIBUTED]} misattributed · "
            f"🔴 {c[UNVERIFIED] + c[BAD_SOURCE]} not found"
        )

        for theme in report.themes:
            with st.expander(f"{round(theme.grounded_score * 100)}%  —  {theme.title}"):
                st.write(theme.summary)
                for e in theme.evidence:
                    src = e.cited_id
                    if e.status == MISATTRIBUTED and e.found_in:
                        src = f"{e.cited_id} → actually {e.found_in}"
                    st.markdown(
                        f"{_ICON[e.status]} *“{e.quote}”*  \n"
                        f"<span style='color:#888;font-size:0.85em'>{e.speaker} · {src} "
                        f"· match {round(e.score * 100)}%</span>",
                        unsafe_allow_html=True,
                    )
else:
    st.info("Click the button above to load the bundled sample transcripts.")
