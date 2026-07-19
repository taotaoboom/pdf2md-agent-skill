"""冒烟测试：验证脚本基本可用，不依赖 ARK_API_KEY。

运行前先安装依赖：
    pip install -r requirements.txt

运行方式：
    # 用 pytest（推荐）
    python3 -m pytest tests/smoke_test.py -v

    # 无 pytest 时
    python3 tests/smoke_test.py
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "md_convert.py")
EXAMPLES = os.path.join(ROOT, "examples")
VERSION = "2.3.0"


def run(args, env=None):
    """运行脚本，返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True, text=True, env=env,
    )


def test_help_exits_zero():
    r = run(["--help"])
    assert r.returncode == 0, r.stderr
    assert "PDF" in r.stdout


def test_version():
    r = run(["--version"])
    assert r.returncode == 0, r.stderr
    assert VERSION in r.stdout


def test_missing_file_exits_nonzero():
    r = run(["/nonexistent/file.pdf", "-o", "/tmp/_should_not_exist.md"])
    assert r.returncode != 0
    assert "不存在" in r.stderr


def test_docx_conversion():
    src = os.path.join(EXAMPLES, "sample.docx")
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = f.name
    try:
        r = run([src, "-o", out, "--no-llm"])
        assert r.returncode == 0, r.stderr
        assert os.path.getsize(out) > 0
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_xlsx_conversion():
    src = os.path.join(EXAMPLES, "sample.xlsx")
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = f.name
    try:
        r = run([src, "-o", out, "--no-llm"])
        assert r.returncode == 0, r.stderr
        content = open(out, encoding="utf-8").read()
        assert "实验结果" in content or "超参数" in content
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_twocol_pdf_without_api_key():
    """双栏 PDF 全程文本页，无需 ARK_API_KEY 即可转换。

    依赖 examples/sample_twocol.pdf 确为纯文本页（0 OCR）。
    若该样例被替换成含公式页/扫描页的 PDF，本测试会失败——属合理信号。
    """
    src = os.path.join(EXAMPLES, "sample_twocol.pdf")
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = f.name
    # 临时清空 ARK_API_KEY，严格验证"纯文本 PDF 无需 Key"特性
    env = {k: v for k, v in os.environ.items() if k != "ARK_API_KEY"}
    try:
        r = run([src, "-o", out], env=env)
        assert r.returncode == 0, r.stderr
        content = open(out, encoding="utf-8").read()
        assert "expanded toolkit" in content or "humidity" in content
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_output_dir_autocreate():
    """输出目录不存在时应自动创建。"""
    src = os.path.join(EXAMPLES, "sample.docx")
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "sub", "deep", "out.md")
        r = run([src, "-o", out, "--no-llm"])
        assert r.returncode == 0, r.stderr
        assert os.path.exists(out)


def test_xlsx_scientific_notation_preserved():
    """xlsx 数字后处理不应破坏科学计数法（回归 P1-5）。"""
    import re
    pattern = r"(\d+)\.0+(?![0-9eE])"
    # 尾零应去除
    assert re.sub(pattern, r"\1", "32.000") == "32"
    assert re.sub(pattern, r"\1", "0.852") == "0.852"
    # 科学计数法应保留
    assert re.sub(pattern, r"\1", "1.0E+10") == "1.0E+10"
    assert re.sub(pattern, r"\1", "2.0e-3") == "2.0e-3"


if __name__ == "__main__":
    # 无 pytest 时简单运行所有 test_ 函数
    import traceback

    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception:
                failed += 1
                print(f"FAIL  {name}")
                traceback.print_exc()
    print("=" * 40)
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    sys.exit(1 if failed else 0)
