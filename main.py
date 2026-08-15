from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hp_ebook.builder import build_book
from hp_ebook.compiler import compile_chm
from hp_ebook.config import (
    CHM_TOOL,
    DEFAULT_BOOK_DIR,
    DEFAULT_OUTPUT_ROOT,
    HPSettings,
    load_template_order,
)
from hp_ebook.gui import run_gui
from hp_ebook.parser import parse_book


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HP电子书制作软件 v3.2（Python 重制）")
    parser.add_argument("--file", help="要制作的 txt 文件")
    parser.add_argument("--book", help="书名（默认从文件名识别）")
    parser.add_argument("--author", help="作者（默认从文件名识别）")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="输出根目录，默认 Ebook",
    )
    parser.add_argument(
        "--templates",
        nargs="*",
        default=None,
        help="按顺序使用的模板名，默认全部模板",
    )
    parser.add_argument("--compile", action="store_true", help="输出后自动编译 CHM")
    parser.add_argument("--gui", action="store_true", help="启动图形界面")
    args = parser.parse_args(argv)

    if args.gui or not args.file:
        run_gui()
        return 0

    book = parse_book(args.file, args.book, args.author)
    templates = args.templates or load_template_order()
    if not templates:
        print("没有找到可用模板", file=sys.stderr)
        return 2

    settings = HPSettings.load()
    output_dir = build_book(args.output, book, templates, settings)
    print(f"HTM 输出目录：{output_dir}")
    print(f"章节数：{len(book.chapters)}")

    if args.compile:
        chm = compile_chm(args.output, book, settings, CHM_TOOL)
        print(f"CHM 文件：{chm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
