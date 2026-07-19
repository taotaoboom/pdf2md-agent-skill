---
name: pdf2md-agent-skill
description: "将 PDF、DOCX、PPTX、XLSX、HTML、CSV 等文档转换为适合 LLM 处理的 Markdown。PDF 自动逐页分流：普通文本页用 PyMuPDF，公式密集页、扫描页和空文本页用视觉 OCR。用户要求阅读、总结、翻译、问答、引用或提取 PDF/Office 文档内容时使用；先转换，再读取生成的 Markdown。"
---
# pdf2md-agent-skill - PDF/文档转 Markdown

## 何时触发

需要读取 PDF 内容时，先使用本 skill 转换为 Markdown。

先将 PDF 转换为 Markdown，再用当前 Agent 可用的文本读取工具读取输出文件。

触发场景：

- 用户给了 PDF 路径，要求阅读、总结、分析、翻译、问答
- 需要引用 PDF 中的具体内容
- 需要提取 PDF 中的表格、公式、参考文献

## 标准工作流

先将 `<skill_dir>` 解析为本 `SKILL.md` 所在目录。不要假定 skill 安装在 `~/.claude/skills`，因为 Codex、自定义安装和 Windows 的路径不同。

按固定顺序执行：

```bash
# 步骤 1：转换（自动处理所有 PDF 类型，无需判断类型）
python3 "<skill_dir>/scripts/md_convert.py" "<pdf路径>" -o "<工作区临时目录>/<名称>.md"

# 步骤 2：用当前 Agent 的文本读取工具读取生成的 .md 文件
```

**示例：**

```bash
python3 "<skill_dir>/scripts/md_convert.py" \
  "/path/to/some-paper.pdf" \
  -o "./some-paper.md"
```

然后读取 `./some-paper.md`。

## 为什么这样设计

PDF 有多类页面，处理策略不同。**脚本自动逐页判断，你无需关心：**

| 页面类型             | 脚本策略               | 说明                                          |
| -------------------- | ---------------------- | --------------------------------------------- |
| 普通文本页           | PyMuPDF 提取           | 快、免费，段落合并+双栏排序+页眉过滤          |
| **公式密集页** | **Ark 视觉 OCR** | 公式转写为 LaTeX（`\( E_i \)`），避免碎片化 |
| 扫描页               | Ark 视觉 OCR           | 渲染图片 + 视觉模型识别                       |
| 混合型               | 逐页自动分流           | 一篇论文只 OCR 公式页，兼顾速度与质量         |

**智能混合策略**：脚本检测每页数学符号密度，公式页（占比 >1.5%）自动用 OCR 转写 LaTeX，文本页用 PyMuPDF。

**禁止行为：**

- ❌ 不要判断 PDF 类型再决定调用方式--直接调用，脚本全自动
- ❌ 不要用 `markitdown` 裸命令转 PDF（默认 pdfminer 后端会丢空格）
- ❌ 不要把 PDF 当纯文本直接读取
- ❌ 不要省略 `-o` 参数（该参数必需）

## 参数

| 参数             | 说明                                            | 何时用                                   |
| ---------------- | ----------------------------------------------- | ---------------------------------------- |
| `input`        | 输入文件路径（必需）                            | 总是                                     |
| `-o, --output` | 输出 .md 路径（必需）                           | 总是                                     |
| `--ocr`        | 强制全篇 LLM OCR                                | **仅当**自动检测明显出错时（罕见） |
| `-m, --model`  | 视觉模型，默认 `doubao-seed-1-6-flash-250828` | 需换模型时                               |
| `--allow-partial` | 允许 OCR 缺页时仍成功退出                     | 仅在用户明确接受残缺输出时                |
| `--no-llm`     | 非 PDF 格式禁用 LLM 增强                        | 仅非 PDF 格式                            |
| `--version`    | 显示版本号                                      | 查询版本时                               |

默认调用**不要加任何可选参数**：

```bash
python3 "<skill_dir>/scripts/md_convert.py" input.pdf -o ./out.md
```

## 非 PDF 格式

Word/PPT/Excel/图片等也支持，走 markitdown 原生路径：

```bash
python3 "<skill_dir>/scripts/md_convert.py" report.docx -o ./report.md
```

这类格式可直接用相应文档工具读取；需要统一结构时再转 Markdown。

## 环境与依赖

**环境变量：**

- `ARK_API_KEY` - 公式密集页、扫描页或空文本页触发视觉 OCR 时必需。完全不触发 OCR 的文本 PDF 无需设置。
- `ARK_BASE_URL` - 可选，默认 `https://ark.cn-beijing.volces.com/api/v3`。Ark 已验证；其他端点必须兼容 Chat Completions、视觉输入和 data URL，使用前自行验证。

**依赖：**

- `pymupdf`（PDF 文本提取 + 渲染）
- `openai`（Ark 视觉模型客户端）
- `markitdown`（非 PDF 格式后端）

要求 Python 3.10+。

## 错误处理

| 报错                                 | 原因                    | 处理                                      |
| ------------------------------------ | ----------------------- | ----------------------------------------- |
| `ARK_API_KEY 未设置`               | 公式页/扫描页/空文本页需要视觉 OCR | 配置 Key，或改用不触发 OCR 的输入 |
| `文件不存在`                       | 路径错或含空格未加引号  | 用引号包裹路径                            |
| `openai/markitdown/pymupdf 未安装` | 依赖缺失                | `pip install <包名>`                    |
| `PDF 已加密`                       | PDF 设了密码            | 先解密 PDF 再转换                         |
| `检测到 OCR 缺页`                  | Key 无效 / 网络 / 模型名 | 检查错误后重试；仅在明确接受残缺输出时使用 `--allow-partial` |
| `输出路径不能与输入文件相同`       | 输出会覆盖原文档         | 为 Markdown 指定不同路径                  |
| 转换成功但内容为空                   | 可能是纯图片 PDF 被误判 | 加 `--ocr` 强制 OCR 重试                |

**转换失败时**：不要反复重试相同命令，先看 stderr 报错信息定位问题。

## 输出约定

- 脚本将 Markdown 写入 `-o` 指定文件，stderr 输出处理日志（每页类型、进度）
- 成功时最后一行：`OK: <input> -> <output> (XX KB)`
- 任一 OCR 页面失败时默认返回非零退出码；显式使用 `--allow-partial` 才接受残缺输出
- 用文本读取工具读取输出文件后，再基于内容继续工作

## 与其他工具的分工

| 场景                   | 工具                             |
| ---------------------- | -------------------------------- |
| 读 PDF 内容            | **本 skill**（必用）       |
| 读 Word/PPT/Excel      | 本 skill 或当前 Agent 的文档工具 |
| 读纯文本/代码/Markdown | 当前 Agent 的文本读取工具        |
