from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="AI 大模型科技树图谱", page_icon="🧠", layout="wide")

st.title("🧠 AI 大模型科技树图谱（论文实时填充版）")
st.caption("科技树每个分支都填入真实 arXiv 最新论文，支持下钻查看和分支追踪。")


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


def shorten(text: str, max_len: int = 40) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= max_len else clean[: max_len - 1] + "…"


def parse_arxiv_entry(entry: ET.Element, ns: dict[str, str]) -> dict[str, Any]:
    title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
    summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip().replace("\n", " ")
    published = (entry.findtext("atom:published", default="", namespaces=ns) or "")

    authors = [
        (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
        for a in entry.findall("atom:author", ns)
    ]
    authors = [name for name in authors if name]

    link = ""
    for link_el in entry.findall("atom:link", ns):
        href = link_el.attrib.get("href")
        rel = link_el.attrib.get("rel", "")
        if href and rel == "alternate":
            link = href
            break

    return {
        "title": title,
        "summary": summary,
        "published": published,
        "authors": authors,
        "link": link,
    }


@st.cache_data(ttl=1200, show_spinner=False)
def fetch_latest_arxiv(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    encoded_query = quote_plus(query)
    url = (
        "https://export.arxiv.org/api/query"
        f"?search_query=all:{encoded_query}&sortBy=submittedDate&sortOrder=descending&start=0&max_results={max_results}"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    return [parse_arxiv_entry(entry, ns) for entry in root.findall("atom:entry", ns)]


@st.cache_data(ttl=1200, show_spinner=True)
def fetch_all_branch_snapshots(branches: list[Branch], per_branch: int) -> dict[str, list[dict[str, Any]]]:
    snapshots: dict[str, list[dict[str, Any]]] = {}
    for b in branches:
        key = f"{b.domain} / {b.subdomain}"
        snapshots[key] = fetch_latest_arxiv(b.query, max_results=per_branch)
    return snapshots


def build_tree_df(branches: list[Branch], snapshots: dict[str, list[dict[str, Any]]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = [{"id": "AI 大模型", "parent": "", "value": 0, "paper_hint": ""}]
    domains = sorted({b.domain for b in branches})

    for domain in domains:
        domain_count = sum(len(snapshots.get(f"{b.domain} / {b.subdomain}", [])) for b in branches if b.domain == domain)
        rows.append(
            {
                "id": domain,
                "parent": "AI 大模型",
                "value": max(domain_count, 1),
                "paper_hint": f"分支论文数：{domain_count}",
            }
        )

    for b in branches:
        key = f"{b.domain} / {b.subdomain}"
        papers = snapshots.get(key, [])
        latest_title = papers[0]["title"] if papers else "暂无论文"
        preview = "<br>".join([f"• {shorten(p['title'], 55)}" for p in papers[:3]]) or "暂无数据"

        rows.append(
            {
                "id": f"{b.subdomain}<br><span style='font-size:11px'>🆕 {shorten(latest_title, 30)}</span>",
                "parent": b.domain,
                "value": max(len(papers), 1),
                "paper_hint": preview,
            }
        )

    return pd.DataFrame(rows)


def render_tree(branches: list[Branch], snapshots: dict[str, list[dict[str, Any]]]) -> None:
    tree_df = build_tree_df(branches, snapshots)
    fig = px.treemap(
        tree_df,
        names="id",
        parents="parent",
        values="value",
        color="parent",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        custom_data=["paper_hint"],
    )
    fig.update_traces(
        root_color="#EAF2FF",
        textinfo="label",
        hovertemplate="<b>%{label}</b><br><br>%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=650)
    st.plotly_chart(fig, use_container_width=True)


def format_date(ts: str) -> str:
    if not ts:
        return "未知"
    return ts.replace("T", " ").replace("Z", " UTC")


def flatten_latest(snapshots: dict[str, list[dict[str, Any]]]) -> pd.DataFrame:
    records: list[dict[str, str]] = []
    for branch_name, papers in snapshots.items():
        for p in papers:
            records.append(
                {
                    "branch": branch_name,
                    "published": p.get("published", ""),
                    "title": p.get("title", ""),
                    "link": p.get("link", ""),
                }
            )
    if not records:
        return pd.DataFrame(columns=["branch", "published", "title", "link"])

    df = pd.DataFrame(records)
    return df.sort_values("published", ascending=False).head(20)


with st.sidebar:
    st.header("⚙️ 图谱参数")
    per_branch_count = st.slider("每个分支拉取论文数", min_value=2, max_value=8, value=4, step=1)
    if st.button("🔄 强制全量刷新"):
        fetch_latest_arxiv.clear()
        fetch_all_branch_snapshots.clear()
    st.caption("默认每 20 分钟自动刷新缓存。")

try:
    snapshots = fetch_all_branch_snapshots(BRANCHES, per_branch=per_branch_count)
except requests.RequestException as exc:
    st.error(f"加载科技树数据失败：{exc}")
    st.stop()

left, right = st.columns([1.4, 1], gap="large")

with left:
    st.subheader("科技树总览（每个节点显示真实最新论文）")
    render_tree(BRANCHES, snapshots)
    st.info("提示：点击矩形下钻，悬浮可看该分支 Top3 最新论文标题。")

with right:
    st.subheader("分支详情")
    branch_options = {f"{b.domain} / {b.subdomain}": b for b in BRANCHES}
    selected_label = st.selectbox("选择分支", options=list(branch_options.keys()), index=0)
    selected_branch = branch_options[selected_label]
    selected_papers = snapshots.get(selected_label, [])

    st.markdown(f"**分支说明：** {selected_branch.description}")
    st.markdown(f"**检索关键词：** `{selected_branch.query}`")
    st.caption(f"数据源：arXiv API ｜ 最近刷新：{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    if not selected_papers:
        st.warning("当前分支暂无论文结果，请调整关键词。")
    else:
        for i, p in enumerate(selected_papers, start=1):
            with st.expander(f"{i}. {p['title']}", expanded=(i <= 2)):
                st.write(f"**发布时间：** {format_date(p['published'])}")
                if p["authors"]:
                    st.write(f"**作者：** {', '.join(p['authors'][:6])}")
                st.write(p["summary"][:1000] + ("..." if len(p["summary"]) > 1000 else ""))
                if p["link"]:
                    st.link_button("查看 arXiv 原文", p["link"])

st.divider()
st.subheader("🌍 全局最新发现（跨分支）")
latest_df = flatten_latest(snapshots)
if latest_df.empty:
    st.info("暂无可展示论文。")
else:
    latest_df["published"] = latest_df["published"].apply(format_date)
    st.dataframe(
        latest_df[["published", "branch", "title", "link"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "published": "发布时间",
            "branch": "分支",
            "title": "论文标题",
            "link": st.column_config.LinkColumn("链接", display_text="打开"),
        },
    )
