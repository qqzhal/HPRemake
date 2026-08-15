# HP电子书制作软件 v3.2（Python 重制）

本项目由 OpenAI Codex 驱动、DeepSeek Flash v4（deepseek-v4-flash）模型生成。

本项目用 Python 重新实现原版“HP电子书制作软件 v3.2”的核心流程：

1. 读取 txt 文件，按“卷名与章节名之间空 2 行以上、章节与章节之间空 2 行以上”的结构解析卷章。
2. 自动从文件名识别书名和作者，也支持手动指定。
3. 按原版规则生成章节 txt、`js/page.js`、`js/chapter.js`、`js/mb.js`、`start.htm` 和多模板目录。
4. 生成 `temp.hhp` 并调用 `chm\hhc.exe` 编译 CHM。

程序所需的模板、参数和 CHM 编译器都已放在本目录内，整个 `python` 目录可以整体复制或移动到其他位置独立使用。

## 运行

图形界面：

```powershell
cd python
python main.py
```

也可以直接双击 `启动HP电子书制作软件.bat`，启动脚本会自动检查并安装依赖。

命令行：

```powershell
cd python
python main.py --file "book\极品家丁 禹言.txt" --compile
```

可指定模板与输出目录：

```powershell
python main.py --file book\书稿.txt --templates 默认模板 起点中文 --output Ebook --compile
```

## 依赖

图形界面使用 `customtkinter` 美化。依赖清单见 `requirements.txt`，首次运行前手动安装一次即可：

```powershell
cd python
python -m pip install -r requirements.txt
```

## 打包为 exe

代码已兼容 PyInstaller 打包。打包后请保持资源目录与 exe 同级，程序会自动以 exe 所在目录为项目根目录：

```text
dist/
├─ HP电子书制作软件.exe
├─ template/
├─ chm/
├─ book/
├─ settings/
└─ Ebook/
```

```powershell
# 1. 安装 PyInstaller
python -m pip install pyinstaller

# 2. 打包（onedir 模式，不弹出控制台窗口）
python -m PyInstaller --noconfirm --onedir --noconsole --name "HP电子书制作软件" main.py
```

打包完成后，exe 位于 `dist\HP电子书制作软件\`。把 `template`、`chm`、`book`、`settings`、`Ebook` 目录复制到 exe 旁边即可独立使用：

```powershell
$dest = "D:\HPRemake"
Copy-Item -LiteralPath "dist\HP电子书制作软件\HP电子书制作软件.exe" -Destination $dest
Copy-Item -LiteralPath "dist\HP电子书制作软件\_internal" -Destination $dest -Recurse
foreach ($name in @("template", "chm", "book", "settings", "Ebook")) {
    Copy-Item -LiteralPath $name -Destination $dest -Recurse
}
```

以后重新打包可以复用已有的打包配置：

```powershell
python -m PyInstaller "HP电子书制作软件.spec" --noconfirm
```

注意：若环境里装过 Python 2 时代残留的 `pathlib` 包，PyInstaller 会报错，先卸载它再打包：

```powershell
python -m pip uninstall -y pathlib
```

打包后的 exe 同样支持命令行构建：`HP电子书制作软件.exe --file "book\书稿.txt" --output Ebook --compile`。`settings` 缺失时仍会自动重建。

## 参数

模板位于本目录 `template`，可编辑参数位于 `settings`（从原版 `源文件\HP面板设置` 复制而来），图形界面中可直接修改“制作 / 版权 / 链接”。`settings` 被误删或文件缺失时，程序会在启动时从内置备份自动重建，不影响运行。

## 说明

- 正文排版、字数统计、目录序号、模板替换均按原版易语言源码行为实现。
- 输出目录已存在时会自动清空重建，请勿把书稿源文件放在输出目录内。
- 编译 CHM 依赖 `chm\hhc.exe`。
- 默认输入目录为 `book`，默认输出目录为 `Ebook`，均位于本目录内。
