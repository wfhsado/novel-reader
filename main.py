"""
小说摸鱼阅读器 - 主程序
一个可以在电脑上悬浮小窗阅读小说的工具
"""
import sys
import json
import os
import threading
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QSettings

from floating_window import FloatingWindow
from file_parser import FileParser


class NovelReaderApp:
    """小说阅读器应用"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 获取程序所在目录（支持打包后的exe）
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))

        # 配置文件路径（保存在程序同目录）
        self.config_dir = os.path.join(self.app_dir, "data")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.last_read_file = os.path.join(self.config_dir, "last_read.json")

        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)

        # 文件解析器
        self.parser = FileParser()

        # 创建悬浮窗
        self.window = FloatingWindow()
        self.window.parent = lambda: self  # 设置父级引用
        self.window.on_position_change = self._on_position_change  # 位置变化回调

        # 加载配置
        self._load_config()

        # 设置系统托盘
        self._setup_tray()

        # 设置全局快捷键
        self._setup_shortcuts()

        # 加载上次阅读的文件
        self._load_last_read()

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.window.resize(config.get('width', 400), config.get('height', 300))
                self.window.move(config.get('x', 100), config.get('y', 100))
                self.window.opacity_slider.setValue(config.get('opacity', 90))
                self.window.font_spin.setValue(config.get('font_size', 14))

    def _save_config(self):
        """保存配置"""
        config = {
            'width': self.window.width(),
            'height': self.window.height(),
            'x': self.window.x(),
            'y': self.window.y(),
            'opacity': self.window.opacity_slider.value(),
            'font_size': self.window.font_spin.value(),
            'last_file': getattr(self, 'current_file', '')
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _load_last_read(self):
        """加载上次阅读进度"""
        if os.path.exists(self.last_read_file):
            with open(self.last_read_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_path = data.get('file_path', '')
                line = data.get('line', 0)

                if file_path and os.path.exists(file_path):
                    self.load_novel(file_path, line)

    def _save_last_read(self):
        """保存阅读进度"""
        if not getattr(self, 'current_file', ''):
            return
        pos = self.window.get_current_position()
        data = {
            'file_path': self.current_file,
            'line': pos['line'],
            'chapter': pos['chapter']
        }
        with open(self.last_read_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _on_position_change(self):
        """阅读位置变化时自动保存"""
        self._save_last_read()

    def _setup_tray(self):
        """设置系统托盘图标"""
        # 创建一个简单的图标（使用应用默认图标）
        self.tray = QSystemTrayIcon(self.app)

        # 托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示窗口", self.tray)
        show_action.triggered.connect(self.window.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("隐藏窗口", self.tray)
        hide_action.triggered.connect(self.window.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self.tray)
        quit_action.triggered.connect(self._quit)
        tray_menu.addAction(quit_action)

        self.tray.setContextMenu(tray_menu)
        self.tray.setToolTip("小说摸鱼阅读器")
        self.tray.activated.connect(self._tray_activated)

        # 显示托盘图标（如果有图标的话）
        # self.tray.show()

    def _tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.window.show()

    def _setup_shortcuts(self):
        """设置全局快捷键"""
        try:
            import keyboard
            # Ctrl+Tab: 恢复/显示窗口
            keyboard.add_hotkey('ctrl+tab', self._toggle_window)
            # Ctrl+H: 隐藏/显示窗口
            keyboard.add_hotkey('ctrl+h', self._toggle_window)
        except ImportError:
            print("keyboard库未安装，全局快捷键不可用")
        except Exception as e:
            print(f"设置全局快捷键失败: {e}")

    def _toggle_window(self):
        """切换窗口显示/隐藏"""
        if self.window.isVisible():
            if self.window.isMinimized():
                self.window.showNormal()
                self.window.activateWindow()
            else:
                self.window.hide()
        else:
            self.window.show()
            self.window.activateWindow()

    def load_novel(self, file_path: str, start_line: int = 0):
        """
        加载小说文件

        Args:
            file_path: 文件路径
            start_line: 起始行号
        """
        try:
            # 解析文件
            content, chapters = self.parser.parse_file(file_path)

            # 更新窗口标题
            file_name = os.path.basename(file_path)
            self.window.setWindowTitle(file_name)

            # 加载内容
            self.window.load_content(content, chapters)

            # 跳转到指定位置
            if start_line > 0:
                self.window.go_to_line(start_line)

            self.current_file = file_path
            self.window.show()

            # 保存阅读进度
            self._save_last_read()

        except Exception as e:
            print(f"加载文件失败: {e}")

    def _quit(self):
        """退出程序"""
        self._save_config()
        self._save_last_read()
        self.app.quit()

    def run(self):
        """运行应用"""
        self.window.show()

        # 处理窗口关闭事件
        self.app.aboutToQuit.connect(self._save_config)

        return self.app.exec_()


def main():
    """主函数"""
    # 检查是否有命令行参数（文件路径）
    reader = NovelReaderApp()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            reader.load_novel(file_path)

    sys.exit(reader.run())


if __name__ == '__main__':
    main()
