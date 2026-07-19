# Changelog

本文件记录 pdf2md-agent-skill 的版本变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.3.1] - 2026-07-19

### 修复

- 拒绝输入与输出指向同一文件或符号链接别名，防止覆盖原文档
- 统一视觉 OCR 的 API Key 契约：公式密集页、扫描页和空文本页均明确提示需要 `ARK_API_KEY`
- 移除对整份 XLSX Markdown 的全局尾零替换，避免篡改版本号、料号等文本值
- 任一 OCR 页面失败时默认返回非零退出码；新增 `--allow-partial` 显式接受残缺输出
- Skill 命令不再写死 Claude Code 与 `/tmp` 路径，并增加 CLI、Claude Code、Codex 安装说明
- 修正 Codex skill frontmatter，增加 `agents/openai.yaml` 与英文 README

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
- `ARK_BASE_URL` 支持切换兼容 Chat Completions、视觉输入和 data URL 的端点；Ark 已验证
