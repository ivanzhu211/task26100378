"""PageForge Studio 门面：整体替换词库、扫描页面。仅内存存储。"""

from __future__ import annotations

from .models import Hit, LexiconEntry, TextBlock
from .scanner import scan_blocks


class PageForgeStudio:
    """敏感词预审定位库入口。"""

    def __init__(self) -> None:
        self._entries: list[LexiconEntry] = []

    def replace_lexicon(self, entries: list[LexiconEntry]) -> None:
        """整体替换词库；后续扫描只使用新词库。"""
        self._entries = list(entries)

    def scan(self, blocks: list[TextBlock]) -> list[Hit]:
        """扫描页面（按阅读顺序排列的文本块），返回完整命中清单。"""
        return scan_blocks(self._entries, blocks)
