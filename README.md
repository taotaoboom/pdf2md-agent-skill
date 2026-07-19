# pdf2md-agent-skill

[English](README_EN.md) | 简体中文

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-D97757?logo=anthropic\&logoColor=white)](https://claude.com/claude-code)
[![PDF](https://img.shields.io/badge/PDF-Smart%20Routing-blue)]()
[![Office](https://img.shields.io/badge/Office-docx%2Fpptx%2Fxlsx-orange)]()

> **让 LLM agent 高效读懂任何文档。** 一条命令把 PDF / Word / PPT / Excel / HTML / CSV 转为结构化 Markdown。PDF 智能分流：文本页用 PyMuPDF 秒转，公式页用视觉模型转 LaTeX，扫描页自动 OCR。

## ✨ 核心特性

- **📄 PDF 智能分流**（独家）：逐页自动判断，文本页 PyMuPDF（快+免费）、公式页视觉 OCR（转 LaTeX）、扫描页 OCR-一篇 40 页论文只 OCR 8-10 页，兼顾质量与速度
- **⚡ 并行 OCR**：所有 OCR 页先一次性分类预渲染，再并行调用视觉模型（默认并发 10），多篇公式页近似单页耗时而非逐页串行等待
- **🔢 公式转 LaTeX**：学术论文公式从 Unicode 碎片 → 标准 LaTeX（`\( A_i \sim P_{\pi,\mathcal{T}}(\cdot | E_{i-1}) \)`），LLM 友好
- **📝 段落结构保留**：按 block 合并成段落，非"一行一断"；双栏论文正确排序；自动过滤页眉页脚/水印
- **📦 全格式覆盖**：PDF + docx/pptx/xlsx/html/csv/epub 等，一条命令统一处理
- **🤖 面向 agent 设计**：作为 Claude Code skill 自动触发，**无需你手动调用**

## 🎯 效果对比

**学术论文 PDF 提取**

| 场景 | 通用工具（markitdown 默认 pdfminer 后端）             | 本 skill                                                                    |
| ---- | ----------------------------------------------------- | --------------------------------------------------------------------------- |
| 空格 | `UncertaintyQuantificationinLLMAgents` 单词粘连     | `Uncertainty Quantification in LLM Agents` 词间空格正常                   |
| 公式 | `𝐴 𝑖 ∼ 𝑃 𝜋,𝒯 (·\|𝐸 𝑖−1 …)` 被拆成表格碎片 | `\[ A_i \sim P_{\pi,\mathcal{T}}(\cdot \| E_{i-1}, O_{i-1}) \]` 标准 LaTeX |
| 排版 | 每物理行单独成行、单词粘连                            | 按 block 合并段落，结构清晰                                                 |
| 双栏 | 左右栏交错，阅读顺序错乱                              | 先左后右，阅读顺序正确                                                      |

## 📸 实际效果

以下均为 [`examples/`](examples/) 真实样本的转换输出片段，完整结果点击各链接查看。

### PDF · 公式转 LaTeX

数学定义转写为标准 LaTeX（inline `\( ... \)`、行间 `\[ ... \]`），LLM 可直接理解：

```markdown
**Definition 1 (Stochastic Agent System).** Let \( E_i \) be an environment state, a mixture of ... Let \( O_i \) and \( A_i \) be the \( i \)-th turn observation and action derived from distributions \( P \) and \( P_{\pi,\mathcal{T}} \), respectively, where \( \mathcal{T} \) indicates a tool set and \( \pi \) is an LLM policy.

\[ A_i \sim P_{\pi,\mathcal{T}}(\cdot | E_{i-1}, O_{i-1}), \quad O_i \sim P(\cdot | A_i, E_i), \quad E_i = h(E_{i-1}, O_{i-1}, A_i). \]
```

→ 完整输出 [`examples/sample_pdf.md`](examples/sample_pdf.md)（搜 `Definition 1`）

### PDF · 双栏排序

双栏论文左栏整段在前、右栏整段在后，阅读顺序正确（pdfminer 会把两栏无关正文按行拼到同一行）：

```markdown
expanded toolkit is 5.6 compared to the 2.7 (seemingly unrelated) tools in the original BFCL dataset, meaning that three semantically-related functions were added on average to each one of the 200 testcases. Next, we evaluate the FC performance of multiple agents using the generated benchmark.

3 Agentic FC Robustness Evaluation
3.1 Experimental Setup

...（左栏续：Models / Evaluation Approach / 3.2 Experimental Results …）...

is the humidity level in Miami,Florida in the upcoming 7 days?". The expected response includes the function weather.humidity_forecast() and validates its location parameter by exact match to one of the predefined values: ["Miami", "Miami, Florida", "FL"].
```

左栏讲 toolkit expansion、右栏讲 Miami humidity，两段无关正文被正确分栏而非交错拼接。→ [`examples/sample_twocol.md`](examples/sample_twocol.md)

### Word · 标题 / 列表结构保留

```markdown
# 测试文档：Uncertainty Quantification 简介

## 1. 研究背景
不确定性量化（Uncertainty Quantification, UQ）是机器学习安全性的关键组件。大语言模型（LLM）在复杂任务中部署，需要可靠的 UQ 机制。

## 2. 主要方法
### 2.1 无序列表
* 基于概率的方法
* 基于一致性的方法
* 基于语言化的方法

### 2.2 有序列表
1. 数据收集
2. 模型训练
3. 不确定性估计
4. 结果评估
```

→ 完整输出 [`examples/sample_docx.md`](examples/sample_docx.md)（含表格转换）

### Excel · 多 sheet + 原值保留

每个 sheet 独立成章节。转换器不对生成后的 Markdown 做全局数字替换，避免误改文本中的版本号、料号或固定精度标识：

```markdown
## 实验结果
| 方法 | 准确率 | AUROC | F1 |
| --- | --- | --- | --- |
| Baseline | 0.852 | 0.78 | 0.83 |
| Method A | 0.891 | 0.85 | 0.87 |
| Method B | 0.913 | 0.89 | 0.90 |

## 超参数
| 参数 | 值 | 说明 |
| --- | --- | --- |
| learning\_rate | 0.001 | 学习率 |
| batch\_size | 32.000 | 批大小 |
| epochs | 100.000 | 训练轮数 |
```

→ 完整输出 [`examples/sample_xlsx.md`](examples/sample_xlsx.md)

## 🚀 快速开始

### 方式一：独立 CLI

```bash
# 1. 克隆并创建隔离环境
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git
cd pdf2md-agent-skill
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

# 2. 无 Key 快速体验：该双栏文本 PDF 全程本地转换
python3 scripts/md_convert.py examples/sample_twocol.pdf -o sample_twocol.md
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1` 激活环境，并可将 `python3` 替换为 `py`。

### 方式二：Claude Code skill

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git \
  ~/.claude/skills/pdf2md-agent-skill
python3 -m pip install -r \
  ~/.claude/skills/pdf2md-agent-skill/requirements.txt
```

重启 Claude Code 后，可直接要求它阅读、总结或转换 PDF。

### 方式三：Codex skill

```bash
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git \
  "$CODEX_SKILLS_DIR/pdf2md-agent-skill"
python3 -m pip install -r \
  "$CODEX_SKILLS_DIR/pdf2md-agent-skill/requirements.txt"
```

重启 Codex 后，可通过 `$pdf2md-agent-skill` 显式调用，也可在文档转换任务中自动触发。

### 可选：配置视觉 OCR

只有公式密集页、扫描页或文本提取为空的页面会调用视觉 OCR：

```bash
export ARK_API_KEY="your-ark-api-key"

# 转换
python3 scripts/md_convert.py paper.pdf -o paper.md
```

## 📋 支持格式

| 格式                          | 后端                       | 质量       | 说明                    |
| ----------------------------- | -------------------------- | ---------- | ----------------------- |
| `.pdf`                      | PyMuPDF + 视觉 OCR         | ⭐⭐⭐⭐⭐ | 智能分流，公式转 LaTeX  |
| `.docx`                     | markitdown (mammoth)       | ⭐⭐⭐⭐   | 标题/列表/表格保留      |
| `.pptx`                     | markitdown                 | ⭐⭐⭐⭐   | 幻灯片分隔 + 图片描述   |
| `.xlsx`                     | markitdown (openpyxl)      | ⭐⭐⭐⭐⭐ | 多 sheet + 文本原值保留 |
| `.html`                     | markitdown (beautifulsoup) | ⭐⭐⭐⭐   | 自动清理 script/style   |
| `.csv`                      | markitdown                 | ⭐⭐⭐⭐⭐ | 转 Markdown 表格        |
| `.epub` / `.ipynb` / 图片 | markitdown                 | ⭐⭐⭐⭐   | 多格式支持              |

## 🔧 依赖说明

### 必需依赖

| 依赖           | 作用                                  | 必需场景    |
| -------------- | ------------------------------------- | ----------- |
| `pymupdf`    | PDF 文本提取 + 页面渲染               | 所有 PDF    |
| `markitdown` | Office/HTML/CSV 等格式后端            | 非 PDF 格式 |
| `openai`     | 调用视觉模型 API（OpenAI-compatible） | OCR 功能    |

### 按格式可选（markitdown 后端）

| 依赖                              | 格式                                              |
| --------------------------------- | ------------------------------------------------- |
| `python-docx`                   | .docx                                             |
| `python-pptx`                   | .pptx                                             |
| `openpyxl`                      | .xlsx                                             |
| `xlrd`                          | .xls（旧格式）                                    |
| `beautifulsoup4` + `lxml`     | .html                                             |
| `pdfminer.six` / `pdfplumber` | markitdown 内部 PDF（本 skill 已用 PyMuPDF 替代） |

一键安装全部：

```bash
python3 -m pip install -r requirements.txt
```

### Python 版本

要求 **Python 3.10+**（markitdown 要求）。

## ⚙️ 配置

### 环境变量

| 变量             | 必需                | 说明                                                            |
| ---------------- | ------------------- | --------------------------------------------------------------- |
| `ARK_API_KEY`  | 触发视觉 OCR 时必需 | 公式密集页、扫描页或空文本页需要；完全本地提取的文本 PDF 可不设 |
| `ARK_BASE_URL` | 可选                | 默认 `https://ark.cn-beijing.volces.com/api/v3`               |
| `PDF2MD_OCR_CONCURRENCY` | 可选        | OCR 并发数，默认 10；等价 `-j`，设 1 顺序处理                    |

### 默认视觉模型

当前默认使用火山方舟视觉模型 **`doubao-seed-1-6-flash-250828`**。它只在公式密集页、扫描页或空文本页触发视觉 OCR 时调用；普通文本页仍由 PyMuPDF 在本地处理。

可通过 `-m/--model` 覆盖默认模型：

```bash
python3 scripts/md_convert.py paper.pdf -o paper.md \
  --model YOUR_ARK_VISION_MODEL_ID
```

模型 ID 可能随平台更新而下线或更名。若 OCR 报模型不存在，请在[火山方舟控制台](https://www.volcengine.com/product/ark)选择当前可用的视觉模型。

### 获取 Ark API Key

1. 注册 [火山方舟](https://www.volcengine.com/product/ark) 平台
2. 创建 API Key
3. 配置：
   ```bash
   echo 'export ARK_API_KEY="your-key"' >> ~/.zshrc
   source ~/.zshrc
   ```

> **换用其他视觉模型**：Ark 已验证。其他端点必须兼容 OpenAI Chat Completions、视觉输入和 data URL；可通过 `ARK_BASE_URL` 与 `-m` 尝试配置，但目前不声明 Azure 或本地 vLLM 已验证兼容。

## 📖 使用方法

### 命令行

```bash
# PDF（自动分流）
python3 scripts/md_convert.py paper.pdf -o paper.md

# Word / PPT / Excel
python3 scripts/md_convert.py report.docx -o report.md
python3 scripts/md_convert.py slides.pptx -o slides.md
python3 scripts/md_convert.py data.xlsx -o data.md

# 强制全篇 OCR（确定是扫描件时，省去自动检测）
python3 scripts/md_convert.py scanned.pdf -o scanned.md --ocr
```

### 参数

| 参数                | 说明                                                               |
| ------------------- | ------------------------------------------------------------------ |
| `input`           | 输入文件路径（必需）                                               |
| `-o, --output`    | 输出 Markdown 路径（必需）                                         |
| `--ocr`           | 强制全篇 LLM OCR（扫描件）                                         |
| `-m, --model`     | 视觉模型，默认 `doubao-seed-1-6-flash-250828`                    |
| `-j, --concurrency` | OCR 并发数，默认 10（等价环境变量 `PDF2MD_OCR_CONCURRENCY`）；设 1 顺序处理 |
| `--allow-partial` | 允许部分 OCR 页面失败后仍返回成功；默认任一 OCR 缺页都返回非零状态 |
| `--no-llm`        | 非 PDF 格式禁用 LLM 增强                                           |

### 作为 Agent skill

安装到 Claude Code 或 Codex 对应的 skills 目录并重启后，agent 可在 PDF/文档转换任务中调用本 skill。Codex 也可以使用 `$pdf2md-agent-skill` 显式调用。

**核心规则（写给 agent）**：禁止用 Read 直接读 PDF，必须先转 Markdown 再读。

## 🧠 工作原理

### PDF 智能分流

```
逐页分析：
  数学符号占比 ≥ 1.5%？ ──是──> 公式页 -> 视觉 OCR（转 LaTeX）
  文字稀少 + 有图片？    ──是──> 扫描页 -> 视觉 OCR
  否                     ──────> 文本页 -> PyMuPDF（段落合并+双栏排序+页眉过滤）
```

文本页用 PyMuPDF 秒转（免费），只有公式页和扫描页才调用视觉模型（收费），**平衡质量与成本**。

### Office 格式

走 markitdown 原生路径；本 skill 不对 xlsx 生成的 Markdown 做全局数字替换，以免篡改文本值。pptx 图片可选 LLM 描述。

## 📂 文件结构

```
pdf2md-agent-skill/
├── SKILL.md            # Agent skill 定义
├── agents/openai.yaml  # Codex UI 元数据
├── README.md           # 本文件
├── README_EN.md        # English documentation
├── CHANGELOG.md        # 版本变更记录
├── LICENSE             # MIT
├── requirements.txt    # 依赖清单
├── .gitignore
├── examples/           # 示例输入输出
│   ├── README.md
│   ├── sample.docx / sample_docx.md
│   ├── sample.xlsx / sample_xlsx.md
│   ├── sample.pdf  / sample_pdf.md
│   └── sample_twocol.pdf / sample_twocol.md
├── scripts/
│   └── md_convert.py   # 主转换脚本
└── tests/
    └── smoke_test.py   # 冒烟测试（不依赖 ARK_API_KEY）
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)
