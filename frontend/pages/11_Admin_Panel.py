# Ensure project root is importable when Streamlit executes pages directly.
from pathlib import Path
import sys

_PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "backend").exists() and (p / "frontend").exists()
)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

from frontend.app_utils.auth import require_role
from frontend.app_utils.api import api_delete, api_get, api_patch, api_post
from frontend.app_utils.ui import hero, section, setup_page, stat_card, status_badge

setup_page("Admin Panel", "shield")
require_role("admin")
hero("Admin panel", "Manage doctor approvals, system metrics, appointment oversight, and RAG knowledge base content.", "System administration")

metrics = api_get("/admin/metrics")
cols = st.columns(6)
for col, (k, v) in zip(cols, metrics.items()):
    with col:
        stat_card(k.replace("_", " ").title(), v)

st.markdown("<div class='admin-metrics-spacer'></div>", unsafe_allow_html=True)

tabs = st.tabs(["Doctor approvals", "Users", "Appointments", "RAG knowledge base"])

with tabs[0]:
    doctors = api_get("/admin/doctor-applications")
    section("Doctor applications")
    for d in doctors:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"### {d['full_name']}")
            c1.write(d.get("bio") or "")
            c2.write(f"**Specialization:** {d.get('specialization')}")
            c2.write(f"**Location:** {d.get('clinic_location') or '—'}")
            c2.write(f"**Experience:** {d.get('experience_years') or 0} years")
            with c3:
                status_badge(d.get("status"))
                statuses = ["pending", "approved", "rejected", "suspended"]
                current_status = d.get("status") if d.get("status") in statuses else "pending"
                new_status = st.selectbox("Set status", statuses, index=statuses.index(current_status), key=f"status_{d['id']}")
                if st.button("Update", key=f"update_{d['id']}"):
                    try:
                        api_patch(f"/admin/doctors/{d['id']}/status", {"status": new_status})
                        st.success("Status updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

with tabs[1]:
    section("Users")
    users = api_get("/admin/users")
    st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)

with tabs[2]:
    section("Appointments")
    appointments = api_get("/admin/appointments")
    st.dataframe(pd.DataFrame(appointments), use_container_width=True, hide_index=True)

with tabs[3]:
    st.markdown(
        """
        <style>
        .rag-admin-hero {
            border: 1px solid rgba(37,99,235,.14);
            background: linear-gradient(135deg, #eff6ff, #ffffff 55%, #f0fdfa);
            border-radius: 28px;
            padding: 24px;
            box-shadow: 0 20px 50px rgba(15,23,42,.08);
            margin-bottom: 18px;
        }
        .rag-admin-hero h2 {
            margin: 0 0 8px;
            font-size: 28px;
            font-weight: 900;
            color: #0f172a;
        }
        .rag-admin-hero p {
            margin: 0;
            color: #475569;
            line-height: 1.7;
            max-width: 900px;
        }
        .rag-doc-card {
            border: 1px solid rgba(226,232,240,.95);
            background: rgba(255,255,255,.92);
            border-radius: 22px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 12px 30px rgba(15,23,42,.055);
        }
        .rag-doc-card h3 {
            margin: 0 0 6px;
            font-size: 19px;
            font-weight: 900;
            color: #0f172a;
        }
        .rag-meta {
            color: #64748b;
            font-size: 13px;
            line-height: 1.55;
        }
        .rag-status-pill {
            display: inline-flex;
            padding: 6px 10px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 12px;
            border: 1px solid rgba(148,163,184,.22);
            background: #f8fafc;
        }
        .rag-status-active { color: #047857; background: #ecfdf5; }
        .rag-status-inactive { color: #b45309; background: #fffbeb; }
        </style>
        <div class="rag-admin-hero">
            <h2>RAG knowledge and vector database</h2>
            <p>
                Upload, clean, index, preview, disable, delete, and rebuild the local Chroma vector database.
                PDF files go through OCR, DOCX/TXT/MD are extracted directly, then all content is cleaned and embedded.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    upload_tab, manual_tab, manage_tab, vector_tab = st.tabs(
        ["Upload & index", "Manual document", "Manage documents", "Vector DB status"]
    )

    with upload_tab:
        left, right = st.columns([1.2, .8])

        with left:
            st.markdown("### Upload knowledge file")
            uploaded = st.file_uploader(
                "PDF, DOCX, TXT, MD, or Markdown",
                type=["pdf", "docx", "txt", "md", "markdown"],
                key="rag_file_upload",
            )
            upload_title = st.text_input("Optional title", key="rag_upload_title")

            if st.button("Extract, upload, and rebuild Chroma", key="upload_extract_index_rag", use_container_width=True):
                if not uploaded:
                    st.warning("Please choose a file first.")
                else:
                    try:
                        with st.spinner("Extracting and cleaning document text..."):
                            files = {
                                "file": (
                                    uploaded.name,
                                    uploaded.getvalue(),
                                    uploaded.type or "application/octet-stream",
                                )
                            }
                            data = {"title": upload_title} if upload_title else {}
                            result = api_post("/admin/rag-documents/upload", files=files, data=data)

                        meta = result.get("upload_metadata", {}) or {}
                        st.success("Document extracted and stored successfully.")

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Document ID", result.get("id", "—"))
                        c2.metric("Provider", meta.get("provider", "—"))
                        c3.metric("OCR", "Yes" if meta.get("ocr_forced") else "No")

                        prep = meta.get("preprocessing") or {}
                        if prep:
                            st.info(
                                f"Text preprocessing completed: "
                                f"{prep.get('original_length', '—')} → {prep.get('cleaned_length', '—')} characters."
                            )

                        with st.spinner("Rebuilding Chroma vector database..."):
                            index_result = api_post("/admin/vector-store/rebuild", {})

                        st.success(
                            f"Chroma rebuilt: {index_result.get('documents', '—')} documents, "
                            f"{index_result.get('chunks', '—')} chunks."
                        )
                        st.json(index_result)
                        st.rerun()

                    except Exception as exc:
                        st.error(str(exc))

        with right:
            st.markdown("### Processing pipeline")
            st.info(
                "File → OCR/extraction → NLP cleaning → chunking → multilingual embeddings → Chroma → cross-encoder reranking."
            )
            st.caption("The assistant only uses active documents. Disabled or deleted documents are excluded from retrieval.")

    with manual_tab:
        st.markdown("### Add manual knowledge")
        with st.form("rag_doc"):
            title = st.text_input("Title")
            content = st.text_area("Content", height=260)
            submitted = st.form_submit_button("Add and rebuild Chroma", use_container_width=True)

        if submitted:
            try:
                with st.spinner("Saving document..."):
                    api_post("/admin/rag-documents", {"title": title, "content": content})
                with st.spinner("Rebuilding Chroma vector database..."):
                    result = api_post("/admin/vector-store/rebuild", {})
                st.success(f"Document added and indexed. Chroma now has {result.get('chunks', '—')} chunks.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with manage_tab:
        st.markdown("### Manage active knowledge")
        docs = api_get("/admin/rag-documents")

        if not docs:
            st.info("No RAG documents yet.")
        else:
            st.caption(f"{len(docs)} knowledge document(s) found.")

        for doc in docs:
            doc_id = doc["id"]
            title = doc.get("title") or f"Document #{doc_id}"
            content = doc.get("content") or ""
            is_active = bool(doc.get("is_active"))

            st.markdown(
                f"""
                <div class="rag-doc-card">
                  <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                    <div>
                      <h3>{title}</h3>
                      <div class="rag-meta">ID: {doc_id} · Length: {len(content)} characters</div>
                    </div>
                    <span class="rag-status-pill {'rag-status-active' if is_active else 'rag-status-inactive'}">
                        {'Active' if is_active else 'Inactive'}
                    </span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"Preview: {title}"):
                st.write(content[:2600] + ("..." if len(content) > 2600 else ""))

            c1, c2, c3 = st.columns([1, 1, 2])

            with c1:
                if st.button("Enable / Disable", key=f"toggle_rag_{doc_id}", use_container_width=True):
                    try:
                        with st.spinner("Updating document and rebuilding Chroma..."):
                            api_patch(f"/admin/rag-documents/{doc_id}/toggle")
                            api_post("/admin/vector-store/rebuild", {})
                        st.success("Document status updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            with c2:
                confirm = st.checkbox("Confirm delete", key=f"confirm_delete_rag_{doc_id}")

            with c3:
                if st.button(
                    "Delete permanently",
                    key=f"delete_rag_{doc_id}",
                    use_container_width=True,
                    disabled=not confirm,
                ):
                    try:
                        with st.spinner("Deleting document and rebuilding Chroma..."):
                            api_delete(f"/admin/rag-documents/{doc_id}")
                            api_post("/admin/vector-store/rebuild", {})
                        st.success("Document deleted.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            st.divider()

    with vector_tab:
        st.markdown("### Chroma vector database")
        try:
            status = api_get("/admin/vector-store/status")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Backend", status.get("backend", "—"))
            c2.metric("Active docs", status.get("documents_active", "—"))
            c3.metric("Chunks", status.get("chunks", "—"))
            c4.metric("Current", "Yes" if status.get("is_current") else "No")

            st.caption(f"Collection: {status.get('collection') or '—'}")
            st.caption(f"DB directory: {status.get('db_dir') or '—'}")

            if status.get("error"):
                st.warning(status["error"])

            if st.button("Rebuild Chroma now", key="manual_rebuild_chroma", use_container_width=True):
                with st.spinner("Rebuilding Chroma vector database..."):
                    result = api_post("/admin/vector-store/rebuild", {})
                st.success("Chroma vector database rebuilt.")
                st.json(result)
                st.rerun()

        except Exception as exc:
            st.error(str(exc))

