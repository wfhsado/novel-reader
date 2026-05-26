"""
文件解析模块
支持多种小说格式：txt, epub, mobi, pdf
"""
import re
import os
import zipfile
from typing import List, Tuple


class FileParser:
    """文件解析器"""

    # 支持的文件格式
    SUPPORTED_FORMATS = {
        '.txt': 'text/plain',
        '.epub': 'application/epub+zip',
        '.mobi': 'application/x-mobipocket-ebook',
        '.pdf': 'application/pdf',
    }

    # 章节识别模式
    CHAPTER_PATTERNS = [
        # 中文格式
        r'^第[零一二三四五六七八九十百千万\d]+[章回节卷篇幕集部]',
        # 数字格式
        r'^\d{1,4}[\.、\.．\s]',
        # 英文格式
        r'^(Chapter|CHAPTER|Chapter)\s+\d+',
        # 特殊格式
        r'^【第[零一二三四五六七八九十百千万\d]+[章回节卷]】',
        # 分隔线格式
        r'^[─━═]{5,}$',
        r'^\*{3,}$',
        r'^#{3,}$',
    ]

    def __init__(self):
        self.content = ""
        self.chapters = []
        self.encoding = 'utf-8'

    def parse_file(self, file_path: str) -> Tuple[str, List[Tuple[int, str]]]:
        """
        解析文件，返回内容和章节列表

        Args:
            file_path: 文件路径

        Returns:
            (内容文本, 章节列表)
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.txt':
            return self._parse_txt(file_path)
        elif ext == '.epub':
            return self._parse_epub(file_path)
        elif ext == '.mobi':
            return self._parse_mobi(file_path)
        elif ext == '.pdf':
            return self._parse_pdf(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def _parse_txt(self, file_path: str) -> Tuple[str, List[Tuple[int, str]]]:
        """解析TXT文件"""
        self.encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=self.encoding) as f:
            self.content = f.read()

        self.chapters = self._find_chapters(self.content)
        return self.content, self.chapters

    def _parse_epub(self, file_path: str) -> Tuple[str, List[Tuple[int, str]]]:
        """解析EPUB文件"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("解析EPUB需要安装依赖: pip install ebooklib beautifulsoup4")

        book = epub.read_epub(file_path)
        content_parts = []
        chapters = []
        current_pos = 0

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()

                # 尝试识别章节标题
                title = self._extract_epub_title(soup)
                if title:
                    chapters.append((current_pos, title))

                content_parts.append(text)
                current_pos += len(text) + 1  # +1 for newline

        self.content = '\n'.join(content_parts)

        # 如果没有从EPUB结构识别到章节，尝试从文本内容识别
        if not chapters:
            self.chapters = self._find_chapters(self.content)
        else:
            self.chapters = chapters

        return self.content, self.chapters

    def _extract_epub_title(self, soup) -> str:
        """从EPUB HTML中提取标题"""
        # 尝试从h1-h6标签提取
        for tag in ['h1', 'h2', 'h3']:
            title_tag = soup.find(tag)
            if title_tag:
                return title_tag.get_text().strip()

        # 尝试从title标签提取
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        return ""

    def _parse_mobi(self, file_path: str) -> Tuple[str, List[Tuple[int, str]]]:
        """解析MOBI文件"""
        try:
            import mobi
        except ImportError:
            raise ImportError("解析MOBI需要安装依赖: pip install mobi")

        # mobi库解析
        tempdir, filepath = mobi.extract(file_path)
        html_path = os.path.join(tempdir, filepath)

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 简单的HTML到文本转换
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', '\n', text).strip()

        self.content = text
        self.chapters = self._find_chapters(self.content)

        # 清理临时文件
        import shutil
        shutil.rmtree(tempdir, ignore_errors=True)

        return self.content, self.chapters

    def _parse_pdf(self, file_path: str) -> Tuple[str, List[Tuple[int, str]]]:
        """解析PDF文件"""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("解析PDF需要安装依赖: pip install PyPDF2")

        content_parts = []
        chapters = []
        current_pos = 0

        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    # 尝试识别章节标题
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if self._is_chapter(line):
                            chapters.append((current_pos, line))

                    content_parts.append(text)
                    current_pos += len(text) + 1

        self.content = '\n'.join(content_parts)

        # 如果没有从PDF结构识别到章节，尝试从文本内容识别
        if not chapters:
            self.chapters = self._find_chapters(self.content)
        else:
            self.chapters = chapters

        return self.content, self.chapters

    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'utf-16']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(10000)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue

        return 'utf-8'

    def _find_chapters(self, content: str) -> List[Tuple[int, str]]:
        """在文本中查找章节"""
        chapters = []
        lines = content.split('\n')
        current_pos = 0

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                current_pos += len(line) + 1
                continue

            if self._is_chapter(line_stripped):
                chapters.append((current_pos, line_stripped))

            current_pos += len(line) + 1

        return chapters

    def _is_chapter(self, line: str) -> bool:
        """判断是否是章节标题"""
        for pattern in self.CHAPTER_PATTERNS:
            if re.match(pattern, line):
                return True
        return False

    def get_supported_formats(self) -> str:
        """获取支持的文件格式过滤器"""
        formats = []
        for ext, mime in self.SUPPORTED_FORMATS.items():
            formats.append(f"*{ext}")
        return " ".join(formats)

    def get_file_filter(self) -> str:
        """获取文件选择对话框的过滤器"""
        return (
            f"小说文件 ({self.get_supported_formats()});;"
            "文本文件 (*.txt);;"
            "EPUB文件 (*.epub);;"
            "MOBI文件 (*.mobi);;"
            "PDF文件 (*.pdf);;"
            "所有文件 (*)"
        )


if __name__ == '__main__':
    # 测试
    parser = FileParser()
    print("支持的格式:", list(parser.SUPPORTED_FORMATS.keys()))
    print("文件过滤器:", parser.get_file_filter())
