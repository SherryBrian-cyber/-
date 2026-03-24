# 公众号排版校对助手（HTML 界面版）

这是一个可本地运行的 HTML Web 应用：上传 `.docx` 后自动排版为公众号易读格式，并支持逐段手动删减、修改与新增，最后导出 Markdown。

## 功能

- 上传 Word（`.docx`）自动解析。
- 自动识别标题 / 小标题 / 正文 / 列表。
- 自动拆分过长正文，提升公众号手机端阅读体验。
- 可视化编辑界面，支持逐段手动修改和删除。
- 支持新增空段落。
- 一键导出 Markdown。
- 一键导出可直接打开的 HTML。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

启动后访问：`http://localhost:5000`

## 生成可直接访问的公网链接（临时）

如果你希望别人直接通过链接访问（无需在对方电脑安装环境），可使用脚本自动生成临时公网地址：

```bash
bash scripts/share_localhost_run.sh
```

运行后终端会输出一个 `https://xxxx.localhost.run` 的地址，直接发给他人即可访问。

> 注意：这是临时隧道链接，关闭终端或中断脚本后链接会失效。

## 使用流程

1. 上传 Word 文档（`.docx`）。
2. 点击“开始排版”，系统自动生成段落块。
3. 在页面中逐段修改类型与内容，删除不需要的段落，或新增空段落。
4. 点击“导出 Markdown”或“导出 HTML”下载结果。

## 项目结构

- `app.py`：Flask 后端与 API。
- `formatter.py`：排版规则与 Markdown 输出。
- `templates/index.html`：前端页面结构与交互逻辑。
- `static/style.css`：页面样式。
- `scripts/share_localhost_run.sh`：生成临时公网访问链接。

## 说明

- 仅支持 `.docx`（不支持 `.doc`）。
- 自动分类采用启发式规则，建议人工复核后再发布。
