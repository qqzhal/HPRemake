from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chapter:
    title: str = ""
    volume_name: str = ""
    volume_number: int = 0
    chapter_number: int = 0
    seq: str = ""
    body_start: int = 0
    body_end: int = 0
    body_has_trailing_newline: bool = False
    word_count: int = 0


@dataclass
class Volume:
    name: str = ""
    number: int = 0
    chapters: list[Chapter] = field(default_factory=list)


@dataclass
class Book:
    source_path: Path
    book_name: str
    author: str
    volumes: list[Volume]
    chapters: list[Chapter]
    processed_bytes: bytes
