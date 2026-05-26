# 小说摸鱼阅读器

一个轻量级的小说阅读工具，以悬浮小窗形式运行，适合在工作时"摸鱼"看小说。

## 下载使用

### 方式一：直接下载exe（推荐）

前往 [Releases](https://github.com/wfhsado/novel-reader/releases) 页面下载最新版本。

下载后双击 `NovelReader.exe` 即可运行。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/wfhsado/novel-reader.git
cd novel-reader

# 安装依赖
pip install PyQt5

# 运行程序
python main.py
```

## 功能特点

- **悬浮小窗**：始终置顶，可自由拖动
- **智能分章**：自动识别"第X章"等章节格式
- **透明度调节**：从20%到100%自由调整
- **字号调节**：10-24号字体可选
- **老板键**：Ctrl+H 快速隐藏窗口
- **滚轮翻页**：鼠标滚轮上下翻页
- **位置记忆**：自动保存阅读进度，精确到行
- **便携版**：配置文件跟随程序，U盘随走随用

## 使用说明

### 基本操作

| 操作 | 说明 |
|------|------|
| **Shift+拖动** | 按住Shift键拖动窗口移动 |
| **Ctrl+H** | 快速隐藏/显示窗口 |
| **鼠标滚轮** | 上下翻页 |
| **打开按钮** | 选择txt小说文件 |

### 界面按钮

- **◀章 / 章▶**：上一章/下一章
- **◀ / ▶**：上一页/下一页
- **打开**：选择小说文件
- **透明**：调节窗口透明度
- **字号**：调节字体大小

## 章节识别

支持以下格式：
- `第X章`、`第X回`、`第X节`、`第X卷`
- 数字格式：`001.`、`01.`、`1.`
- 英文格式：`Chapter X`、`CHAPTER X`
- 分隔线格式：`────`、`****`

## 文件说明

```
novel-reader/
├── main.py              # 主程序
├── chapter_parser.py    # 章节识别模块
├── floating_window.py   # 悬浮窗UI
├── build.bat            # 打包脚本
├── install.bat          # 安装依赖
├── start.bat            # 启动脚本
└── test_novel.txt       # 测试小说
```

## 自己打包

```bash
# 安装打包工具
pip install pyinstaller

# 运行打包脚本
build.bat
```

打包后的exe在 `dist/` 目录下。

## 技术栈

- Python 3.12
- PyQt5
- PyInstaller（打包）

## 许可证

MIT License

## 问题反馈

如果遇到问题或有建议，欢迎提交 [Issue](https://github.com/wfhsado/novel-reader/issues)。
