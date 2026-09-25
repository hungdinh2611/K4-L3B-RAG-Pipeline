"""Streamlit demo for the university document RAG pipeline."""

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Hỏi đáp tài liệu đại học",
    page_icon="🎓",
    layout="wide",
)


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Nguồn tham khảo ({len(sources)})"):
        for index, item in enumerate(sources, start=1):
            metadata = item["metadata"]
            st.markdown(
                f"**{index}. {metadata['title']}** — `{metadata['source']}`  \n"
                f"ID: `{item['id']}` · Phương pháp: {item['retrieval_method']} "
                f"· Điểm: {item['score']:.4f}"
            )
            if metadata.get("url"):
                st.link_button("Mở tài liệu", metadata["url"])
            st.caption(item["content"][:700])


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("Hỏi đáp tài liệu đại học")
    st.caption("Quy định đào tạo, học phí, học bổng và thông báo liên quan.")
    top_k = st.slider("Số chunks", 3, 10, 5)
    st.info("Câu trả lời luôn kèm ID nguồn để bạn kiểm tra lại tài liệu.")

st.title("Hỏi đáp tài liệu đại học")
st.caption("Hỏi bằng tiếng Việt về các tài liệu đã được lập chỉ mục.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm trong tài liệu..."):
            result = generate_with_citation(query, top_k=top_k)
        answer = result["answer"]
        sources = result["sources"]
        st.markdown(answer)
        render_sources(sources)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
