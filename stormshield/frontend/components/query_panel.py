"""
StormShield AI conversational query panel.
Uses st.chat_input + st.chat_message to provide a chat-style RAG interface.
"""
from __future__ import annotations

import httpx
import streamlit as st


def render_query_panel(backend_url: str) -> None:
    """Render the conversational query panel with chat-style UI."""
    if "query_history" not in st.session_state:
        st.session_state["query_history"] = []

    st.markdown("""
    <div style="font-size:13px; color:#94a3b8; margin-bottom:12px;">
        Ask StormShield AI anything about current flood conditions, road closures,
        evacuation timing, or safe areas.
    </div>
    """, unsafe_allow_html=True)

    # Render chat history
    for turn in st.session_state["query_history"]:
        with st.chat_message("user", avatar="🧑"):
            st.write(turn["q"])
        with st.chat_message("assistant", avatar="🛡️"):
            st.write(turn["a"])
            st.caption(f"Grounded at: {turn.get('grounded_at', '')[:19]} UTC")

    # Input
    question = st.chat_input(
        "Ask about current flood conditions…",
        key="query_input",
    )

    if question:
        with st.chat_message("user", avatar="🧑"):
            st.write(question)

        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("StormShield AI is thinking…"):
                try:
                    # Last 5 turns as history
                    history = [
                        {"q": t["q"], "a": t["a"]}
                        for t in st.session_state["query_history"][-5:]
                    ]
                    resp = httpx.post(
                        f"{backend_url}/api/query",
                        json={"question": question, "history": history},
                        timeout=20,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    answer = data.get("answer", "No answer returned.")
                    grounded_at = data.get("grounded_at", "")
                except Exception as exc:
                    answer = f"Unable to reach StormShield AI backend: {exc}"
                    grounded_at = ""

            st.write(answer)
            if grounded_at:
                st.caption(f"Grounded at: {grounded_at[:19]} UTC")

        # Append to history
        st.session_state["query_history"].append({
            "q": question,
            "a": answer,
            "grounded_at": grounded_at,
        })
