from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import Iterable, List


TITLE_MAX_LEN = 28
SUBTITLE_MAX_LEN = 36
SENTENCE_MAX_LEN = 60


@dataclass
class Block:
    """A content block suitable for WeChat article layout."""

    kind: str
    text: str


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    raw = re.split(r"(?<=[。！？!?；;])", text)
    parts = [seg.strip() for seg in raw if seg.strip()]
    return parts


def wrap_for_readability(text: str, max_len: int = SENTENCE_MAX_LEN) -> str:
    if len(text) <= max_len:
        return text

    output: list[str] = []
    buf = ""
    for seg in split_sentences(text):
        if len(buf) + len(seg) <= max_len:
            buf += seg
            continue
        if buf:
            output.append(buf)
        if len(seg) <= max_len:
            buf = seg
        else:
            # Force wrap very long sentence.
            for i in range(0, len(seg), max_len):
                chunk = seg[i : i + max_len]
                if len(chunk) == max_len and i + max_len < len(seg):
                    output.append(chunk)
                else:
                    buf = chunk
    if buf:
        output.append(buf)
    return "\n".join(output)


def classify_line(line: str, index: int) -> str:
    stripped = line.strip()

    if index == 0 or (len(stripped) <= TITLE_MAX_LEN and "。" not in stripped):
        return "title"

    if stripped.startswith(("一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、")):
        return "subtitle"

    if len(stripped) <= SUBTITLE_MAX_LEN and stripped.endswith(("：", ":")):
        return "subtitle"

    if stripped.startswith(("-", "•", "1.", "2.", "3.")):
        return "bullet"

    return "paragraph"


def format_to_blocks(lines: Iterable[str]) -> List[Block]:
    blocks: list[Block] = []

    cleaned = [normalize_text(line) for line in lines if normalize_text(line)]
    for idx, line in enumerate(cleaned):
        kind = classify_line(line, idx)
        if kind == "paragraph":
            line = wrap_for_readability(line)
        blocks.append(Block(kind=kind, text=line))

    return blocks


def blocks_to_markdown(blocks: Iterable[Block]) -> str:
    lines: list[str] = []
    for block in blocks:
        if block.kind == "title":
            lines.append(f"# {block.text}")
            lines.append("")
        elif block.kind == "subtitle":
            lines.append(f"## {block.text.rstrip('：:')}")
            lines.append("")
        elif block.kind == "bullet":
            stripped = block.text.lstrip("-• ").strip()
            lines.append(f"- {stripped}")
        else:
            para = block.text.replace("\n", "\n\n")
            lines.append(para)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def blocks_to_html(blocks: Iterable[Block]) -> str:
    """Export blocks as a standalone, WeChat-friendly HTML article."""
    body_parts: list[str] = []
    for block in blocks:
        text = escape(block.text.strip())
        if not text:
            continue

        if block.kind == "title":
            body_parts.append(f"<h1>{text}</h1>")
        elif block.kind == "subtitle":
            body_parts.append(f"<h2>{text.rstrip('：:')}</h2>")
        elif block.kind == "bullet":
            item = re.sub(r"^[-•\s]+", "", text)
            body_parts.append(f"<p class=\"bullet\">• {item}</p>")
        else:
            paragraph = "<br><br>".join(text.split("\n"))
            body_parts.append(f"<p>{paragraph}</p>")

    body_html = "\n    ".join(body_parts)
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>公众号文章导出</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7fb;
      font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, \"PingFang SC\", \"Microsoft YaHei\", sans-serif;
      color: #1f2937;
      line-height: 1.9;
    }}
    .article {{
      max-width: 760px;
      margin: 28px auto;
      background: #fff;
      padding: 24px;
      border-radius: 12px;
      border: 1px solid #e5e7eb;
    }}
    h1 {{ font-size: 1.8rem; margin: 0 0 18px; line-height: 1.4; }}
    h2 {{ font-size: 1.25rem; margin: 26px 0 12px; color: #111827; }}
    p {{ margin: 0 0 14px; font-size: 1.05rem; }}
    .bullet {{ padding-left: 4px; }}
  </style>
</head>
<body>
  <article class=\"article\">
    {body_html}
  </article>
</body>
</html>
"""
