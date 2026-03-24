from __future__ import annotations

import io
from dataclasses import asdict

from docx import Document
from flask import Flask, jsonify, render_template, request, send_file

from formatter import Block, blocks_to_html, blocks_to_markdown, format_to_blocks

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


def parse_docx(file_stream) -> list[str]:
    doc = Document(file_stream)
    lines: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines


def load_blocks_from_payload(payload: dict) -> list[Block]:
    raw_blocks = payload.get("blocks", [])
    blocks: list[Block] = []
    for item in raw_blocks:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        kind = str(item.get("kind", "paragraph"))
        blocks.append(Block(kind=kind, text=text))
    return blocks


@app.post("/api/format")
def format_docx():
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "请先上传 .docx 文件"}), 400

    if not uploaded.filename.lower().endswith(".docx"):
        return jsonify({"error": "仅支持 .docx 文件"}), 400

    try:
        source_lines = parse_docx(uploaded)
        blocks = [asdict(b) for b in format_to_blocks(source_lines)]
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"文档解析失败：{exc}"}), 400

    return jsonify({"count": len(source_lines), "blocks": blocks})


@app.post("/api/export")
def export_markdown():
    payload = request.get_json(silent=True) or {}
    markdown_text = blocks_to_markdown(load_blocks_from_payload(payload))

    return send_file(
        io.BytesIO(markdown_text.encode("utf-8")),
        as_attachment=True,
        download_name="wechat_article.md",
        mimetype="text/markdown",
    )


@app.post("/api/export_html")
def export_html():
    payload = request.get_json(silent=True) or {}
    html_text = blocks_to_html(load_blocks_from_payload(payload))

    return send_file(
        io.BytesIO(html_text.encode("utf-8")),
        as_attachment=True,
        download_name="wechat_article.html",
        mimetype="text/html",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
