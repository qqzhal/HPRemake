from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import GB_ENCODING
from .model import Book, Chapter, Volume


def to_halfwidth(text: str) -> str:
    """模拟易语言 到半角：全角 ASCII 区和全角空格转半角。"""
    out = []
    for ch in text:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            out.append(chr(code - 0xFEE0))
        elif ch == "\u3000":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def extract_book_author(file_path: str | Path) -> tuple[str, str]:
    """按原软件规则从文件名提取书名和作者。"""
    name = Path(str(file_path)).name
    if "." in name:
        name = name[: name.rfind(".")]
    name = name.strip()

    idx = name.find("作者：")
    if idx >= 0:
        return name[:idx].rstrip(), name[idx + 3 :].lstrip()

    last_space = name.rfind(" ")
    last_close = name.rfind("》")
    if last_close < last_space and last_space > 0:
        return name[:last_space].rstrip(), name[last_space + 1 :]
    if last_space < last_close and last_close > 2:
        return name[: last_close + 1], name[last_close + 1 :].lstrip()
    return "", ""


def _encode_for_book(text: str) -> bytes:
    """UTF-8/UTF-16 输入统一转 GBK；GBK 外的字符转 HTML 实体，保证 CHM 显示。"""
    return text.encode("gbk", errors="xmlcharrefreplace")


def normalize_source_bytes(data: bytes) -> bytes:
    """UTF-8/UTF-16 输入转 GBK（含 HTML 实体兜底），GB18030 输入原样保留。"""
    if data.startswith(b"\xef\xbb\xbf"):
        return _encode_for_book(data[3:].decode("utf-8"))
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return _encode_for_book(data.decode("utf-16"))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        return _encode_for_book(text)
    try:
        data.decode(GB_ENCODING)
        return data
    except UnicodeDecodeError:
        return data


def preprocess_bytes(data: bytes) -> bytes:
    """原软件 _按钮_下一步1 中的字节预处理。"""
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n").replace(b"\n", b"\r\n")
    data = data.replace(b"\x1a", b"")
    data = data.replace(b"\\\\", b"\\")
    data = data.replace(b"\\", b"\\\\")
    return data


@dataclass
class _Line:
    text: str
    start: int
    end_after_terminator: int
    terminated: bool


def _build_lines(processed: bytes) -> list[_Line]:
    text = processed.decode(GB_ENCODING)
    parts = text.split("\r\n")
    lines: list[_Line] = []
    pos = 0
    for idx, part in enumerate(parts):
        raw_len = len(part.encode(GB_ENCODING))
        terminated = idx < len(parts) - 1
        lines.append(
            _Line(
                text=part,
                start=pos,
                end_after_terminator=pos + raw_len + (2 if terminated else 0),
                terminated=terminated,
            )
        )
        pos += raw_len + (2 if terminated else 0)
    return lines


def _blank(line: _Line) -> bool:
    return line.text.strip() == ""


def parse_book(
    source_path: str | Path,
    book_name: str | None = None,
    author: str | None = None,
) -> Book:
    path = Path(source_path)
    if book_name is None or author is None:
        inferred_book, inferred_author = extract_book_author(path)
        book_name = inferred_book if book_name is None else book_name
        author = inferred_author if author is None else author
    if not book_name or not author:
        raise ValueError("无法从文件名识别书名/作者，请手动指定 --book 和 --author")

    data = normalize_source_bytes(path.read_bytes())
    processed = preprocess_bytes(data)
    lines = _build_lines(processed)

    volumes: list[Volume] = []
    chapters: list[Chapter] = []
    current_volume: Volume | None = None
    volume_number = 0
    i = 0
    n = len(lines)

    while i < n:
        while i < n and _blank(lines[i]):
            i += 1
        if i >= n:
            break

        title_idx = i
        is_volume = (
            i + 1 < n
            and i + 2 < n
            and _blank(lines[i + 1])
            and _blank(lines[i + 2])
            and any(not _blank(lines[j]) for j in range(i + 3, n))
        )
        if is_volume:
            volume_number += 1
            current_volume = Volume(
                name=to_halfwidth(lines[i].text.strip()),
                number=volume_number,
                chapters=[],
            )
            volumes.append(current_volume)
            i += 3
            while i < n and _blank(lines[i]):
                i += 1
            if i >= n:
                break
            title_idx = i

        if current_volume is None:
            volume_number += 1
            current_volume = Volume(name="", number=volume_number, chapters=[])
            volumes.append(current_volume)

        title = to_halfwidth(lines[title_idx].text.strip())
        body_start = lines[title_idx].end_after_terminator
        body_end = len(processed)
        blank_pair = None
        j = title_idx + 1
        while j < n:
            if _blank(lines[j]) and j + 1 < n and _blank(lines[j + 1]):
                blank_pair = j
                body_end = lines[j].start
                break
            j += 1

        has_trailing = blank_pair is not None or processed.endswith(b"\r\n")
        chapter = Chapter(
            title=title,
            volume_name=current_volume.name,
            volume_number=current_volume.number,
            body_start=body_start,
            body_end=body_end,
            body_has_trailing_newline=has_trailing,
        )
        current_volume.chapters.append(chapter)
        chapters.append(chapter)

        if blank_pair is None:
            break
        i = blank_pair + 2

    volume_digits = max(1, len(str(max(1, len(volumes)))))
    for volume in volumes:
        count = len(volume.chapters)
        chapter_digits = 1 if count < 10 else len(str(count))
        for idx, chapter in enumerate(volume.chapters, start=1):
            chapter.chapter_number = idx
            chapter.seq = (
                f"{str(volume.number).zfill(volume_digits)}_"
                f"{str(idx).zfill(chapter_digits)}"
            )

    book = Book(
        source_path=path,
        book_name=book_name,
        author=author,
        volumes=volumes,
        chapters=chapters,
        processed_bytes=processed,
    )
    for chapter in chapters:
        chapter.word_count = compute_word_count(book, chapter)
    return book


def chapter_body_text(book: Book, chapter: Chapter) -> str:
    raw = book.processed_bytes[chapter.body_start : chapter.body_end].decode(
        GB_ENCODING
    )
    if chapter.body_has_trailing_newline and not raw.endswith("\r\n"):
        raw += "\r\n"
    return raw


def compute_word_count(book: Book, chapter: Chapter) -> int:
    temp = build_body_temp(chapter_body_text(book, chapter))
    if "img src" in temp:
        return 0
    return len(temp.encode(GB_ENCODING)) // 2


def build_body_temp(raw_body: str) -> str:
    """输出TXT 中的正文排版规则，与易语言原版一致。"""
    temp = raw_body.replace("\r\n", "<p>")
    while temp.startswith("<p>"):
        temp = temp[3:]
    while "<p><p>" in temp:
        temp = temp.replace("<p><p>", "<p>")
    while "<p> " in temp or "<p>\u3000" in temp:
        temp = temp.replace("<p> ", "<p>").replace("<p>\u3000", "<p>")
    temp = "\u3000\u3000" + temp.replace("<p>", "<p>\u3000\u3000").strip(" \t\u3000")
    return temp
