# Changelog

本文件记录 pdf2md-agent-skill 的版本变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.3.0] - 2026-07-19

首次公开发布。

### 特性

- **PDF 智能逐页分流**：文本页 PyMuPDF（段落合并 + 双栏排序 + 页眉页脚/水印过滤），公式页/扫描页 Ark 视觉 OCR（公式转 LaTeX）
- **公式密集页检测**：数学符号占比 > 1.5% 自动 OCR，40 页论文通常只 OCR 8-10 页
- **跨页连字符断词合并**
- **全格式覆盖**：docx/pptx/xlsx/html/csv/epub 等走 markitdown
- **xlsx 数字后处理**：去除 openpyxl 浮点尾零（`32.000` -> `32`），保留科学计数法不被误改
- OCR 客户端延迟创建：纯文本 PDF 无需 `ARK_API_KEY`
- OCR 单页失败重试 + 失败率告警（≥50% 返回非零退出码，避免残缺输出被误当完整结果）
- 加密 PDF / 空 PDF 友好报错
- 输出目录自动创建（支持 `-o /tmp/sub/out.md` 深层路径）
- `--version`、`--ocr`、`--no-llm`、`-m` 参数
- `ARK_BASE_URL` 支持切换 OpenAI-compatible 端点（OpenAI / Azure / 本地 vLLM 等）
