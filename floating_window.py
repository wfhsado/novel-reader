"""
悬浮小窗模块
实现可置顶、可调节透明度的迷你阅读窗口
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QSlider, QFileDialog,
    QComboBox, QSpinBox, QMenu, QAction, QApplication,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QFont, QColor, QCursor


class FloatingWindow(QWidget):
    """悬浮小窗"""

    def __init__(self):
        super().__init__()

        # 窗口配置
        self.window_width = 400
        self.window_height = 300
        self.opacity = 0.9
        self.font_size = 14
        self.always_on_top = True

        # 阅读状态
        self.content = ""
        self.chapters = []
        self.current_chapter = 0
        self.current_pos = 0
        self.lines_per_page = 15  # 每页显示行数
        self.all_lines = []

        # 拖动相关
        self.drag_position = None

        # 位置变化回调
        self.on_position_change = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(self.opacity)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # 标题栏
        title_bar = QHBoxLayout()

        self.title_label = QLabel("小说摸鱼阅读器")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                padding: 2px;
            }
        """)
        title_bar.addWidget(self.title_label)

        # 最小化按钮
        btn_minimize = QPushButton("—")
        btn_minimize.setFixedSize(20, 20)
        btn_minimize.setStyleSheet(self._button_style())
        btn_minimize.clicked.connect(self.showMinimized)
        title_bar.addWidget(btn_minimize)

        # 关闭按钮
        btn_close = QPushButton("×")
        btn_close.setFixedSize(20, 20)
        btn_close.setStyleSheet(self._button_style("#ff5555"))
        btn_close.clicked.connect(self.close)
        title_bar.addWidget(btn_close)

        layout.addLayout(title_bar)

        # 章节目录面板（默认隐藏）
        self.chapter_panel = QListWidget()
        self.chapter_panel.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 30, 30, 230);
                color: #d4d4d4;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #4a9eff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)
        self.chapter_panel.itemClicked.connect(self._on_chapter_selected)
        self.chapter_panel.hide()  # 默认隐藏
        layout.addWidget(self.chapter_panel)

        # 阅读区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 30, 230);
                color: #d4d4d4;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
            }
        """)
        self.text_display.setFont(QFont("Microsoft YaHei", self.font_size))
        self.text_display.installEventFilter(self)  # 安装事件过滤器
        layout.addWidget(self.text_display)

        # 控制栏
        control_bar = QHBoxLayout()

        # 章节目录按钮
        self.btn_chapter_list = QPushButton("目录")
        self.btn_chapter_list.setFixedSize(35, 25)
        self.btn_chapter_list.setStyleSheet(self._button_style("#4a9eff"))
        self.btn_chapter_list.clicked.connect(self.toggle_chapter_panel)
        control_bar.addWidget(self.btn_chapter_list)

        # 上一章
        btn_prev_chapter = QPushButton("◀章")
        btn_prev_chapter.setFixedSize(35, 25)
        btn_prev_chapter.setStyleSheet(self._button_style())
        btn_prev_chapter.clicked.connect(self.prev_chapter)
        control_bar.addWidget(btn_prev_chapter)

        # 上一页
        btn_prev = QPushButton("◀")
        btn_prev.setFixedSize(25, 25)
        btn_prev.setStyleSheet(self._button_style())
        btn_prev.clicked.connect(self.prev_page)
        control_bar.addWidget(btn_prev)

        # 页码显示
        self.page_label = QLabel("0/0")
        self.page_label.setStyleSheet("color: #aaa; font-size: 10px;")
        self.page_label.setAlignment(Qt.AlignCenter)
        control_bar.addWidget(self.page_label)

        # 下一页
        btn_next = QPushButton("▶")
        btn_next.setFixedSize(25, 25)
        btn_next.setStyleSheet(self._button_style())
        btn_next.clicked.connect(self.next_page)
        control_bar.addWidget(btn_next)

        # 下一章
        btn_next_chapter = QPushButton("章▶")
        btn_next_chapter.setFixedSize(35, 25)
        btn_next_chapter.setStyleSheet(self._button_style())
        btn_next_chapter.clicked.connect(self.next_chapter)
        control_bar.addWidget(btn_next_chapter)

        layout.addLayout(control_bar)

        # 底部工具栏
        tool_bar = QHBoxLayout()

        # 打开文件按钮
        btn_open = QPushButton("打开")
        btn_open.setFixedSize(40, 22)
        btn_open.setStyleSheet(self._button_style("#4a9eff"))
        btn_open.clicked.connect(self.open_file)
        tool_bar.addWidget(btn_open)

        # 背景模式选择
        bg_label = QLabel("背景:")
        bg_label.setStyleSheet("color: #aaa; font-size: 10px;")
        tool_bar.addWidget(bg_label)

        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["透明", "米色", "深色"])
        self.bg_combo.setFixedWidth(55)
        self.bg_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
                font-size: 10px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #e0e0e0;
                selection-background-color: #4a9eff;
            }
        """)
        self.bg_combo.currentTextChanged.connect(self.change_background)
        tool_bar.addWidget(self.bg_combo)

        # 透明度滑块
        opacity_label = QLabel("透明:")
        opacity_label.setStyleSheet("color: #aaa; font-size: 10px;")
        tool_bar.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(int(self.opacity * 100))
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        tool_bar.addWidget(self.opacity_slider)

        # 字号调节
        font_label = QLabel("字号:")
        font_label.setStyleSheet("color: #aaa; font-size: 10px;")
        tool_bar.addWidget(font_label)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setFixedWidth(50)
        self.font_spin.valueChanged.connect(self.change_font_size)
        tool_bar.addWidget(self.font_spin)

        layout.addLayout(tool_bar)

        # 设置初始大小和位置
        self.resize(self.window_width, self.window_height)
        self.move(100, 100)

        # 快捷键提示
        self._setup_shortcuts()

    def _button_style(self, hover_color="#666"):
        """按钮样式"""
        return f"""
            QPushButton {{
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: #2a2a2a;
            }}
        """

    def _setup_shortcuts(self):
        """设置快捷键提示"""
        # 在标题显示快捷键提示
        self.title_label.setText("小说摸鱼阅读器 | Ctrl+H隐藏 | Shift+拖动 | Ctrl+滚轮调大小")

    def load_content(self, content: str, chapters: list):
        """
        加载小说内容

        Args:
            content: 全文内容
            chapters: 章节列表 [(位置, 标题), ...]
        """
        self.content = content
        self.chapters = chapters
        self.all_lines = content.split('\n')

        # 更新章节目录
        self._update_chapter_list()

        if chapters:
            self.current_chapter = 0
            self.current_pos = chapters[0][0]
            self._display_chapter(0)
        else:
            self.current_pos = 0
            self._display_from_pos(0)

    def _update_chapter_list(self):
        """更新章节目录列表"""
        self.chapter_panel.clear()
        for i, (pos, title) in enumerate(self.chapters):
            self.chapter_panel.addItem(f"{i+1}. {title}")

    def toggle_chapter_panel(self):
        """切换章节目录面板显示/隐藏"""
        if self.chapter_panel.isVisible():
            self.chapter_panel.hide()
            self.btn_chapter_list.setStyleSheet(self._button_style("#4a9eff"))
        else:
            self.chapter_panel.show()
            self.btn_chapter_list.setStyleSheet(self._button_style("#ff9900"))
            # 滚动到当前章节
            if self.current_chapter < self.chapter_panel.count():
                self.chapter_panel.setCurrentRow(self.current_chapter)

    def _on_chapter_selected(self, item):
        """点击章节目录项"""
        index = self.chapter_panel.row(item)
        self._display_chapter(index)
        self.chapter_panel.hide()
        self.btn_chapter_list.setStyleSheet(self._button_style("#4a9eff"))

    def _display_chapter(self, chapter_index: int):
        """显示指定章节"""
        if not self.chapters or chapter_index < 0 or chapter_index >= len(self.chapters):
            return

        self.current_chapter = chapter_index

        # 计算章节在行数组中的位置
        pos = self.chapters[chapter_index][0]
        line_num = self.content[:pos].count('\n')

        # 计算下一章位置
        if chapter_index + 1 < len(self.chapters):
            next_pos = self.chapters[chapter_index + 1][0]
            end_line = self.content[:next_pos].count('\n')
        else:
            end_line = len(self.all_lines)

        # 更新标题
        chapter_title = self.chapters[chapter_index][1]
        self.title_label.setText(f"{chapter_title} | Ctrl+H隐藏")

        # 显示内容
        start = line_num
        end = min(start + self.lines_per_page, end_line)
        self._show_lines(start, end)

    def _display_from_pos(self, line_num: int):
        """从指定行开始显示"""
        end = min(line_num + self.lines_per_page, len(self.all_lines))
        self._show_lines(line_num, end)

    def _show_lines(self, start: int, end: int):
        """显示指定范围的行"""
        self.current_pos = start
        text = '\n'.join(self.all_lines[start:end])
        self.text_display.setText(text)

        # 更新页码
        total_pages = len(self.all_lines) // self.lines_per_page + 1
        current_page = start // self.lines_per_page + 1
        self.page_label.setText(f"{current_page}/{total_pages}")

        # 更新章节信息
        self._update_chapter_info(start)

        # 触发位置变化回调
        if self.on_position_change:
            self.on_position_change()

    def _update_chapter_info(self, current_line: int):
        """更新当前章节信息"""
        if not self.chapters:
            return

        # 找到当前行所在的章节
        for i in range(len(self.chapters) - 1, -1, -1):
            chap_pos = self.chapters[i][0]
            chap_line = self.content[:chap_pos].count('\n')
            if current_line >= chap_line:
                if i != self.current_chapter:
                    self.current_chapter = i
                    chapter_title = self.chapters[i][1]
                    self.title_label.setText(f"{chapter_title} | Ctrl+H隐藏")
                break

    def next_page(self):
        """下一页"""
        next_pos = self.current_pos + self.lines_per_page

        # 正常翻页
        if next_pos < len(self.all_lines):
            self._display_from_pos(next_pos)
        elif self.chapters and self.current_chapter + 1 < len(self.chapters):
            # 已经到文末，但还有下一章
            self._display_chapter(self.current_chapter + 1)

    def prev_page(self):
        """上一页"""
        prev_pos = self.current_pos - self.lines_per_page

        if prev_pos >= 0:
            self._display_from_pos(prev_pos)
        elif self.chapters and self.current_chapter > 0:
            # 已经到文首，但还有上一章
            self._display_chapter(self.current_chapter - 1)

    def next_chapter(self):
        """下一章"""
        if self.current_chapter + 1 < len(self.chapters):
            self._display_chapter(self.current_chapter + 1)

    def prev_chapter(self):
        """上一章"""
        if self.current_chapter > 0:
            self._display_chapter(self.current_chapter - 1)

    def open_file(self):
        """打开文件对话框"""
        from file_parser import FileParser
        parser = FileParser()

        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开小说文件", "",
            parser.get_file_filter()
        )
        if file_path:
            # 通过信号通知主窗口
            self.parent().load_novel(file_path)

    def change_opacity(self, value: int):
        """改变透明度"""
        self.opacity = value / 100
        self.setWindowOpacity(self.opacity)

    def change_font_size(self, size: int):
        """改变字号"""
        self.font_size = size
        self.text_display.setFont(QFont("Microsoft YaHei", size))

    def change_background(self, mode: str):
        """改变背景模式"""
        if mode == "透明":
            self.text_display.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(30, 30, 30, 230);
                    color: #d4d4d4;
                    border: 1px solid #444;
                    border-radius: 5px;
                    padding: 8px;
                    font-family: "Microsoft YaHei", "SimSun", sans-serif;
                }
            """)
        elif mode == "米色":
            self.text_display.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(255, 253, 240, 240);
                    color: #333333;
                    border: 1px solid #d4c5a9;
                    border-radius: 5px;
                    padding: 8px;
                    font-family: "Microsoft YaHei", "SimSun", sans-serif;
                }
            """)
        elif mode == "深色":
            self.text_display.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(30, 30, 30, 250);
                    color: #d4d4d4;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 8px;
                    font-family: "Microsoft YaHei", "SimSun", sans-serif;
                }
            """)

    def get_current_position(self) -> dict:
        """获取当前阅读位置信息"""
        return {
            'line': self.current_pos,
            'chapter': self.current_chapter
        }

    def go_to_line(self, line_num: int):
        """跳转到指定行"""
        if 0 <= line_num < len(self.all_lines):
            self._display_from_pos(line_num)

    def eventFilter(self, obj, event):
        """事件过滤器：让QTextEdit也能响应Shift+拖动"""
        if obj == self.text_display:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.setCursor(Qt.ClosedHandCursor)
                    return True
            elif event.type() == event.MouseMove:
                if self.drag_position and event.buttons() == Qt.LeftButton:
                    self.move(event.globalPos() - self.drag_position)
                    return True
            elif event.type() == event.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.drag_position = None
                    self.setCursor(Qt.ArrowCursor)
                    return True
        return super().eventFilter(obj, event)

    # 鼠标拖动支持（按住Shift键拖动）
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        """鼠标滚轮：Ctrl+滚轮调整大小，滚轮翻页"""
        if event.modifiers() == Qt.ControlModifier:
            # Ctrl+滚轮：调整窗口大小
            delta = event.angleDelta().y()
            current_width = self.width()
            current_height = self.height()

            if delta > 0:
                # 放大
                new_width = min(current_width + 30, 1200)
                new_height = min(current_height + 20, 900)
            else:
                # 缩小
                new_width = max(current_width - 30, 250)
                new_height = max(current_height - 20, 150)

            self.resize(new_width, new_height)
            # 根据窗口大小调整每页行数
            self.lines_per_page = max(5, (new_height - 120) // 20)
        else:
            # 普通滚轮：翻页
            if event.angleDelta().y() > 0:
                self.prev_page()
            else:
                self.next_page()
        event.accept()
