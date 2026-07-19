#!/usr/bin/env python3
"""
markitdown skill - PDF/文档 转 Markdown（面向 LLM agent）

设计目标：agent 遇到 PDF 时，一条命令转为高质量 Markdown，无需判断 PDF 类型。

自动策略（逐页判断）：
  - 文本页（born-digital）-> PyMuPDF 提取（保留空格、过滤页眉页脚、多栏排序）
  - 扫描页（scanned）    -> 渲染图片 + Ark 视觉 LLM OCR
  - 混合型 PDF           -> 逐页自动分流
  - 非 PDF（Word/PPT等） -> markitdown 原生

用法:
    python3 md_convert.py <input> -o <output.md> [--ocr] [--no-llm] [-m MODEL] [--version]

环境变量:
    ARK_API_KEY  - Ark API Key（扫描页 OCR 必需；未设置时扫描页会报错）
    ARK_BASE_URL - 可选，OpenAI-compatible 端点（默认火山方舟）
"""

import os
import sys
import base64

__version__ = "2.3.0"

DEFAULT_MODEL = "doubao-seed-1-6-flash-250828"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
# 页面文字少于该字符数且含图片，判定为扫描页
SCAN_TEXT_THRESHOLD = 50
# OCR 单页失败时的重试次数（不含首次），用于应对网络抖动/限流
OCR_MAX_RETRIES = 1


def get_ark_client():
    """创建 Ark OpenAI-compatible 客户端。"""
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai 包未安装，请运行 pip install openai", file=sys.stderr)
        sys.exit(2)

    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("ERROR: ARK_API_KEY 未设置（扫描页 OCR 必需）", file=sys.stderr)
        sys.exit(2)

    base_url = os.environ.get("ARK_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


# ---------------------------------------------------------------------------
# PDF 文本页提取
# ---------------------------------------------------------------------------

def extract_text_page(page):
    """提取文本页：按 block（段落）合并输出，过滤页眉页脚/边距水印，双栏排序。

    改进点（相比按 line 输出）：
    - 按 PyMuPDF 的 block（通常=段落）合并行，block 内行用空格连接成段落
    - block 之间用空行分隔，输出结构化 Markdown 而非"一行一断"
    - 过滤边距水印（如 arXiv 角标 x0 < 30）
    - 连字符断词合并（"quantiﬁ- cation" -> "quantiﬁcation"）
    - 双栏检测与排序以 block 中心点为单位
    """
    import re

    page_height = page.rect.height
    page_width = page.rect.width
    header_thresh = page_height * 0.08
    footer_thresh = page_height * 0.92

    page_dict = page.get_text("dict")
    blocks = []
    for block in page_dict.get("blocks", []):
        if "lines" not in block:
            continue
        bx0, by0, bx1, by1 = block["bbox"]
        # 过滤页眉（顶部 8%）、页脚（底部 8%）、边距水印（x0 < 30，如 arXiv 角标）
        if by0 < header_thresh or by0 > footer_thresh:
            continue
        if bx0 < 30:
            continue
        # 合并 block 内的行成一个段落
        line_texts = []
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                line_texts.append(text)
        if not line_texts:
            continue
        para = " ".join(line_texts)
        # 合并跨行连字符断词：行尾"小写字母-" + 空格 + "小写字母"
        para = re.sub(r"([a-z])-\s+([a-z])", r"\1\2", para)
        blocks.append({
            "x0": bx0, "x1": bx1, "y0": by0,
            "center": (bx0 + bx1) / 2,
            "text": para,
        })

    if not blocks:
        return ""

    # 双栏检测：用窄 block（宽度 < 页宽 45%）的中心点判断
    mid = page_width / 2
    narrow = [b for b in blocks if (b["x1"] - b["x0"]) < page_width * 0.45]
    is_two_col = False
    if len(narrow) >= 8:
        left_n = sum(1 for b in narrow if b["center"] < mid)
        right_n = len(narrow) - left_n
        is_two_col = left_n > len(narrow) * 0.15 and right_n > len(narrow) * 0.15

    if is_two_col:
        left = sorted([b for b in blocks if b["center"] < mid], key=lambda b: b["y0"])
        right = sorted([b for b in blocks if b["center"] >= mid], key=lambda b: b["y0"])
        ordered = left + right
    else:
        ordered = sorted(blocks, key=lambda b: b["y0"])

    # block 之间用空行分隔，形成段落结构
    return "\n\n".join(b["text"] for b in ordered)


# ---------------------------------------------------------------------------
# PDF 扫描页 OCR
# ---------------------------------------------------------------------------

def ocr_page(page, model, client):
    """渲染页面为图片，调用 Ark 视觉模型 OCR。

    client 由调用方传入并复用，避免每页重复建连。
    失败时重试 OCR_MAX_RETRIES 次；仍失败返回 None（由调用方统计与占位）。
    """
    import fitz

    # 2x 缩放提高 OCR 精度
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")

    prompt = (
        "Transcribe this document page image to Markdown. Rules:\n"
        "1. Output ONLY the transcribed content. Start directly with the first word on the page.\n"
        "2. NO commentary, NO introductions, NO descriptions (e.g. no '以下是正文', '接下来', '第一段').\n"
        "3. Preserve headings, paragraphs, lists, and tables structure.\n"
        "4. Transcribe math formulas as LaTeX: use $...$ for inline math, $$...$$ for display math.\n"
        "5. Keep the original language (English stays English, do not translate).\n"
        "6. For figures, output the caption text only."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                },
            ],
        }
    ]

    last_err = None
    for attempt in range(OCR_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            last_err = e
            if attempt < OCR_MAX_RETRIES:
                continue
    print(f"  OCR 失败: {last_err}", file=sys.stderr)
    return None


def _ocr_page_chunk(page, model, client, page_num, total, reason):
    """对单页执行 OCR，返回 (chunk_text, failed)。

    failed=True 时 chunk_text 为占位注释。日志格式：[page/total] reason -> OCR。
    """
    print(f"[{page_num}/{total}] {reason} -> OCR", file=sys.stderr)
    out = ocr_page(page, model, client)
    if out is None:
        return f"<!-- 第 {page_num} 页 OCR 失败 -->", True
    return out, False


# ---------------------------------------------------------------------------
# PDF 主转换（自动逐页分流）
# ---------------------------------------------------------------------------

def convert_pdf(input_path, model, force_ocr=False):
    """自动逐页分流：文本页 PyMuPDF，公式页/扫描页 LLM OCR。

    分流逻辑：
    - force_ocr：强制全篇 OCR
    - 扫描页（文字稀少+有图片）：OCR
    - 公式密集页（数学符号占比 > 1.5%）：OCR（视觉模型转写 LaTeX 公式）
    - 普通文本页：PyMuPDF（快、免费）

    返回 (markdown, ocr_count, ocr_failures)：
    - ocr_count：尝试 OCR 的页数
    - ocr_failures：OCR 失败的页数

    纯文本 PDF 不会触发 OCR，因此无需 ARK_API_KEY。
    """
    import fitz

    with fitz.open(input_path) as doc:
        if doc.is_encrypted and not doc.authenticate(""):
            print("ERROR: PDF 已加密，需提供密码（暂不支持）", file=sys.stderr)
            sys.exit(1)

        total = len(doc)
        if total == 0:
            print("ERROR: PDF 无任何页面", file=sys.stderr)
            sys.exit(1)

        # 延迟创建 OCR 客户端：首次需要 OCR 时才建，纯文本 PDF 无需 ARK_API_KEY
        client = None

        def ensure_client():
            nonlocal client
            if client is None:
                client = get_ark_client()
            return client

        chunks = []
        ocr_count = 0
        ocr_failures = 0

        for idx, page in enumerate(doc):
            page_num = idx + 1

            if force_ocr:
                ocr_count += 1
                chunk, failed = _ocr_page_chunk(
                    page, model, ensure_client(), page_num, total, "强制 OCR"
                )
                ocr_failures += failed
                chunks.append(chunk)
                continue

            # 扫描页检测（文字稀少+有图片）
            if _is_scanned_page(page):
                ocr_count += 1
                chunk, failed = _ocr_page_chunk(
                    page, model, ensure_client(), page_num, total, "扫描页"
                )
                ocr_failures += failed
                chunks.append(chunk)
                continue

            # 文本页：先 PyMuPDF 提取
            text = extract_text_page(page)

            # 公式密集页：OCR 转写 LaTeX 公式（比 PyMuPDF 碎片化好很多）
            if _is_formula_heavy(text):
                ocr_count += 1
                chunk, failed = _ocr_page_chunk(
                    page, model, ensure_client(), page_num, total, "公式页"
                )
                ocr_failures += failed
                chunks.append(chunk)
            elif text.strip():
                print(f"[{page_num}/{total}] 文本页 -> PyMuPDF", file=sys.stderr)
                chunks.append(text)
            else:
                ocr_count += 1
                chunk, failed = _ocr_page_chunk(
                    page, model, ensure_client(), page_num, total, "文本为空"
                )
                ocr_failures += failed
                chunks.append(chunk)

    print(f"完成：共 {total} 页，其中 {ocr_count} 页 OCR（{ocr_failures} 页失败）", file=sys.stderr)

    # 跨页连字符断词合并：上一页末尾"词-" + 下一页开头"词" -> "词"
    import re
    merged = []
    for i, chunk in enumerate(chunks):
        if i > 0 and merged:
            prev = merged[-1]
            m = re.search(r"([a-z])-\s*$", prev.rstrip())
            if m and chunk.strip() and chunk.strip()[0].islower():
                merged[-1] = prev.rstrip()[: m.start()] + m.group(1) + chunk.lstrip()
                continue
        merged.append(chunk)
    return "\n\n".join(merged), ocr_count, ocr_failures


def _is_formula_heavy(text, threshold=0.015):
    """检测文本是否公式密集（数学 Unicode 符号占比 > threshold，默认 1.5%）。

    公式页含大量 Mathematical Alphabetic Symbols（U+1D400-U+1D7FF，如 𝐴𝐸𝑂）
    和数学符号（∑∏∫等）。这类页面 PyMuPDF 会提取成碎片化 Unicode 文本，
    用视觉模型 OCR 转写为 LaTeX 公式质量更好。
    """
    if not text:
        return False
    math_alpha = sum(1 for c in text if "\U0001D400" <= c <= "\U0001D7FF")
    math_sym = sum(1 for c in text if c in "∑∏∫≤≥≠∈∀∃∂∇√∞")
    return (math_alpha + math_sym) / len(text) > threshold


def _is_scanned_page(page):
    """检测页面是否为扫描页：文字稀少且含图片。"""
    text = page.get_text("text").strip()
    if len(text) >= SCAN_TEXT_THRESHOLD:
        return False
    images = page.get_images()
    return len(images) > 0


# ---------------------------------------------------------------------------
# 非 PDF 格式（markitdown 原生）
# ---------------------------------------------------------------------------

def convert_other(input_path, use_llm, model):
    """Word/PPT/Excel 等走 markitdown，可选 LLM 增强。"""
    try:
        from markitdown import MarkItDown
    except ImportError:
        print("ERROR: markitdown 未安装，请运行 pip install markitdown", file=sys.stderr)
        sys.exit(2)

    if use_llm:
        client = get_ark_client()
        md = MarkItDown(llm_client=client, llm_model=model)
    else:
        md = MarkItDown()

    result = md.convert(input_path).text_content

    # xlsx 后处理：openpyxl 把整数读成浮点（32 -> 32.000），去掉无意义的 .0+ 尾零
    # 仅匹配小数点后全为 0 且后跟非数字/非科学计数法（如 32.000| -> 32|），
    # 保留 0.001 / 0.852 等，也保留 1.0E+10 这类科学计数法
    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".xlsx", ".xls") and result:
        import re
        result = re.sub(r"(\d+)\.0+(?![0-9eE])", r"\1", result)

    return result


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="PDF/文档转 Markdown（agent 用）：PDF 自动逐页分流，非 PDF 走 markitdown"
    )
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", required=True, help="输出 Markdown 文件路径（必需）")
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help=f"Ark 视觉模型（默认 {DEFAULT_MODEL}）"
    )
    parser.add_argument(
        "--ocr", action="store_true",
        help="强制全篇 LLM OCR（确定是扫描件时用，省去自动检测）"
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="非 PDF 格式禁用 LLM 增强（对 PDF 无效）"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()

    ocr_count = 0
    ocr_failures = 0
    if ext == ".pdf":
        markdown, ocr_count, ocr_failures = convert_pdf(
            args.input, args.model, force_ocr=args.ocr
        )
    else:
        use_llm = not args.no_llm
        if use_llm and not os.environ.get("ARK_API_KEY"):
            print("提示：ARK_API_KEY 未设置，非 PDF 格式降级为无 LLM 增强", file=sys.stderr)
            use_llm = False
        markdown = convert_other(args.input, use_llm, args.model)

    # 输出目录不存在时自动创建（支持 -o /tmp/sub/out.md 这种深层路径）
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown)

    size_kb = os.path.getsize(args.output) / 1024
    print(f"OK: {args.input} -> {args.output} ({size_kb:.1f} KB)", file=sys.stderr)

    # OCR 失败告警：失败率高时返回非零退出码，提示 agent 不要把残缺输出当完整结果
    if ocr_failures > 0:
        print(f"警告：{ocr_failures}/{ocr_count} 页 OCR 失败，输出可能不完整", file=sys.stderr)
        if ocr_count > 0 and ocr_failures >= ocr_count * 0.5:
            print("错误：OCR 失败率过高，请检查 ARK_API_KEY / 网络 / 模型名", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
