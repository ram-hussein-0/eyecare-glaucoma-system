from __future__ import annotations

from pathlib import Path
import html
import re
import sys
import time

_PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "backend").exists() and (p / "frontend").exists()
)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from markdown_it import MarkdownIt

from frontend.app_utils.auth import require_login
from frontend.app_utils.api import api_post_stream
from frontend.app_utils.ui import hero, section, setup_page


setup_page("AI Assistant", "assistant")
require_login()


st.markdown(
    """
    <style>
    .ai-assistant-shell {
        margin-top: .2rem;
    }

    .ai-rag-banner {
        border: 1px solid rgba(37, 99, 235, .14);
        background:
            radial-gradient(circle at top left, rgba(37,99,235,.12), transparent 30%),
            linear-gradient(135deg, #ffffff, #f8fbff 55%, #f0fdfa);
        border-radius: 28px;
        padding: 22px 24px;
        box-shadow: 0 20px 55px rgba(15, 23, 42, .08);
        margin-bottom: 18px;
    }

    .ai-rag-banner-title {
        font-size: 22px;
        font-weight: 950;
        color: #0f172a;
        margin: 0 0 8px;
    }

    .ai-rag-banner-text {
        color: #475569;
        line-height: 1.75;
        font-size: 14px;
        margin: 0;
    }

    .assistant-input-card {
        border: 1px solid rgba(226, 232, 240, .95);
        background: rgba(255,255,255,.96);
        border-radius: 24px;
        padding: 18px;
        box-shadow: 0 14px 38px rgba(15, 23, 42, .07);
        margin: 16px 0 20px;
    }

    .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin: 12px 0 8px;
    }

    .chat-stream {
        display: flex;
        flex-direction: column;
        gap: 14px;
        margin-top: 12px;
    }

    .message-row {
        display: grid;
        grid-template-columns: 44px minmax(0, 1fr);
        gap: 12px;
        align-items: flex-start;
        margin-bottom: 14px;
    }

    .message-row.user {
        grid-template-columns: minmax(0, 1fr) 44px;
    }

    .avatar-box {
        width: 44px;
        height: 44px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 12px 24px rgba(15,23,42,.09);
        border: 1px solid rgba(226,232,240,.9);
    }

    .avatar-assistant {
        background: linear-gradient(135deg, #2563eb, #14b8a6);
    }

    .avatar-user {
        background: linear-gradient(135deg, #0f172a, #475569);
    }

    .message-card {
        border: 1px solid rgba(226,232,240,.92);
        background: #ffffff;
        border-radius: 22px;
        padding: 15px 17px;
        box-shadow: 0 12px 32px rgba(15,23,42,.055);
    }

    .message-row.user .message-card {
        background: linear-gradient(135deg, #f8fafc, #ffffff);
    }

    .message-label {
        font-size: 12px;
        font-weight: 850;
        letter-spacing: .02em;
        color: #64748b;
        margin-bottom: 8px;
        text-transform: uppercase;
    }

    .message-text {
        color: #0f172a;
        font-size: 15.5px;
        line-height: 1.88;
        unicode-bidi: plaintext;
        word-break: break-word;
    }

    .message-text p {
        margin: 0 0 12px;
    }

    .message-text ul {
        margin: 8px 0 14px;
        padding-inline-start: 1.4rem;
    }

    .message-text li {
        margin-bottom: 7px;
    }

    .message-text code {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 2px 6px;
        color: #0f172a;
        font-size: .92em;
        direction: ltr;
        unicode-bidi: isolate;
    }

    .markdown-body {
        unicode-bidi: plaintext;
    }

    .markdown-body > :first-child {
        margin-top: 0;
    }

    .markdown-body > :last-child {
        margin-bottom: 0;
    }

    .markdown-body p {
        margin: 0 0 12px;
        line-height: 1.88;
    }

    .markdown-body strong {
        font-weight: 900;
        color: #0f172a;
    }

    .markdown-body em {
        font-style: italic;
    }

    .markdown-body ul,
    .markdown-body ol {
        margin: 8px 0 14px;
        padding-inline-start: 1.6rem;
    }

    .markdown-body li {
        margin-bottom: 7px;
        unicode-bidi: plaintext;
    }

    .markdown-body li > p {
        margin-bottom: 6px;
    }

    .markdown-body h1,
    .markdown-body h2,
    .markdown-body h3,
    .markdown-body h4 {
        color: #0f172a;
        font-weight: 900;
        line-height: 1.35;
        margin: 16px 0 9px;
    }

    .markdown-body h1 { font-size: 1.35rem; }
    .markdown-body h2 { font-size: 1.22rem; }
    .markdown-body h3 { font-size: 1.10rem; }
    .markdown-body h4 { font-size: 1.02rem; }

    .markdown-body blockquote {
        margin: 12px 0;
        padding: 8px 14px;
        border-inline-start: 4px solid rgba(37, 99, 235, .35);
        background: #f8fafc;
        border-radius: 10px;
        color: #334155;
    }

    .markdown-body pre {
        margin: 12px 0;
        padding: 13px 14px;
        overflow-x: auto;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        background: #0f172a;
        direction: ltr;
        text-align: left;
        unicode-bidi: isolate;
    }

    .markdown-body pre code {
        border: 0;
        padding: 0;
        background: transparent;
        color: #e2e8f0;
        white-space: pre;
    }

    .markdown-body a {
        color: #2563eb;
        text-decoration: underline;
        text-underline-offset: 2px;
        overflow-wrap: anywhere;
    }

    .answer-rtl {
        direction: rtl;
        text-align: right;
        font-family: "Noto Naskh Arabic", "Geeza Pro", "Arial", sans-serif;
    }

    .answer-ltr {
        direction: ltr;
        text-align: left;
    }

    .thinking-card {
        border: 1px solid rgba(37, 99, 235, .16);
        background: linear-gradient(135deg, rgba(239,246,255,.98), rgba(240,253,250,.96));
        border-radius: 20px;
        padding: 15px 17px;
        display: flex;
        align-items: center;
        gap: 13px;
        box-shadow: 0 14px 35px rgba(15,23,42,.06);
        margin: 6px 0 14px;
    }

    .thinking-spinner {
        width: 23px;
        height: 23px;
        border: 3px solid rgba(37, 99, 235, .16);
        border-top-color: #2563eb;
        border-radius: 999px;
        animation: ragSpin .8s linear infinite;
        flex: 0 0 auto;
    }

    .thinking-title {
        font-weight: 900;
        color: #0f172a;
        font-size: 14px;
    }

    .thinking-subtitle {
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
    }

    .source-card {
        border: 1px solid rgba(226,232,240,.95);
        border-radius: 16px;
        padding: 12px 14px;
        background: #fff;
        margin-bottom: 8px;
    }

    @keyframes ragSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @media (max-width: 900px) {
        .suggestion-grid {
            grid-template-columns: 1fr;
        }
        .message-row,
        .message-row.user {
            grid-template-columns: 40px minmax(0, 1fr);
        }
        .message-row.user .avatar-box {
            grid-column: 1;
            grid-row: 1;
        }
        .message-row.user .message-card {
            grid-column: 2;
            grid-row: 1;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


ASSISTANT_AVATAR = """
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 3.2c1.2 2.9 3.2 5 6.1 6.2-2.9 1.2-4.9 3.3-6.1 6.2-1.2-2.9-3.2-5-6.1-6.2 2.9-1.2 4.9-3.3 6.1-6.2Z" stroke="white" stroke-width="1.8" stroke-linejoin="round"/>
  <path d="M18.5 14.8c.5 1.2 1.3 2.1 2.5 2.6-1.2.5-2 1.4-2.5 2.6-.5-1.2-1.3-2.1-2.5-2.6 1.2-.5 2-1.4 2.5-2.6Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
</svg>
"""

USER_AVATAR = """
<svg width="23" height="23" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 12.1a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" stroke="white" stroke-width="1.8"/>
  <path d="M4.6 20.2c.9-3.5 3.5-5.5 7.4-5.5s6.5 2 7.4 5.5" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
</svg>
"""


def _has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


_MARKDOWN_RENDERER = MarkdownIt(
    "commonmark",
    {
        "html": False,
        "linkify": False,
        "typographer": False,
    },
)


def _text_to_html(text: str) -> str:
    clean_text = (text or "").strip()

    if not clean_text:
        return ""

    direction_class = (
        "answer-rtl"
        if _has_arabic(clean_text)
        else "answer-ltr"
    )

    rendered = _MARKDOWN_RENDERER.render(
        clean_text
    )

    return (
        f"<div class='{direction_class} markdown-body' dir='auto'>"
        f"{rendered}"
        "</div>"
    )


def _message_html(role: str, content: str) -> str:
    is_user = role == "user"
    row_class = "message-row user" if is_user else "message-row assistant"
    avatar_class = "avatar-box avatar-user" if is_user else "avatar-box avatar-assistant"
    avatar = USER_AVATAR if is_user else ASSISTANT_AVATAR
    label = "You" if is_user else "AI Assistant"
    text_html = _text_to_html(content)

    if is_user:
        return f"""
        <div class="{row_class}">
          <div class="message-card">
            <div class="message-label">{label}</div>
            <div class="message-text" dir="auto">{text_html}</div>
          </div>
          <div class="{avatar_class}">{avatar}</div>
        </div>
        """

    return f"""
    <div class="{row_class}">
      <div class="{avatar_class}">{avatar}</div>
      <div class="message-card">
        <div class="message-label">{label}</div>
        <div class="message-text" dir="auto">{text_html}</div>
      </div>
    </div>
    """


def render_message(role: str, content: str) -> None:
    st.markdown(
        _message_html(role, content),
        unsafe_allow_html=True,
    )


hero(
    "AI assistant",
    "Ask questions grounded in the indexed knowledge base. The assistant no longer reads operational database records directly.",
    "Knowledge assistant",
)

st.markdown(
    """
    <div class="ai-rag-banner">
      <div class="ai-rag-banner-title">Knowledge-based support</div>
      <p class="ai-rag-banner-text">
        This assistant searches the approved RAG documents through Chroma, reranks evidence with a local cross-encoder,
        then prepares an answer from the retrieved context. It does not generate SQL and does not access patient,
        doctor, or admin operational tables.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

suggestions = [
    "ما المقصود بنتيجة عالية الخطورة؟",
    "كيف يعمل فحص الجلوكوما في النظام؟",
    "كيف أقرأ التقرير الطبي؟",
    "What does glaucoma screening mean?",
    "ما الفرق بين screening والتشخيص النهائي؟",
    "كيف يستخدم المساعد مصادر المعرفة المعتمدة؟",
]

section("Suggested questions")
cols = st.columns(3)
for i, prompt_text in enumerate(suggestions):
    if cols[i % 3].button(prompt_text, key=f"suggest_{i}", use_container_width=True):
        st.session_state["pending_prompt"] = prompt_text

st.markdown('<div class="assistant-input-card">', unsafe_allow_html=True)
with st.form("assistant_question_form", clear_on_submit=True):
    user_input = st.text_area(
        "Ask the assistant",
        placeholder="اكتب سؤالك هنا... / Write your question here...",
        height=88,
        key="assistant_stable_input",
    )
    submit = st.form_submit_button("Ask AI Assistant", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Clear conversation", key="clear_ai_conversation"):
    st.session_state.chat_history = []
    st.rerun()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

prompt = st.session_state.pop("pending_prompt", None) if "pending_prompt" in st.session_state else None
if submit and user_input.strip():
    prompt = user_input.strip()

st.markdown('<div class="chat-stream">', unsafe_allow_html=True)

for message in st.session_state.chat_history:
    render_message(message["role"], message["content"])

if prompt:
    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )
    render_message(
        "user",
        prompt,
    )

    thinking = st.empty()
    thinking.markdown(
        """
        <div class="thinking-card">
          <div class="thinking-spinner"></div>
          <div>
            <div class="thinking-title">Preparing...</div>
            <div class="thinking-subtitle">
              Reviewing approved reference material.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    assistant_slot = st.empty()

    try:
        start = time.time()
        answer_parts: list[str] = []
        final_meta: dict = {}
        last_render = 0.0
        stream_error: str | None = None

        for event in api_post_stream(
            "/assistant/chat/stream",
            {
                "message":
                    prompt,
            },
        ):
            event_type = event.get(
                "type"
            )

            if event_type == "status":
                stage = event.get(
                    "stage"
                )

                if stage == "generation":
                    status_text = (
                        "Preparing the answer..."
                    )
                else:
                    status_text = (
                        "Reviewing approved "
                        "reference material..."
                    )

                thinking.markdown(
                    f"""
                    <div class="thinking-card">
                      <div class="thinking-spinner"></div>
                      <div>
                        <div class="thinking-title">Working...</div>
                        <div class="thinking-subtitle">
                          {html.escape(status_text)}
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif event_type == "delta":
                text_delta = str(
                    event.get(
                        "text",
                        "",
                    )
                )

                if not text_delta:
                    continue

                answer_parts.append(
                    text_delta
                )

                thinking.empty()

                now = time.monotonic()

                if (
                    now - last_render
                    >= 0.05
                ):
                    assistant_slot.markdown(
                        _message_html(
                            "assistant",
                            "".join(
                                answer_parts
                            ),
                        ),
                        unsafe_allow_html=True,
                    )
                    last_render = now

            elif event_type == "error":
                stream_error = str(
                    event.get(
                        "message",
                        (
                            "The answer stream "
                            "was interrupted."
                        ),
                    )
                )

            elif event_type == "done":
                final_meta = event

        thinking.empty()

        answer = "".join(
            answer_parts
        ).strip()

        if answer:
            assistant_slot.markdown(
                _message_html(
                    "assistant",
                    answer,
                ),
                unsafe_allow_html=True,
            )

        elapsed = (
            time.time()
            - start
        )

        mode = final_meta.get(
            "mode",
            "unknown",
        )

        st.caption(
            f"Mode: {mode} "
            f"· Response time: "
            f"{elapsed:.1f}s"
        )

        sources = (
            final_meta.get(
                "sources"
            )
            or []
        )

        if sources:
            with st.expander(
                "Reference sources"
            ):
                for source in sources:
                    st.markdown(
                        f"""
                        <div class="source-card">
                          <strong>{html.escape(str(source.get('title', 'Source')))}</strong><br>
                          <span>Mode: <code>{html.escape(str(source.get('retrieval_mode', '—')))}</code></span><br>
                          <span>Score: <code>{html.escape(str(source.get('score', '—')))}</code></span>
                          {f"<br><span>Rerank: <code>{html.escape(str(source.get('rerank_score')))}</code></span>" if source.get('rerank_score') is not None else ""}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        if final_meta.get(
            "policy_note"
        ):
            st.info(
                final_meta[
                    "policy_note"
                ]
            )

        if stream_error:
            st.warning(
                stream_error
            )

        if answer:
            st.session_state.chat_history.append(
                {
                    "role":
                        "assistant",
                    "content":
                        answer,
                }
            )
        elif stream_error:
            st.session_state.chat_history.append(
                {
                    "role":
                        "assistant",
                    "content":
                        stream_error,
                }
            )
        else:
            fallback_error = (
                "The assistant did not return "
                "an answer."
            )
            st.error(
                fallback_error
            )
            st.session_state.chat_history.append(
                {
                    "role":
                        "assistant",
                    "content":
                        fallback_error,
                }
            )

    except Exception as exc:
        thinking.empty()

        error_msg = (
            "Assistant request failed: "
            f"{exc}"
        )

        st.error(
            error_msg
        )

        st.session_state.chat_history.append(
            {
                "role":
                    "assistant",
                "content":
                    error_msg,
            }
        )

st.markdown("</div>", unsafe_allow_html=True)
