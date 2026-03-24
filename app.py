from __future__ import annotations

import io
from dataclasses import asdict

import streamlit as st
from docx import Document

from formatter import Block, blocks_to_markdown, format_to_blocks


st.set_page_config(page_title="公众号排版校对助手", page_icon="📝", layout="wide")

st.title("📝 公众号排版校对助手")
st.caption("上传 Word 文档，自动排版成公众号易读格式，并支持逐段手动修改、删减与导出。")


def parse_docx(uploaded_file) -> list[str]:
    doc = Document(uploaded_file)
    lines: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines


def init_session():
    if "blocks" not in st.session_state:
        st.session_state.blocks = []


init_session()

left, right = st.columns([1, 2])

with left:
    uploaded = st.file_uploader("上传 Word 文件（.docx）", type=["docx"])

    if uploaded is not None:
        try:
            source_lines = parse_docx(uploaded)
            st.session_state.blocks = [asdict(b) for b in format_to_blocks(source_lines)]
            st.success(f"已解析 {len(source_lines)} 段文本，完成自动排版。")
        except Exception as exc:  # noqa: BLE001
            st.error(f"文档解析失败：{exc}")

    st.divider()
    st.subheader("全局排版参数")
    st.write("可继续在右侧逐段调整。")

    if st.button("清空当前内容"):
        st.session_state.blocks = []
        st.info("已清空。")

with right:
    st.subheader("手动校对与编辑")

    blocks: list[dict] = st.session_state.blocks

    if not blocks:
        st.info("请先在左侧上传 Word 文档。")
    else:
        remove_indexes: list[int] = []

        for idx, block in enumerate(blocks):
            with st.container(border=True):
                top1, top2, top3 = st.columns([2, 6, 2])
                with top1:
                    kind = st.selectbox(
                        f"段落类型 #{idx+1}",
                        ["title", "subtitle", "paragraph", "bullet"],
                        index=["title", "subtitle", "paragraph", "bullet"].index(block["kind"]),
                        key=f"kind_{idx}",
                    )
                with top2:
                    text = st.text_area(
                        f"内容 #{idx+1}",
                        value=block["text"],
                        height=120,
                        key=f"text_{idx}",
                    )
                with top3:
                    if st.button("删除", key=f"del_{idx}"):
                        remove_indexes.append(idx)

                block["kind"] = kind
                block["text"] = text.strip()

        if remove_indexes:
            st.session_state.blocks = [
                b for i, b in enumerate(st.session_state.blocks) if i not in set(remove_indexes)
            ]
            st.rerun()

        st.divider()
        col_add, col_export = st.columns([1, 1])
        with col_add:
            if st.button("新增空段落"):
                st.session_state.blocks.append(asdict(Block(kind="paragraph", text="")))
                st.rerun()

        with col_export:
            markdown_text = blocks_to_markdown(
                [Block(kind=b["kind"], text=b["text"]) for b in st.session_state.blocks if b["text"].strip()]
            )
            st.download_button(
                "导出 Markdown",
                data=io.BytesIO(markdown_text.encode("utf-8")),
                file_name="wechat_article.md",
                mime="text/markdown",
            )

        st.subheader("预览（Markdown）")
        st.code(markdown_text, language="markdown")
