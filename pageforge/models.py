"""PageForge Studio 敏感词预审定位库：数据模型。

词库与扫描数据均只保存在内存中。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LexiconEntry:
    """词条：唯一标识 + 原始文字。"""

    entry_id: str
    text: str


@dataclass(frozen=True)
class TextFragment:
    """文本片段：编辑器中的一个文本节点。

    text 为编辑器中的原文，相邻片段之间不隐含任何字符。
    """

    node_id: str
    text: str


@dataclass(frozen=True)
class TextBlock:
    """文本块：按阅读顺序排列的片段序列。命中绝不跨块。"""

    fragments: tuple[TextFragment, ...] = ()


@dataclass(frozen=True)
class NodeRange:
    """单个节点上的高亮区间，偏移按原文 Unicode 码点计，左闭右开。"""

    node_id: str
    start: int
    end: int


@dataclass(frozen=True)
class Hit:
    """一条命中：关联词条及用于高亮的各节点区间（按阅读顺序）。"""

    entry_id: str
    entry_text: str
    ranges: tuple[NodeRange, ...] = field(default_factory=tuple)
