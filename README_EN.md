# pdf2md-agent-skill

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Convert PDF and common Office documents to Markdown for command-line and AI-agent workflows. PDF pages are routed individually: ordinary text pages use PyMuPDF, while equation-heavy, scanned, or text-empty pages use visual OCR.

[中文说明](README.md)

## Quick Start

Requires Python 3.10 or newer.

```bash
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git
cd pdf2md-agent-skill
python3 -m pip install -r requirements.txt
python3 scripts/md_convert.py /path/to/paper.pdf -o ./paper.md
```

A born-digital PDF containing ordinary text may convert without an API key. If any page is equation-heavy, scanned, or has no extractable text, visual OCR is triggered and `ARK_API_KEY` is required.

## Features

- Per-page PDF routing between PyMuPDF text extraction and visual OCR
- LaTeX-oriented OCR prompts for equation-heavy pages
- Paragraph reconstruction and basic multi-column ordering for text PDFs
- DOCX, PPTX, XLSX, HTML, CSV, and other formats supported through `markitdown`
- Explicit failure status when any OCR page is missing
- CLI and reusable skill instructions for Claude Code and Codex

XLSX conversion does not run a global trailing-zero replacement over the generated Markdown. Text such as version identifiers and part numbers is preserved rather than rewritten as if it were numeric data.

## Installation

### CLI

Install the repository wherever you keep command-line tools:

```bash
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git
cd pdf2md-agent-skill
python3 -m pip install -r requirements.txt
python3 scripts/md_convert.py --help
```

Run the script with its repository-relative path, or use an absolute path from another working directory.

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git \
  ~/.claude/skills/pdf2md-agent-skill
python3 -m pip install -r \
  ~/.claude/skills/pdf2md-agent-skill/requirements.txt
```

Start a new Claude Code session after installation so the skill can be discovered. The instructions in `SKILL.md` resolve the script relative to the installed skill directory; they do not require a particular project working directory.

### Codex

```bash
CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
git clone https://github.com/taotaoboom/pdf2md-agent-skill.git \
  "$CODEX_SKILLS_DIR/pdf2md-agent-skill"
python3 -m pip install -r \
  "$CODEX_SKILLS_DIR/pdf2md-agent-skill/requirements.txt"
```

Start a new Codex session after installation so the skill can be discovered. When the skill is selected, Codex converts the document to a Markdown file in the active workspace before reading it.

## Configuration

Visual OCR has been verified with Volcengine Ark. Configure it with:

```bash
export ARK_API_KEY="your-ark-api-key"
# Optional; this is the default:
export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

The default visual model is `doubao-seed-1-6-flash-250828`. If that model is unavailable for your account or has been retired, pass a currently available Ark vision model with `-m`.

Other endpoints may work only if they implement the required OpenAI-compatible Chat Completions behavior, visual input, and data URLs. They have not been verified by this project and must be tested independently.

Pages sent to visual OCR are rendered as images and transmitted to the configured endpoint. Review the endpoint's privacy, retention, and pricing terms before processing confidential documents.

## Usage

```bash
# Automatic per-page routing
python3 scripts/md_convert.py paper.pdf -o paper.md

# Force visual OCR for every PDF page
python3 scripts/md_convert.py scanned.pdf -o scanned.md --ocr

# Select another Ark vision model
python3 scripts/md_convert.py paper.pdf -o paper.md -m MODEL_ID

# Explicitly accept output with failed OCR pages
python3 scripts/md_convert.py paper.pdf -o paper.md --allow-partial

# Office and structured-document conversion
python3 scripts/md_convert.py report.docx -o report.md
python3 scripts/md_convert.py slides.pptx -o slides.md
python3 scripts/md_convert.py data.xlsx -o data.md
```

Key options:

| Option              | Meaning                                                       |
| ------------------- | ------------------------------------------------------------- |
| `input`           | Source document path                                          |
| `-o, --output`    | Required Markdown output path                                 |
| `--ocr`           | Force visual OCR for every PDF page                           |
| `-m, --model`     | Visual model ID; defaults to `doubao-seed-1-6-flash-250828` |
| `--allow-partial` | Return success even when one or more OCR pages fail           |
| `--no-llm`        | Disable LLM enhancement for non-PDF formats                   |
| `--version`       | Print the converter version                                   |

The input and output must not resolve to the same file. The converter rejects identical paths and existing filesystem aliases instead of overwriting the source document.

## Failure Behavior

- If a PDF never triggers OCR, `ARK_API_KEY` is not needed.
- If an equation-heavy, scanned, or text-empty page triggers OCR without a key, conversion fails with an explanatory error.
- If any OCR page fails, the command returns a non-zero exit code by default, even if a partial Markdown file was written.
- `--allow-partial` is an explicit opt-in to accept missing OCR pages and return success.
- Reusing the input file as `-o` is rejected before conversion.

Agents and automation should check the process exit code before treating the Markdown as complete.

## Tests

Run the repository's test suite from the project directory:

```bash
python3 tests/smoke_test.py
# Or, when pytest is installed:
python3 -m pytest tests/smoke_test.py -v
```

The local tests cover no-key conversion paths, CLI behavior, common Office formats, path safety, and failure handling. Visual OCR quality is demonstrated by the checked-in examples; the project does not currently claim a cross-dataset OCR accuracy benchmark.

See [`examples/`](examples/) for sample inputs and generated Markdown.

## License

The project code is released under the [MIT License](LICENSE). Sample or third-party documents may have separate source licenses; check their provenance before redistribution.
