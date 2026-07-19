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
import importlib.util
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "md_convert.py")
EXAMPLES = os.path.join(ROOT, "examples")
VERSION = "2.4.0"

SPEC = importlib.util.spec_from_file_location("md_convert", SCRIPT)
MD_CONVERT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MD_CONVERT)


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
    assert "--allow-partial" in r.stdout


def test_version():
    r = run(["--version"])
    assert r.returncode == 0, r.stderr
    assert VERSION in r.stdout


def test_missing_file_exits_nonzero():
    with tempfile.TemporaryDirectory() as d:
        r = run([os.path.join(d, "missing.pdf"), "-o", os.path.join(d, "out.md")])
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


def test_xlsx_text_values_are_not_rewritten():
    from openpyxl import Workbook

    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "text-values.xlsx")
        out = os.path.join(d, "out.md")
        wb = Workbook()
        ws = wb.active
        ws.append(["value"])
        ws.append(["version 1.000"])
        ws.append(["part 32.000A"])
        wb.save(src)
        r = run([src, "-o", out, "--no-llm"])
        assert r.returncode == 0, r.stderr
        content = open(out, encoding="utf-8").read()
        assert "version 1.000" in content
        assert "part 32.000A" in content


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


def test_formula_pdf_without_api_key_reports_visual_ocr_requirement():
    src = os.path.join(EXAMPLES, "sample.pdf")
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = f.name
    env = {k: v for k, v in os.environ.items() if k != "ARK_API_KEY"}
    try:
        r = run([src, "-o", out], env=env)
        assert r.returncode == 2
        assert "公式页 -> OCR" in r.stderr
        assert "视觉 OCR" in r.stderr
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


def test_input_and_output_cannot_be_same_file():
    src = os.path.join(EXAMPLES, "sample_twocol.pdf")
    with tempfile.TemporaryDirectory() as d:
        local_pdf = os.path.join(d, "input.pdf")
        with open(src, "rb") as source, open(local_pdf, "wb") as target:
            target.write(source.read())
        before = open(local_pdf, "rb").read()
        r = run([local_pdf, "-o", local_pdf])
        assert r.returncode != 0
        assert "不能与输入文件相同" in r.stderr
        assert open(local_pdf, "rb").read() == before


def test_input_and_output_symlink_alias_is_rejected():
    if not hasattr(os, "symlink"):
        return
    src = os.path.join(EXAMPLES, "sample_twocol.pdf")
    with tempfile.TemporaryDirectory() as d:
        local_pdf = os.path.join(d, "input.pdf")
        alias = os.path.join(d, "alias.pdf")
        with open(src, "rb") as source, open(local_pdf, "wb") as target:
            target.write(source.read())
        try:
            os.symlink(local_pdf, alias)
        except OSError:
            return
        r = run([local_pdf, "-o", alias])
        assert r.returncode != 0
        assert "不能与输入文件相同" in r.stderr


def test_partial_ocr_requires_explicit_opt_in():
    assert MD_CONVERT._partial_ocr_is_error(1, allow_partial=False)
    assert not MD_CONVERT._partial_ocr_is_error(1, allow_partial=True)
    assert not MD_CONVERT._partial_ocr_is_error(0, allow_partial=False)


def test_partial_ocr_exit_status_end_to_end():
    src = os.path.join(EXAMPLES, "sample.pdf")
    fake_openai = """
class _Completions:
    def create(self, **kwargs):
        raise RuntimeError("simulated OCR failure")
class _Chat:
    completions = _Completions()
class OpenAI:
    def __init__(self, **kwargs):
        self.chat = _Chat()
"""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "openai.py"), "w", encoding="utf-8") as f:
            f.write(fake_openai)
        strict_out = os.path.join(d, "strict.md")
        partial_out = os.path.join(d, "partial.md")
        env = dict(os.environ)
        env["ARK_API_KEY"] = "test-key"
        env["PYTHONPATH"] = d + os.pathsep + env.get("PYTHONPATH", "")

        strict = run([src, "-o", strict_out], env=env)
        assert strict.returncode != 0
        assert "检测到 OCR 缺页" in strict.stderr
        assert "OK:" not in strict.stderr

        partial = run([src, "-o", partial_out, "--allow-partial"], env=env)
        assert partial.returncode == 0, partial.stderr
        assert "--allow-partial" in partial.stderr
        assert "OK:" in partial.stderr


def test_concurrency_one_runs_sequential_path():
    """-j 1 走顺序分支：fake openai 全失败时，与默认并行路径同样报 OCR 缺页。"""
    src = os.path.join(EXAMPLES, "sample.pdf")
    fake_openai = """
class _Completions:
    def create(self, **kwargs):
        raise RuntimeError("simulated OCR failure")
class _Chat:
    completions = _Completions()
class OpenAI:
    def __init__(self, **kwargs):
        self.chat = _Chat()
"""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "openai.py"), "w", encoding="utf-8") as f:
            f.write(fake_openai)
        out = os.path.join(d, "out.md")
        env = dict(os.environ)
        env["ARK_API_KEY"] = "test-key"
        env["PYTHONPATH"] = d + os.pathsep + env.get("PYTHONPATH", "")

        r = run([src, "-o", out, "-j", "1"], env=env)
        assert r.returncode != 0
        assert "检测到 OCR 缺页" in r.stderr
        assert "OK:" not in r.stderr


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
