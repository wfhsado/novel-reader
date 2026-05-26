"""
章节识别模块
支持多种章节格式的自动识别
"""
import re
from typing import List, Tuple


class ChapterParser:
    """章节解析器"""

    # 常见章节格式
    CHAPTER_PATTERNS = [
        # 中文格式：第X章、第X回、第X节、第X卷
        r'^第[零一二三四五六七八九十百千万\d]+[章回节卷篇幕集部]',
        # 数字格式：001.、01、1、
        r'^\d{1,4}[\.、\.．\s]',
        # 英文格式：Chapter X、CHAPTER X
        r'^(Chapter|CHAPTER|Chapter)\s+\d+',
        # 特殊格式：【第X章】
        r'^【第[零一二三四五六七八九十百千万\d]+[章回节卷]】',
        # 分隔线格式
        r'^[─━═]{5,}$',
        r'^\*{3,}$',
        r'^#{3,}$',
    ]

    def __init__(self):
        self.chapters: List[Tuple[int, str]] = []  # (位置, 标题)

    def parse(self, content: str) -> List[Tuple[int, str]]:
        """
        解析文本内容，识别章节位置

        Args:
            content: 小说文本内容

        Returns:
            章节列表，每个元素为 (字符位置, 章节标题)
        """
        self.chapters = []
        lines = content.split('\n')

        current_pos = 0
        for line in lines:
            line_stripped = line.strip()

            # 跳过空行
            if not line_stripped:
                current_pos += len(line) + 1  # +1 for newline
                continue

            # 检查是否匹配章节格式
            if self._is_chapter(line_stripped):
                self.chapters.append((current_pos, line_stripped))

            current_pos += len(line) + 1

        return self.chapters

    def _is_chapter(self, line: str) -> bool:
        """判断一行是否是章节标题"""
        for pattern in self.CHAPTER_PATTERNS:
            if re.match(pattern, line):
                return True
        return False

    def get_chapter_content(self, content: str, chapter_index: int, next_chapter_pos: int = None) -> str:
        """
        获取指定章节的内容

        Args:
            content: 完整文本
            chapter_index: 章节索引
            next_chapter_pos: 下一章位置，如果为None则取到文末

        Returns:
            章节内容文本
        """
        if chapter_index < 0 or chapter_index >= len(self.chapters):
            return ""

        start_pos = self.chapters[chapter_index][0]

        if next_chapter_pos is None:
            if chapter_index + 1 < len(self.chapters):
                next_chapter_pos = self.chapters[chapter_index + 1][0]
            else:
                next_chapter_pos = len(content)

        return content[start_pos:next_chapter_pos]

    def detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码

        Args:
            file_path: 文件路径

        Returns:
            编码名称
        """
        # 尝试常见编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'utf-16']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(10000)  # 读取前10000字符测试
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue

        return 'utf-8'  # 默认


if __name__ == '__main__':
    # 测试章节识别
    test_text = """
第一章 初入江湖

    那是一个风雨交加的夜晚，少年背着包袱，独自走在山路上。

第二章 奇遇

    山洞中，少年发现了一本古老的秘籍。

第三章 习武

    少年开始日夜修炼，终于有所小成。

001. 序章

故事从这里开始。

002. 起源

一切的起源。
"""
    parser = ChapterParser()
    chapters = parser.parse(test_text)

    print("识别到的章节：")
    for pos, title in chapters:
        print(f"  位置 {pos}: {title}")
