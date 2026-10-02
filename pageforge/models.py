"""Data types for PageForge Studio sensitive-word pre-screening."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WordEntry:
    """A sensitive-word entry with a unique id and its original text."""

    entry_id: str
    text: str


@dataclass(frozen=True)
class TextFragment:
    """A text fragment inside a block; text is the raw editor content."""

    node_id: str
    text: str


@dataclass(frozen=True)
class TextBlock:
    """A text block in reading order; matches never cross block boundaries."""

    fragments: tuple[TextFragment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class NodeRange:
    """A highlight range on one node, in original Unicode code points, [start, end)."""

    node_id: str
    start: int
    end: int


@dataclass(frozen=True)
class ScanHit:
    """One reported hit: the matched entry plus per-node highlight ranges."""

    entry_id: str
    block_index: int
    ranges: tuple[NodeRange, ...]
