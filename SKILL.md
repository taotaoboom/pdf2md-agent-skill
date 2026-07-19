---
name: pdf2md-agent-skill
version: 2.3.0
description: "将 PDF 及各类文档转为 Markdown 供 LLM 处理。PDF 自动逐页分流：文本页用 PyMuPDF（段落合并+双栏排序+页眉过滤），公式密集页和扫描页用 Ark 视觉 LLM OCR（公式转 LaTeX）。当需要读取或处理 PDF 文件内容时使用此 skill，禁止用 Read 工具直接读取 PDF。"
metadata:
  requires:
    python_packages: ["markitdown", "openai", "pymupdf"]
  cliHelp: "python3 ~/.claude/skills/pdf2md-agent-skill/scripts/md_convert.py --help"
---
# pdf2md-agent-skill- PDF/文档转 Markdown

## 何时触发

当你（agent）需要**读取 PDF 文件内容**时，必须使用本 skill。

**核心规则：禁止用 Read 工具直接读取 PDF。** Read 读 PDF 会得到乱码或空内容，必须先转为 Markdown。

触发场景：

- 用户给了 PDF 路径，要求阅读、总结、分析、翻译、问答
- 需要引用 PDF 中的具体内容
- 需要提取 PDF 中的表格、公式、参考文献

## 标准工作流

**两步，固定顺序：**

```bash
# 步骤 1：转换（自动处理所有 PDF 类型，无需判断类型）
python3 ~/.claude/skills/pdf2md-agent-skill/scripts/md_convert.py "<pdf路径>" -o /tmp/<名称>.md

# 步骤 2：用 Read 工具读取生成的 .md 文件
```

**示例：**

```bash
python3 ~/.claude/skills/pdf2md-agent-skill/scripts/md_convert.py \
  "/path/to/some-paper.pdf" \
  -o /tmp/some-paper.md
```

然后 `Read /tmp/some-paper.md`。

## 为什么这样设计

PDF 有多类页面，处理策略不同。**脚本自动逐页判断，你无需关心：**

| 页面类型             | 脚本策略               | 说明                                          |
| -------------------- | ---------------------- | --------------------------------------------- |
| 普通文本页           | PyMuPDF 提取           | 快、免费，段落合并+双栏排序+页眉过滤          |
| **公式密集页** | **Ark 视觉 OCR** | 公式转写为 LaTeX（`\( E_i \)`），避免碎片化 |
| 扫描页               | Ark 视觉 OCR           | 渲染图片 + 视觉模型识别                       |
| 混合型               | 逐页自动分流           | 一篇论文只 OCR 公式页，兼顾速度与质量         |

**智能混合策略**：脚本检测每页数学符号密度，公式页（占比 ≥1.5%）自动用 OCR 转写 LaTeX，文本页用 PyMuPDF。40 页论文通常只 OCR 8-10 页。

**禁止行为：**

- ❌ 不要判断 PDF 类型再决定调用方式--直接调用，脚本全自动
- ❌ 不要用 `markitdown` 裸命令转 PDF（默认 pdfminer 后端会丢空格）
- ❌ 不要用 Read 直接读 PDF
- ❌ 不要省略 `-o` 参数（该参数必需）

## 参数

| 参数             | 说明                                            | 何时用                                   |
| ---------------- | ----------------------------------------------- | ---------------------------------------- |
| `input`        | 输入文件路径（必需）                            | 总是                                     |
| `-o, --output` | 输出 .md 路径（必需）                           | 总是                                     |
| `--ocr`        | 强制全篇 LLM OCR                                | **仅当**自动检测明显出错时（罕见） |
| `-m, --model`  | 视觉模型，默认 `doubao-seed-1-6-flash-250828` | 需换模型时                               |
| `--no-llm`     | 非 PDF 格式禁用 LLM 增强                        | 仅非 PDF 格式                            |
| `--version`    | 显示版本号                                      | 查询版本时                               |

默认调用**不要加任何可选参数**：

```bash
python3 ~/.claude/skills/pdf2md-agent-skill/scripts/md_convert.py input.pdf -o /tmp/out.md
```

## 非 PDF 格式

Word/PPT/Excel/图片等也支持，走 markitdown 原生路径：

```bash
python3 ~/.claude/skills/pdf2md-agent-skill/scripts/md_convert.py report.docx -o /tmp/report.md
```

这类格式可直接用 Read 读，转 Markdown 是可选的（为了更好的结构化）。

## 环境与依赖

**环境变量：**

- `ARK_API_KEY` - 扫描页 OCR 必需。未设置时：文本型 PDF 仍可用，扫描页会报错退出。
- `ARK_BASE_URL` - 可选，OpenAI-compatible 端点（默认 `https://ark.cn-beijing.volces.com/api/v3`），换用其他视觉模型时设置。

**依赖（已安装）：**

- `pymupdf`（PDF 文本提取 + 渲染）
- `openai`（Ark 视觉模型客户端）
- `markitdown`（非 PDF 格式后端）

## 错误处理

| 报错                                 | 原因                    | 处理                                      |
| ------------------------------------ | ----------------------- | ----------------------------------------- |
| `ARK_API_KEY 未设置`               | 扫描页需要 OCR 但无 Key | 检查 `echo $ARK_API_KEY`，参考 ~/.zshrc |
| `文件不存在`                       | 路径错或含空格未加引号  | 用引号包裹路径                            |
| `openai/markitdown/pymupdf 未安装` | 依赖缺失                | `pip install <包名>`                    |
| `PDF 已加密`                       | PDF 设了密码            | 先解密 PDF 再转换                         |
| `OCR 失败率过高`                   | Key 无效 / 网络 / 模型名 | 看 stderr 详情，检查 Key 与模型名          |
| 转换成功但内容为空                   | 可能是纯图片 PDF 被误判 | 加 `--ocr` 强制 OCR 重试                |

**转换失败时**：不要反复重试相同命令，先看 stderr 报错信息定位问题。

## 输出约定

- 脚本将 Markdown 写入 `-o` 指定文件，stderr 输出处理日志（每页类型、进度）
- 成功时最后一行：`OK: <input> -> <output> (XX KB)`
- OCR 有失败时额外打印 `警告：X/Y 页 OCR 失败`；失败率 ≥50% 返回非零退出码
- 用 Read 读取输出文件后，正常基于内容继续工作

## 与其他工具的分工

| 场景                   | 工具                             |
| ---------------------- | -------------------------------- |
| 读 PDF 内容            | **本 skill**（必用）       |
| 读 Word/PPT/Excel      | 本 skill 或 Read（前者结构更好） |
| 读纯文本/代码/Markdown | 直接 Read                        |
