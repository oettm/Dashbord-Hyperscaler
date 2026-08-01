import streamlit as st


def _safe(note: str) -> str:
    # Streamlit's markdown renderer treats a "$...$" pair as inline LaTeX;
    # commentary quotes routinely contain bare dollar amounts (e.g. "$250M"),
    # so escape "$" or a stray one turns half a sentence into a math block.
    return note.replace("$", "\\$")


def render(comparison: dict):
    st.header("Qualitative notes: management commentary")

    companies = sorted(comparison.keys())
    company = st.selectbox("Company", companies, key="notes_company")
    comp = comparison[company]
    commentary = comp.get("commentary", {})

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Q1")
        q1_notes = commentary.get("q1", [])
        if not q1_notes:
            st.write("No commentary extracted.")
        for note in q1_notes:
            st.markdown(f"> {_safe(note)}")
            st.write("")
    with col2:
        st.subheader("Q2")
        if not comp["q2_available"]:
            st.info("Q2 is not available for this company.")
        else:
            q2_notes = commentary.get("q2", [])
            if not q2_notes:
                st.write("No commentary extracted.")
            for note in q2_notes:
                st.markdown(f"> {_safe(note)}")
                st.write("")
