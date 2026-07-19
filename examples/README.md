# 示例

本目录提供 4 个典型示例，展示 skill 对不同格式的转换效果。每个示例含原始输入文件和转换后的 Markdown。

## 示例列表

| 示例 | 输入 | 输出 | 展示特性 |
|------|------|------|----------|
| docx | `sample.docx` | `sample_docx.md` | 标题层级、有序/无序列表、表格 |
| xlsx | `sample.xlsx` | `sample_xlsx.md` | 多 sheet、Markdown 表格、数字后处理 |
| pdf | `sample.pdf` | `sample_pdf.md` | PDF 智能分流、公式转 LaTeX |
| pdf（双栏） | `sample_twocol.pdf` | `sample_twocol.md` | 双栏排序、段落合并 |

## 使用方法

```bash
# 复现示例（需先安装依赖并配置 ARK_API_KEY）
cd ~/.claude/skills/pdf2md-agent-skill

# docx 示例（无需 API Key）
python3 scripts/md_convert.py examples/sample.docx -o /tmp/out_docx.md --no-llm

# xlsx 示例（无需 API Key）
python3 scripts/md_convert.py examples/sample.xlsx -o /tmp/out_xlsx.md --no-llm

# pdf 示例（需 ARK_API_KEY，公式页 OCR）
export ARK_API_KEY="your-key"
python3 scripts/md_convert.py examples/sample.pdf -o /tmp/out_pdf.md

# pdf 双栏示例（纯文本页，无需 API Key）
python3 scripts/md_convert.py examples/sample_twocol.pdf -o /tmp/out_twocol.md
```

## 示例 1：docx

`sample.docx` 含 4 级标题、段落、无序列表、有序列表、表格。转换后：
- 标题 -> Markdown `#`/`##`/`###`
- 列表 -> `-`（无序）/ `1.`（有序）
- 表格 -> Markdown 表格

查看 [`sample_docx.md`](sample_docx.md)。

## 示例 2：xlsx

`sample.xlsx` 含 2 个 sheet（"实验结果"、"超参数"）。转换后：
- 每个 sheet 用 `## Sheet名` 标注
- 数据转为 Markdown 表格
- 数字后处理：`32.000` -> `32`，`0.852` 保留

查看 [`sample_xlsx.md`](sample_xlsx.md)。

## 示例 3：pdf

`sample.pdf` 是学术论文 3 页（含数学公式定义）。转换展示智能分流：
- 文本页 -> PyMuPDF（段落合并、双栏排序）
- 公式页 -> 视觉 OCR（公式转 LaTeX，如 `\( E_i \)`、`\[ A_i \sim P_{\pi,\mathcal{T}}(\cdot | E_{i-1}, O_{i-1}) \]`）

查看 [`sample_pdf.md`](sample_pdf.md)，搜索 `Definition 1` 查看公式效果。

## 示例 4：pdf（双栏）

`sample_twocol.pdf` 是双栏学术论文 2 页（Rabinovich et al., *On the Robustness of Agentic Function Calling*，p4–p5 摘录）。转换展示双栏排序：
- 全程 PyMuPDF（文本页，0 OCR）
- 双栏检测触发 -> 先左栏后右栏，阅读顺序正确

对照：`markitdown examples/sample_twocol.pdf`（默认 pdfminer 后端）会把左右两栏无关正文按行交错拼到同一行，如 `...comparedtothe2.7(seem- isthehumiditylevelinMiami...`；本 skill 输出中两栏分离、各成段落。

查看 [`sample_twocol.md`](sample_twocol.md)，搜索 `expanded toolkit is 5.6` 可看到左栏正文与右栏 `is the humidity level in Miami` 正确分离。
