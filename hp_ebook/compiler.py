from __future__ import annotations

import subprocess
from pathlib import Path

from .config import CHM_TOOL, GB_ENCODING, HPSettings, safe_dir_name
from .model import Book


def chm_file_base(book: Book) -> str:
    book_name = book.book_name.strip()
    if not (book_name.startswith("《") and book_name.endswith("》")):
        book_name = f"《{book_name}》"
    return f"{book_name}作者：{book.author}"


def _all_files(root: Path) -> list[Path]:
    files = [p for p in root.rglob("*") if p.is_file() and p.name != "temp.hhp"]
    return sorted(files)


def compile_chm(
    output_root: str | Path,
    book: Book,
    settings: HPSettings,
    hhc: str | Path = CHM_TOOL,
) -> Path:
    output_root = Path(output_root).resolve()
    output_dir = output_root / safe_dir_name(book.book_name)
    if not output_dir.is_dir():
        raise FileNotFoundError(f"HTM 输出目录不存在: {output_dir}")
    if not Path(hhc).is_file():
        raise FileNotFoundError(f"CHM 编译器不存在: {hhc}")

    title = (
        f"{book.book_name} 作者：{book.author}"
        f" - {settings.copyright.strip()} - {settings.maker.strip()}"
    )
    base = chm_file_base(book)
    hhp_text = settings.hhp_template
    hhp_text = hhp_text.replace("{标题}", title).replace("{文件名}", base)
    data = hhp_text.encode(GB_ENCODING)
    if not data.endswith(b"\n"):
        data += b"\r\n"
    for path in _all_files(output_dir):
        data += ("\r\n" + str(path)).encode(GB_ENCODING)

    hhp_path = (output_dir / "temp.hhp").resolve()
    hhp_path.write_bytes(data)
    chm_path = output_root / f"{base}.chm"
    try:
        result = subprocess.run(
            [str(hhc), str(hhp_path)],
            cwd=str(output_dir),
            capture_output=True,
            timeout=600,
            check=False,
        )
    finally:
        hhp_path.unlink(missing_ok=True)

    if result.returncode != 0 and not chm_path.exists():
        detail = (result.stdout + result.stderr).decode("gb18030", errors="replace")
        raise RuntimeError(f"CHM 编译失败：{detail}")
    if not chm_path.exists():
        raise RuntimeError("CHM 编译结束，但未找到输出文件")
    return chm_path
