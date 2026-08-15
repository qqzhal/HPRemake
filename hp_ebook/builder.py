from __future__ import annotations

import shutil
from pathlib import Path

from .config import GB_ENCODING, TEMPLATE_ROOT, HPSettings, safe_dir_name
from .model import Book
from .parser import build_body_temp, chapter_body_text, compute_word_count


def _replace_bytes(data: bytes, old: str, new: str) -> bytes:
    return data.replace(old.encode(GB_ENCODING), new.encode(GB_ENCODING))


def standard_replace(
    data: bytes,
    settings: HPSettings,
    book: Book,
    multi_template: bool,
    title: str | None = None,
    content: str | None = None,
) -> bytes:
    if title is not None:
        data = _replace_bytes(data, "{标题}", title)
    if content is not None:
        data = _replace_bytes(data, "{内容}", content)
    data = _replace_bytes(data, "{书名}", book.book_name)
    data = _replace_bytes(data, "{作者}", book.author)
    data = _replace_bytes(data, "{制作}", settings.maker)
    data = _replace_bytes(data, "{版权}", settings.copyright)
    data = _replace_bytes(data, "{上一页}", settings.previous)
    data = _replace_bytes(data, "{目录}", settings.catalog)
    data = _replace_bytes(data, "{下一页}", settings.next_page)
    data = _replace_bytes(
        data, "{模板}", settings.template_script if multi_template else ""
    )
    data = _replace_bytes(data, "{链接}", settings.link)
    return data


def _apply_template_files(
    index_dir: Path,
    settings: HPSettings,
    book: Book,
    multi_template: bool,
) -> None:
    chapter_path = index_dir / "chapter.htm"
    chapter_data: bytes | None = None
    if chapter_path.exists():
        chapter_data = chapter_path.read_bytes()
        chapter_data = standard_replace(
            chapter_data,
            settings,
            book,
            multi_template,
            title=settings.title_chapter,
            content=settings.content_chapter,
        )
        chapter_path.write_bytes(chapter_data)

    index_path = index_dir / "index.htm"
    if index_path.exists():
        index_data = index_path.read_bytes()
    elif chapter_data is not None:
        index_data = chapter_data
    else:
        index_data = b""
    if index_data:
        index_data = standard_replace(
            index_data,
            settings,
            book,
            multi_template,
            title=settings.title_index,
            content=settings.content_index,
        )
        index_path.write_bytes(index_data)

    volume_path = index_dir / "volume.htm"
    if volume_path.exists():
        data = volume_path.read_bytes()
        data = standard_replace(
            data,
            settings,
            book,
            multi_template,
            title=settings.title_volume,
            content=settings.content_volume,
        )
        data = _replace_bytes(data, "{章节}", settings.volume_script)
        volume_path.write_bytes(data)

    readall_path = index_dir / "readall.htm"
    if readall_path.exists():
        data = readall_path.read_bytes()
        data = standard_replace(
            data,
            settings,
            book,
            multi_template,
            title=settings.title_readall,
            content=settings.content_readall,
        )
        data = _replace_bytes(data, "{章节}", settings.readall_script)
        readall_path.write_bytes(data)


def _copy_pic_folder(book: Book, txt_dir: Path) -> None:
    pic_dir = book.source_path.parent / "pic"
    if not pic_dir.is_dir():
        return
    for src in pic_dir.iterdir():
        if src.is_file():
            shutil.copy2(src, txt_dir / src.name)


def build_book(
    output_root: str | Path,
    book: Book,
    template_names: list[str],
    settings: HPSettings,
    overwrite: bool = True,
) -> Path:
    output_root = Path(output_root)
    output_dir = output_root / safe_dir_name(book.book_name)
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(f"输出目录已存在: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    multi_template = len(template_names) > 1
    for idx, template_name in enumerate(template_names, start=1):
        src = TEMPLATE_ROOT / template_name
        if not src.is_dir():
            raise FileNotFoundError(f"找不到模板: {template_name}")
        shutil.copytree(src, output_dir, dirs_exist_ok=True)
        index_dir = output_dir / "index"
        _apply_template_files(index_dir, settings, book, multi_template)
        renamed = output_dir / f"index{idx}"
        if renamed.exists():
            shutil.rmtree(renamed)
        index_dir.rename(renamed)

    txt_dir = output_dir / "txt"
    js_dir = output_dir / "js"
    txt_dir.mkdir()
    js_dir.mkdir()

    page_lines = ""
    for idx, chapter in enumerate(book.chapters):
        chapter.word_count = compute_word_count(book, chapter)
        temp = build_body_temp(chapter_body_text(book, chapter))

        header = settings.txt_template.encode(GB_ENCODING)
        header = _replace_bytes(header, "{卷章序}", chapter.seq)
        header = _replace_bytes(header, "{卷名}", chapter.volume_name)
        header = _replace_bytes(header, "{章名}", chapter.title)
        body_js = temp
        if "'" in body_js:
            body_js = body_js.replace("'", '"')
        (txt_dir / f"{chapter.seq}.txt").write_bytes(
            header + f"document.write ('{body_js}')".encode(GB_ENCODING)
        )

        first_in_volume = chapter.chapter_number == 1
        page_lines += (
            f" pages[{idx}]=['{chapter.seq}','{chapter.title}',"
            f"'{chapter.word_count}'"
        )
        if first_in_volume and chapter.volume_name:
            page_lines += f",'{chapter.volume_name}'"
        page_lines += "];\r\n"

    _copy_pic_folder(book, txt_dir)

    page_text = settings.page_template.replace("{PAGE}", page_lines)
    page_data = standard_replace(
        page_text.encode(GB_ENCODING), settings, book, multi_template
    )
    (js_dir / "page.js").write_bytes(page_data)

    star_text = settings.star_template.replace("{默认模板}", "index1")
    star_data = standard_replace(
        star_text.encode(GB_ENCODING), settings, book, multi_template
    )
    (output_dir / "start.htm").write_bytes(star_data)

    (js_dir / "chapter.js").write_bytes(settings.chapter_js.encode(GB_ENCODING))

    if multi_template:
        options = ""
        for idx, template_name in enumerate(template_names, start=1):
            options += f'<option value="../index{idx}/index.htm">{template_name}'
        mb_text = settings.mb_template.replace("{模板项目}", options)
        (js_dir / "mb.js").write_bytes(mb_text.encode(GB_ENCODING))

    return output_dir
