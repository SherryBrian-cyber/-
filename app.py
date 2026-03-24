from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="AI 大模型科技树图谱", page_icon="🧠", layout="wide")

st.title("🧠 AI 大模型科技树图谱（实时更新版）")
st.caption("参考 O-DataMap 的图谱思路：左侧看科技树，右侧查看分支最新论文进展（arXiv 实时拉取）。")


@dataclass(frozen=True)
class Branch:
    domain: str
    subdomain: str
    query: str
    description: str


BRANCHES: list[Branch] = [
    Branch("基础模型", "架构与训练范式", "transformer architecture large language model training", "模型结构、扩展规律与训练策略"),
    Branch("基础模型", "对齐与安全", "alignment RLHF constitutional AI large language models", "价值对齐、安全与可控输出"),
    Branch("基础模型", "高效推理与压缩", "quantization distillation efficient inference LLM", "量化、蒸馏、KV Cache 与推理优化"),
    Branch("多模态", "视觉-语言模型", "vision language model multimodal reasoning", "图文理解、图像推理与生成"),
    Branch("多模态", "语音与音频", "speech language model audio foundation model", "语音识别、语音生成与语音理解"),
    Branch("多模态", "视频理解与生成", "video large language model video generation", "视频问答、时序理解与生成"),
    Branch("Agent", "工具调用与规划", "LLM agent tool use planning", "函数调用、任务规划、工作流编排"),
    Branch("Agent", "多智能体协作", "multi agent large language model coordination", "协作机制、通信协议和任务分解"),
    Branch("Agent", "软件工程 Agent", "code agent autonomous software engineering", "代码生成、修复、评测与自动开发"),
    Branch("RAG 与知识", "检索增强生成（RAG）", "retrieval augmented generation RAG", "检索策略、索引与生成协同"),
    Branch("RAG 与知识", "长上下文与记忆", "long context memory language model", "超长上下文处理与持久记忆"),
    Branch("RAG 与知识", "知识图谱融合", "knowledge graph large language model integration", "结构化知识增强模型能力"),
    Branch("评测与治理", "评测基准与幻觉", "LLM benchmark hallucination evaluation", "可靠性、事实性与能力评估"),
    Branch("评测与治理", "可解释性", "interpretability large language model", "神经机制解释、可视化和归因"),
    Branch("评测与治理", "隐私与合规", "privacy compliance governance foundation model", "数据合规、隐私保护与治理框架"),
    Branch("行业应用", "医疗与生命科学", "large language model healthcare biomedical", "医学问答、临床与生物医药研究"),
    Branch("行业应用", "金融与风控", "large language model finance risk", "投研、合规审查与风险管理"),
    Branch("行业应用", "教育与科研", "large language model education scientific discovery", "教学辅助、科研协同与自动化探索"),
]


@st.cache_data(ttl=900, show_spinner=False)
def fetch_latest_arxiv(query: str, max_results: int = 8) -> list[dict]:
    encoded_query = quote_plus(query)
    url = (
        "https://export.arxiv.org/api/query"
        f"?search_query=all:{encoded_query}&sortBy=submittedDate&sortOrder=descending&start=0&max_results={max_results}"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers: list[dict] = []
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip().replace("\n", " ")
        published = (entry.findtext("atom:published", default="", namespaces=ns) or "")
        link = ""
        for link_el in entry.findall("atom:link", ns):
            href = link_el.attrib.get("href")
            rel = link_el.attrib.get("rel", "")
            if href and rel == "alternate":
                link = href
                break

        papers.append(
            {
                "title": title,
                "summary": summary,
                "published": published,
                "link": link,
            }
        )

    return papers


def build_tree_df(branches: list[Branch]) -> pd.DataFrame:
    rows = [{"id": "AI 大模型", "parent": "", "value": 0}]
    domains = sorted({b.domain for b in branches})

    for domain in domains:
        rows.append({"id": domain, "parent": "AI 大模型", "value": 0})

    for branch in branches:
        rows.append(
            {
                "id": branch.subdomain,
                "parent": branch.domain,
                "value": 1,
            }
        )

    return pd.DataFrame(rows)


def render_tree(branches: list[Branch]) -> None:
    tree_df = build_tree_df(branches)
    fig = px.treemap(
        tree_df,
        names="id",
        parents="parent",
        values="value",
        color="parent",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_traces(root_color="#EAF2FF", hovertemplate="<b>%{label}</b><extra></extra>")
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        height=620,
    )
    st.plotly_chart(fig, use_container_width=True)


left, right = st.columns([1.35, 1], gap="large")

with left:
    st.subheader("科技树总览（可缩放/点击下钻）")
    render_tree(BRANCHES)
    st.info("提示：点击任意矩形可下钻到该分支；双击空白处可返回上层。")

with right:
    st.subheader("分支最新进展")

    branch_options = {f"{b.domain} / {b.subdomain}": b for b in BRANCHES}
    selected_label = st.selectbox("选择要追踪的分支", options=list(branch_options.keys()), index=0)
    selected_branch = branch_options[selected_label]

    col1, col2 = st.columns([1, 1])
    with col1:
        paper_count = st.slider("展示论文数量", min_value=3, max_value=20, value=8, step=1)
    with col2:
        if st.button("🔄 立即刷新"):
            fetch_latest_arxiv.clear()

    st.markdown(f"**分支说明：** {selected_branch.description}")
    st.markdown(f"**检索关键词：** `{selected_branch.query}`")

    try:
        papers = fetch_latest_arxiv(selected_branch.query, max_results=paper_count)
        now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        st.caption(f"数据源：arXiv API ｜ 最近刷新：{now}")

        if not papers:
            st.warning("未检索到结果，请更换分支或稍后重试。")
        else:
            for i, p in enumerate(papers, start=1):
                with st.expander(f"{i}. {p['title']}", expanded=(i == 1)):
                    published = p["published"].replace("T", " ").replace("Z", "") if p["published"] else "未知"
                    st.write(f"**发布时间：** {published}")
                    st.write(p["summary"][:800] + ("..." if len(p["summary"]) > 800 else ""))
                    if p["link"]:
                        st.link_button("查看 arXiv 原文", p["link"])
    except requests.RequestException as exc:
        st.error(f"获取最新论文失败：{exc}")
        st.caption("请检查网络连接，或稍后重试。")

st.divider()
st.markdown(
    "### 使用建议\n"
    "- 将本页面作为 AI 技术雷达：每天点击刷新，快速跟踪你关心的分支。\n"
    "- 结合团队需求新增分支关键词，可扩展成企业内部 AI 知识地图。\n"
    "- 如果你希望接入更多源（如 OpenReview、Papers with Code、Hugging Face），可在同一结构下继续扩展。"
)
