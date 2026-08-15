from __future__ import annotations

import dataclasses
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from . import settings_defaults


if getattr(sys, "frozen", False):
    # PyInstaller 打包后，资源目录放在 exe 同级，根目录以 exe 为准。
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_DIR = PROJECT_ROOT / "settings"
TEMPLATE_ROOT = PROJECT_ROOT / "template"
CHM_TOOL = PROJECT_ROOT / "chm" / "hhc.exe"
DEFAULT_BOOK_DIR = PROJECT_ROOT / "book"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "Ebook"

GB_ENCODING = "gb18030"
UTF8_ENCODING = "utf-8"
DEFAULT_TEMPLATE_ORDER = ("默认模板",)


def safe_dir_name(name: str) -> str:
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip() or "未命名"


def _read(path: Path, encoding: str) -> str:
    return path.read_bytes().decode(encoding)


@dataclass
class HPSettings:
    """原软件 data.edb 中可编辑参数的等价物，全部从 HP面板设置 目录读取。"""

    title_chapter: str = ""
    title_index: str = ""
    title_volume: str = ""
    title_readall: str = ""
    content_chapter: str = ""
    content_index: str = ""
    content_volume: str = ""
    content_readall: str = ""
    volume_script: str = ""
    readall_script: str = ""
    link: str = ""
    previous: str = ""
    next_page: str = ""
    catalog: str = ""
    template_script: str = ""
    star_template: str = ""
    chapter_js: str = ""
    page_template: str = ""
    mb_template: str = ""
    hhp_template: str = ""
    epj_template: str = ""
    txt_template: str = ""
    copyright: str = ""
    maker: str = ""

    @classmethod
    def load(cls, settings_dir: Path = SETTINGS_DIR) -> "HPSettings":
        restore_missing_settings(settings_dir)
        values = {}
        for attr, filename, encoding, _bom in SETTING_FILES:
            values[attr] = _read(settings_dir / filename, encoding)
        return cls(**values)

    def with_overrides(self, **kwargs: str) -> "HPSettings":
        return dataclasses.replace(self, **kwargs)


def list_templates(template_root: Path = TEMPLATE_ROOT) -> list[str]:
    if not template_root.is_dir():
        return []
    names = [p.name for p in template_root.iterdir() if p.is_dir()]
    known = [name for name in DEFAULT_TEMPLATE_ORDER if name in names]
    unknown = sorted(name for name in names if name not in DEFAULT_TEMPLATE_ORDER)
    return known + unknown


def load_template_order(template_root: Path = TEMPLATE_ROOT) -> list[str]:
    """返回上次保存且仍存在的模板顺序，无记录时退回全部模板。"""
    available = list_templates(template_root)
    path = SETTINGS_DIR / "template_order.txt"
    saved: list[str] = []
    if path.is_file():
        try:
            saved = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, UnicodeDecodeError):
            saved = []
    valid = [name for name in saved if name in available]
    return valid or list(available)


def save_template_order(names: list[str]) -> None:
    """保存模板顺序，供下次启动恢复。"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    (SETTINGS_DIR / "template_order.txt").write_text(
        "\r\n".join(names) + "\r\n", encoding="utf-8"
    )


LAST_DIRS_FILE = "last_dirs.json"
LAST_INPUT_FILE = "输入目录.txt"
LAST_OUTPUT_FILE = "输出目录.txt"


def load_last_dirs(settings_dir: Path = SETTINGS_DIR) -> dict[str, Path]:
    """读取上次使用的输入/输出目录，目录已不存在时忽略。"""
    result: dict[str, Path] = {}
    for key, filename in (
        ("input_dir", LAST_INPUT_FILE),
        ("output_dir", LAST_OUTPUT_FILE),
    ):
        path = settings_dir / filename
        if not path.is_file():
            continue
        try:
            value = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            continue
        if value:
            candidate = Path(value)
            if candidate.is_dir():
                result[key] = candidate

    legacy_path = settings_dir / LAST_DIRS_FILE
    if legacy_path.is_file():
        migrated = False
        try:
            raw = json.loads(legacy_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            raw = None
        if isinstance(raw, dict):
            for key, filename in (
                ("input_dir", LAST_INPUT_FILE),
                ("output_dir", LAST_OUTPUT_FILE),
            ):
                if key in result:
                    continue
                value = raw.get(key)
                if isinstance(value, str) and value.strip():
                    candidate = Path(value.strip())
                    if candidate.is_dir():
                        result[key] = candidate
                        migrated = True
        if migrated:
            save_last_dirs(
                input_dir=result.get("input_dir"),
                output_dir=result.get("output_dir"),
                settings_dir=settings_dir,
            )
            legacy_path.unlink(missing_ok=True)
    return result


def save_last_dirs(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings_dir: Path = SETTINGS_DIR,
) -> None:
    """保存最后使用的目录，与主设置分开存放。"""
    settings_dir.mkdir(parents=True, exist_ok=True)
    if input_dir is not None:
        (settings_dir / LAST_INPUT_FILE).write_text(
            f"{Path(input_dir)}\r\n", encoding="utf-8"
        )
    if output_dir is not None:
        (settings_dir / LAST_OUTPUT_FILE).write_text(
            f"{Path(output_dir)}\r\n", encoding="utf-8"
        )
    (settings_dir / LAST_DIRS_FILE).unlink(missing_ok=True)


SETTING_FILES: list[tuple[str, str, str, bool]] = [
    ("title_chapter", "标题_Chapter.txt", GB_ENCODING, False),
    ("title_index", "标题_Index.txt", GB_ENCODING, False),
    ("title_volume", "标题_Volume.txt", GB_ENCODING, False),
    ("title_readall", "标题_Readall.txt", GB_ENCODING, False),
    ("content_chapter", "内容_Chapter.txt", GB_ENCODING, False),
    ("content_index", "内容_Index.txt", GB_ENCODING, False),
    ("content_volume", "内容_Volume.txt", GB_ENCODING, False),
    ("content_readall", "内容_Readall.txt", GB_ENCODING, False),
    ("volume_script", "章节_Volume.txt", GB_ENCODING, False),
    ("readall_script", "章节_Readall.txt", GB_ENCODING, False),
    ("link", "链接.txt", GB_ENCODING, False),
    ("previous", "上一页.txt", GB_ENCODING, False),
    ("next_page", "下一页.txt", GB_ENCODING, False),
    ("catalog", "目录.txt", GB_ENCODING, False),
    ("template_script", "模板.txt", GB_ENCODING, False),
    ("star_template", "star.htm", "utf-8-sig", True),
    ("chapter_js", "Chapter.js", GB_ENCODING, False),
    ("page_template", "Page.js", "utf-8-sig", True),
    ("mb_template", "mb.js", UTF8_ENCODING, False),
    ("hhp_template", "HHP.txt", GB_ENCODING, False),
    ("epj_template", "EPJ.txt", GB_ENCODING, False),
    ("txt_template", "TXT模板.txt", GB_ENCODING, False),
    ("copyright", "版权.txt", GB_ENCODING, False),
    ("maker", "制作.txt", GB_ENCODING, False),
]


def save_settings(
    settings: HPSettings,
    settings_dir: Path = SETTINGS_DIR,
    fields: Iterable[str] | None = None,
) -> None:
    """把设置写回 settings 目录，保留原文件的尾部换行与 BOM。"""
    settings_dir.mkdir(parents=True, exist_ok=True)
    selected = set(fields) if fields is not None else None
    for attr, filename, encoding, has_bom in SETTING_FILES:
        if selected is not None and attr not in selected:
            continue
        path = settings_dir / filename
        old = path.read_bytes() if path.exists() else b""
        value = getattr(settings, attr)
        if old.endswith(b"\r\n") and not value.endswith("\r\n"):
            value += "\r\n"
        elif old.endswith(b"\n") and not value.endswith("\n"):
            value += "\n"
        data = value.encode(encoding)
        if has_bom and not data.startswith(b"\xef\xbb\xbf"):
            data = b"\xef\xbb\xbf" + data
        path.write_bytes(data)


def restore_missing_settings(settings_dir: Path = SETTINGS_DIR) -> list[str]:
    """settings 被误删或文件缺失时，从内置备份恢复资源文件。"""
    settings_dir.mkdir(parents=True, exist_ok=True)
    restored: list[str] = []
    for _attr, filename, encoding, has_bom in SETTING_FILES:
        path = settings_dir / filename
        if path.exists():
            continue
        text = settings_defaults.DEFAULT_SETTINGS.get(filename)
        if text is None:
            continue
        data = text.encode(encoding)
        if has_bom and not data.startswith(b"\xef\xbb\xbf"):
            data = b"\xef\xbb\xbf" + data
        path.write_bytes(data)
        restored.append(filename)
    return restored
