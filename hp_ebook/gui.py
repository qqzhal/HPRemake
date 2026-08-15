from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from .builder import build_book
from .compiler import compile_chm
from .config import (
    CHM_TOOL,
    DEFAULT_BOOK_DIR,
    DEFAULT_OUTPUT_ROOT,
    SETTINGS_DIR,
    HPSettings,
    list_templates,
    load_last_dirs,
    load_template_order,
    save_last_dirs,
    save_settings,
    save_template_order,
)
from .parser import extract_book_author, parse_book


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


SETTING_GROUPS = (
    (
        "常用参数",
        (
            ("maker", "制作", False),
            ("copyright", "版权", False),
            ("link", "链接", False),
            ("previous", "上一页", False),
            ("next_page", "下一页", False),
            ("catalog", "目录", False),
            ("template_script", "模板", False),
        ),
    ),
    (
        "标题模板",
        (
            ("title_chapter", "标题_Chapter", False),
            ("title_index", "标题_Index", False),
            ("title_volume", "标题_Volume", False),
            ("title_readall", "标题_Readall", False),
        ),
    ),
    (
        "正文模板",
        (
            ("content_chapter", "内容_Chapter", True),
            ("content_index", "内容_Index", True),
            ("content_volume", "内容_Volume", True),
            ("content_readall", "内容_Readall", True),
        ),
    ),
    (
        "章节脚本",
        (
            ("volume_script", "章节_Volume", True),
            ("readall_script", "章节_Readall", True),
        ),
    ),
    (
        "脚本文件",
        (
            ("chapter_js", "Chapter.js", True),
            ("page_template", "Page.js", True),
            ("mb_template", "mb.js", True),
            ("hhp_template", "HHP.txt", True),
            ("epj_template", "EPJ.txt", True),
            ("txt_template", "TXT模板.txt", True),
            ("star_template", "star.htm", True),
        ),
    ),
)

EXTRA_GROUP = "扩展"


class HpEbookApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("HP电子书制作软件 v3.2（Python 重制）")
        self.root.geometry("1020x740")
        self.root.minsize(880, 620)

        self.settings = HPSettings.load()
        self.available_templates = list_templates()
        self.selected_templates: list[str] = load_template_order()
        last_dirs = load_last_dirs()
        self.input_dir = last_dirs.get("input_dir", DEFAULT_BOOK_DIR)
        self.output_root = last_dirs.get("output_dir", DEFAULT_OUTPUT_ROOT)
        self.book = None
        self.last_output_dir: Path | None = None
        self.last_output_root: Path | None = None
        self.last_chm: Path | None = None
        self.dirty_groups: set[str] = set()
        self.current_setting_group: str | None = None
        self.group_buttons: dict[str, ctk.CTkButton] = {}
        self.group_frames: dict[str, ctk.CTkFrame] = {}
        self._loading_settings = False
        self.text_widgets: dict[str, ctk.CTkTextbox] = {}

        self._build_ui()
        self._load_settings_into_widgets()
        self._update_step_buttons()
        self._set_status("请先在“输入文件”页选择 txt 并解析")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.status_var = tk.StringVar()
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        self.input_tab = self.notebook.add("输入文件")
        self.tree_tab = self.notebook.add("目录结构")
        self.output_tab = self.notebook.add("输出")
        self.settings_tab = self.notebook.add("设置")
        self.notebook.set("输入文件")

        self._tab_input()
        self._tab_tree()
        self._tab_settings()
        self._tab_output()

        ctk.CTkLabel(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            text_color="#555555",
        ).pack(fill="x", padx=14, pady=(0, 12))

    def _tab_input(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.input_tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            frame, text="输入文件", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ctk.CTkLabel(frame, text="文本文件：").grid(
            row=1, column=0, sticky="e", pady=6
        )
        self.file_var = tk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.file_var, height=34).grid(
            row=1, column=1, sticky="we", padx=6
        )
        ctk.CTkButton(
            frame, text="浏览...", width=90, command=self._browse_file
        ).grid(row=1, column=2)

        ctk.CTkLabel(frame, text="书名：").grid(row=2, column=0, sticky="e", pady=6)
        self.book_var = tk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.book_var, height=34).grid(
            row=2, column=1, columnspan=2, sticky="we", padx=6
        )

        ctk.CTkLabel(frame, text="作者：").grid(row=3, column=0, sticky="e", pady=6)
        self.author_var = tk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.author_var, height=34).grid(
            row=3, column=1, columnspan=2, sticky="we", padx=6
        )

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.grid(row=4, column=2, sticky="e", pady=(18, 0))
        ctk.CTkButton(
            actions, text="读取并解析", width=120, command=self._parse_and_show
        ).pack(side="left", padx=4)

        frame.columnconfigure(1, weight=1)
        return frame

    def _is_tab_enterable(self, name: str) -> bool:
        if name in ("输入文件", "设置"):
            return True
        return self.book is not None

    def _select_tab(self, name: str) -> None:
        if not self._is_tab_enterable(name):
            return
        self.notebook.set(name)

    def _tab_tree(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.tree_tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            frame, text="目录结构", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.tree_hint = ctk.CTkLabel(
            frame,
            text="尚未解析文件，请先到“输入文件”页读取并解析。",
            text_color="#888888",
        )
        self.tree_hint.grid(row=1, column=0, sticky="w", pady=10)

        columns = ("章序", "字数")
        self.tree = ttk.Treeview(frame, columns=columns, show="tree headings")
        self.tree.heading("#0", text="卷 / 章")
        self.tree.heading("章序", text="章序")
        self.tree.heading("字数", text="字数")
        self.tree.column("#0", width=460)
        self.tree.column("章序", width=90, anchor="center")
        self.tree.column("字数", width=80, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.grid_remove()
        self.tree_scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree_scrollbar.grid_remove()

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="e", pady=(10, 0))
        self.next_output_btn = ctk.CTkButton(
            actions,
            text="下一步：输出",
            width=150,
            fg_color="gray55",
            hover_color="gray40",
            state=tk.DISABLED,
            command=lambda: self._select_tab("输出"),
        )
        self.next_output_btn.pack()

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        return frame

    def _update_step_buttons(self) -> None:
        theme = ctk.ThemeManager.theme["CTkButton"]
        ready = self.book is not None
        self.next_output_btn.configure(
            state=tk.NORMAL if ready else tk.DISABLED,
            fg_color=theme["fg_color"] if ready else "gray55",
            hover_color=theme["hover_color"] if ready else "gray40",
        )

    def _tab_settings(self) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(self.settings_tab, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.grid_columnconfigure(1, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        menu = ctk.CTkFrame(outer, width=170, corner_radius=8)
        menu.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        menu.grid_propagate(False)
        ctk.CTkLabel(
            menu, text="设置分组", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(12, 8))

        for group_title, _items in SETTING_GROUPS:
            btn = ctk.CTkButton(
                menu,
                text=group_title,
                anchor="w",
                height=36,
                fg_color="gray55",
                hover_color="gray40",
                command=lambda name=group_title: self._select_setting_group(name),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.group_buttons[group_title] = btn

        extra_btn = ctk.CTkButton(
            menu,
            text=EXTRA_GROUP,
            anchor="w",
            height=36,
            fg_color="gray55",
            hover_color="gray40",
            command=lambda name=EXTRA_GROUP: self._select_setting_group(name),
        )
        extra_btn.pack(fill="x", padx=10, pady=3)
        self.group_buttons[EXTRA_GROUP] = extra_btn

        self.settings_content = ctk.CTkFrame(outer, fg_color="transparent")
        self.settings_content.grid(row=0, column=1, sticky="nsew")
        self.settings_content.grid_columnconfigure(0, weight=1)
        self.settings_content.grid_rowconfigure(0, weight=1)

        for group_title, items in SETTING_GROUPS:
            frame = ctk.CTkFrame(self.settings_content, fg_color="transparent")
            scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
            scroll.pack(fill="both", expand=True)
            scroll.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                scroll,
                text=group_title,
                font=ctk.CTkFont(size=16, weight="bold"),
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 12))
            for r, (attr, label, multiline) in enumerate(items, start=1):
                ctk.CTkLabel(scroll, text=f"{label}：").grid(
                    row=r,
                    column=0,
                    sticky="nw" if multiline else "e",
                    padx=(4, 8),
                    pady=4,
                )
                tall_group = group_title in ("标题模板", "正文模板", "章节脚本")
                base_height = 130 if multiline else 76
                text_height = base_height if tall_group else base_height // 2
                text = ctk.CTkTextbox(scroll, height=text_height, wrap="word")
                text.grid(row=r, column=1, sticky="we", padx=(0, 4), pady=4)
                text.bind(
                    "<<Modified>>",
                    lambda _event, widget=text, group=group_title: self._on_text_modified(
                        widget, group
                    ),
                )
                self.text_widgets[attr] = text
            self.group_frames[group_title] = frame

        self.input_dir_var = tk.StringVar(value=str(self.input_dir))
        self.input_dir_var.trace_add("write", self._on_input_dir_changed)
        extra_frame = ctk.CTkFrame(self.settings_content, fg_color="transparent")
        scroll = ctk.CTkScrollableFrame(extra_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            scroll,
            text=EXTRA_GROUP,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 12))
        ctk.CTkLabel(scroll, text="输入目录：").grid(
            row=1, column=0, sticky="e", padx=(4, 8), pady=4
        )
        ctk.CTkEntry(scroll, textvariable=self.input_dir_var, height=34).grid(
            row=1, column=1, sticky="we", padx=(0, 4), pady=4
        )
        ctk.CTkButton(
            scroll,
            text="浏览...",
            width=90,
            command=self._browse_input_dir,
        ).grid(row=1, column=2, padx=(4, 0), pady=4)
        self.group_frames[EXTRA_GROUP] = extra_frame

        self.current_setting_group = SETTING_GROUPS[0][0]
        self.group_frames[self.current_setting_group].grid(
            row=0, column=0, sticky="nsew"
        )
        self._update_group_button_styles()

        buttons = ctk.CTkFrame(outer, fg_color="transparent")
        buttons.grid(row=1, column=0, columnspan=2, sticky="we", pady=(10, 0))
        ctk.CTkButton(
            buttons, text="保存当前内容", width=120, command=self._save_settings
        ).pack(side="left")
        ctk.CTkButton(
            buttons,
            text="重新载入",
            width=110,
            fg_color="gray55",
            hover_color="gray40",
            command=self._reload_settings,
        ).pack(side="left", padx=6)
        ctk.CTkLabel(
            buttons,
            text=f"设置目录：{SETTINGS_DIR}",
            text_color="#888888",
        ).pack(side="right")
        return outer

    def _select_setting_group(self, group: str) -> None:
        if group == self.current_setting_group:
            return
        if self.current_setting_group in self.group_frames:
            self.group_frames[self.current_setting_group].grid_remove()
        self.current_setting_group = group
        self.group_frames[group].grid(row=0, column=0, sticky="nsew")
        self._update_group_button_styles()

    def _update_group_button_styles(self) -> None:
        theme = ctk.ThemeManager.theme["CTkButton"]
        for name, btn in self.group_buttons.items():
            selected = name == self.current_setting_group
            btn.configure(
                fg_color=theme["fg_color"] if selected else "gray55",
                hover_color=theme["hover_color"] if selected else "gray40",
            )

    def _tab_output(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.output_tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            frame, text="输出", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        ctk.CTkLabel(frame, text="可选模板：").grid(
            row=1, column=0, sticky="nw", pady=4
        )
        self.avail_box = tk.Listbox(
            frame, height=9, selectmode=tk.EXTENDED, exportselection=False
        )
        for name in self.available_templates:
            self.avail_box.insert(tk.END, name)
        self.avail_box.grid(row=2, column=0, sticky="nsew", padx=(0, 6))

        move = ctk.CTkFrame(frame, fg_color="transparent")
        move.grid(row=2, column=1, padx=4)
        ctk.CTkButton(
            move, text="添加 ->", width=88, command=self._add_templates
        ).pack(fill="x", pady=2)
        ctk.CTkButton(
            move, text="<- 移除", width=88, command=self._remove_templates
        ).pack(fill="x", pady=2)
        ctk.CTkButton(
            move, text="上移", width=88, command=lambda: self._move(-1)
        ).pack(fill="x", pady=2)
        ctk.CTkButton(
            move, text="下移", width=88, command=lambda: self._move(1)
        ).pack(fill="x", pady=2)

        ctk.CTkLabel(frame, text="已选顺序：").grid(
            row=1, column=2, sticky="nw", pady=4
        )
        self.order_box = tk.Listbox(
            frame, height=9, selectmode=tk.EXTENDED, exportselection=False
        )
        self._refresh_order_box()
        self.order_box.grid(row=2, column=2, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(frame, text="输出目录：").grid(
            row=3, column=0, sticky="e", pady=8
        )
        self.output_var = tk.StringVar(value=str(self.output_root))
        self.output_var.trace_add("write", self._on_output_dir_changed)
        ctk.CTkEntry(frame, textvariable=self.output_var, height=34).grid(
            row=3, column=1, columnspan=2, sticky="we", padx=6
        )
        ctk.CTkButton(
            frame, text="浏览...", width=90, command=self._browse_output
        ).grid(row=3, column=3)

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.grid(row=4, column=0, columnspan=4, sticky="e", pady=(16, 0))
        self.build_btn = ctk.CTkButton(
            actions,
            text="输出 HTM",
            width=110,
            command=self._output,
            state=tk.DISABLED,
        )
        self.build_btn.pack(side="left", padx=4)
        self.compile_btn = ctk.CTkButton(
            actions,
            text="编译 CHM",
            width=110,
            command=self._compile,
            state=tk.DISABLED,
        )
        self.compile_btn.pack(side="left", padx=4)
        self.open_btn = ctk.CTkButton(
            actions,
            text="打开输出目录",
            width=120,
            command=self._open_output,
            state=tk.DISABLED,
        )
        self.open_btn.pack(side="left", padx=4)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(2, weight=1)
        return frame

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _on_close(self) -> None:
        try:
            input_path = self.input_dir_var.get().strip()
            if input_path:
                save_last_dirs(input_dir=input_path)
            output_path = self.output_var.get().strip()
            if output_path:
                save_last_dirs(output_dir=output_path)
        except Exception:
            pass
        self.root.destroy()

    def _browse_input_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=str(self.input_dir))
        if path:
            self.input_dir_var.set(path)
            self.input_dir = Path(path)
            save_last_dirs(input_dir=self.input_dir)

    def _on_input_dir_changed(self, *_args) -> None:
        value = self.input_dir_var.get().strip()
        self.input_dir = Path(value) if value else DEFAULT_BOOK_DIR

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self.input_dir),
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.file_var.set(path)
        book, author = extract_book_author(path)
        self.book_var.set(book)
        self.author_var.set(author)
        self._set_status(f"已载入：{Path(path).name}")

    def _parse_and_show(self) -> None:
        path = self.file_var.get().strip()
        book_name = self.book_var.get().strip()
        author = self.author_var.get().strip()
        if not path or not Path(path).is_file():
            messagebox.showwarning("提示", "请先选择有效的 txt 文件")
            return
        if not book_name or not author:
            messagebox.showwarning("提示", "请填写书名和作者")
            return
        try:
            self.book = parse_book(path, book_name, author)
        except Exception as exc:
            messagebox.showerror("解析失败", str(exc))
            return

        self.tree.delete(*self.tree.get_children())
        for volume in self.book.volumes:
            parent = self.tree.insert(
                "", "end", text=volume.name or "（无卷名）", open=True
            )
            for chapter in volume.chapters:
                self.tree.insert(
                    parent,
                    "end",
                    text=chapter.title,
                    values=(chapter.seq, chapter.word_count),
                )
        self.tree_hint.grid_remove()
        self.tree.grid()
        self.tree_scrollbar.grid()
        self.last_output_dir = None
        self.last_output_root = None
        self.last_chm = None
        self.compile_btn.configure(state=tk.DISABLED)
        self.open_btn.configure(state=tk.DISABLED)
        self.build_btn.configure(state=tk.NORMAL)
        self._set_status(
            f"解析完成：{len(self.book.volumes)} 卷，{len(self.book.chapters)} 章"
        )
        self._update_step_buttons()
        self._select_tab("目录结构")

    def _load_settings_into_widgets(self) -> None:
        self._loading_settings = True
        try:
            for attr, widget in self.text_widgets.items():
                widget.delete("1.0", tk.END)
                widget.insert("1.0", getattr(self.settings, attr))
                widget.edit_modified(False)
        finally:
            self._loading_settings = False
        self.dirty_groups.clear()

    def _mark_settings_dirty(self, group: str) -> None:
        if self._loading_settings:
            return
        self.dirty_groups.add(group)
        self._set_status(f"{group}：已修改，尚未保存")

    def _on_text_modified(self, widget: ctk.CTkTextbox, group: str) -> None:
        if not widget.edit_modified():
            return
        self._mark_settings_dirty(group)
        widget.edit_modified(False)

    def _save_settings(self) -> None:
        group = self.current_setting_group
        if not group or group not in self.group_frames:
            return
        if group == EXTRA_GROUP:
            self._set_status("输入目录修改后已自动保存")
            return
        attrs = [
            attr
            for group_title, items in SETTING_GROUPS
            if group_title == group
            for attr, _label, _multiline in items
        ]
        values = {
            attr: self.text_widgets[attr].get("1.0", "end-1c") for attr in attrs
        }
        try:
            save_settings(HPSettings(**values), SETTINGS_DIR, fields=attrs)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        for attr, value in values.items():
            setattr(self.settings, attr, value)
        self.dirty_groups.discard(group)
        self._set_status(f"{group}：已保存")
        messagebox.showinfo("设置", f"{group} 已保存到：\n{SETTINGS_DIR}")

    def _reload_settings(self) -> None:
        try:
            self.settings = HPSettings.load(SETTINGS_DIR)
        except Exception as exc:
            messagebox.showerror("读取失败", str(exc))
            return
        self._load_settings_into_widgets()
        self._set_status("已重新载入设置")

    def _refresh_order_box(self) -> None:
        self.order_box.delete(0, tk.END)
        for name in self.selected_templates:
            self.order_box.insert(tk.END, name)

    def _add_templates(self) -> None:
        added = False
        for index in self.avail_box.curselection():
            name = self.avail_box.get(index)
            if name not in self.selected_templates:
                self.selected_templates.append(name)
                added = True
        if not added:
            return
        self._refresh_order_box()
        save_template_order(self.selected_templates)

    def _remove_templates(self) -> None:
        remove = {self.order_box.get(i) for i in self.order_box.curselection()}
        remaining = [
            name for name in self.selected_templates if name not in remove
        ]
        if len(remaining) == len(self.selected_templates):
            return
        self.selected_templates = remaining
        self._refresh_order_box()
        save_template_order(self.selected_templates)

    def _move(self, delta: int) -> None:
        indexes = sorted(self.order_box.curselection())
        if not indexes:
            return
        names = list(self.selected_templates)
        moved = [names[i] for i in indexes]
        for i in reversed(indexes):
            names.pop(i)
        insert_at = max(0, min(len(names), indexes[0] + delta))
        for offset, name in enumerate(moved):
            names.insert(min(len(names), insert_at + offset), name)
        self.selected_templates = names
        self._refresh_order_box()
        for offset in range(len(moved)):
            self.order_box.selection_set(insert_at + offset)
        save_template_order(self.selected_templates)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(initialdir=str(self.output_root))
        if path:
            self.output_var.set(path)
            self.output_root = Path(path)
            save_last_dirs(output_dir=self.output_root)

    def _on_output_dir_changed(self, *_args) -> None:
        self.last_output_dir = None
        self.last_output_root = None
        self.last_chm = None
        self.compile_btn.configure(state=tk.DISABLED)
        self.open_btn.configure(state=tk.DISABLED)

    def _output(self) -> None:
        if self.book is None:
            messagebox.showwarning("提示", "请先在“输入文件”页读取并解析 txt")
            return
        if self.dirty_groups:
            messagebox.showwarning(
                "设置未保存",
                "以下设置尚未保存，请先到“设置”页保存：\n"
                + "、".join(sorted(self.dirty_groups)),
            )
            return
        if not self.selected_templates:
            messagebox.showwarning("提示", "请至少选择一个模板")
            return

        output_root = Path(self.output_var.get().strip() or str(self.output_root))
        self.build_btn.configure(state=tk.DISABLED)
        self.root.update_idletasks()
        try:
            self.last_output_dir = build_book(
                output_root, self.book, self.selected_templates, self.settings
            )
            self.last_output_root = output_root
            self.output_root = output_root
            save_last_dirs(output_dir=output_root)
            self._set_status(f"HTM 输出成功：{self.last_output_dir}")
            self.compile_btn.configure(state=tk.NORMAL)
            self.open_btn.configure(state=tk.NORMAL)
        except Exception as exc:
            messagebox.showerror("输出失败", str(exc))
            self._set_status(f"输出失败：{exc}")
        finally:
            self.build_btn.configure(state=tk.NORMAL)

    def _compile(self) -> None:
        if self.book is None or self.last_output_dir is None:
            messagebox.showwarning("提示", "请先输出 HTM")
            return
        if self.dirty_groups:
            messagebox.showwarning(
                "设置未保存",
                "以下设置尚未保存，请先到“设置”页保存：\n"
                + "、".join(sorted(self.dirty_groups)),
            )
            return
        output_root = self.last_output_root or Path(
            self.output_var.get().strip() or str(self.output_root)
        )
        self.compile_btn.configure(state=tk.DISABLED)
        self.root.update_idletasks()
        try:
            self.last_chm = compile_chm(
                output_root, self.book, self.settings, CHM_TOOL
            )
            self._set_status(f"CHM 编译成功：{self.last_chm}")
            messagebox.showinfo("完成", f"CHM 已生成：\n{self.last_chm}")
        except Exception as exc:
            messagebox.showerror("编译失败", str(exc))
            self._set_status(f"编译失败：{exc}")
        finally:
            self.compile_btn.configure(state=tk.NORMAL)

    def _open_output(self) -> None:
        if self.last_output_dir is not None:
            os.startfile(str(self.last_output_dir))  # type: ignore[attr-defined]


def run_gui() -> None:
    root = ctk.CTk()
    HpEbookApp(root)
    root.mainloop()
