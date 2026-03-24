from __future__ import annotations

import re
from dataclasses import dataclass
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
