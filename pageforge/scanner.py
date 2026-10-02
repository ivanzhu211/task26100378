"""In-memory scanner: replaceable word list plus page scanning."""

from __future__ import annotations

from .models import NodeRange, ScanHit, TextBlock, WordEntry
from .normalize import normalize_char


def _normalize_block(block: TextBlock) -> tuple[str, list[int], list[int]]:
    """Normalize a whole block.

    Returns the normalized text plus, for each normalized code point, the
    index of the originating fragment and the code-point offset of the
    originating original character inside that fragment.
    """
    normalized_parts: list[str] = []
    origin_fragment: list[int] = []
    origin_offset: list[int] = []
    for frag_index, fragment in enumerate(block.fragments):
        for char_offset, ch in enumerate(fragment.text):
            piece = normalize_char(ch)
            normalized_parts.append(piece)
            origin_fragment.extend([frag_index] * len(piece))
            origin_offset.extend([char_offset] * len(piece))
    return "".join(normalized_parts), origin_fragment, origin_offset


def _find_overlapping(haystack: str, needle: str) -> list[int]:
    """All start indices of needle in haystack, including overlaps."""
    starts: list[int] = []
    pos = haystack.find(needle)
    while pos != -1:
        starts.append(pos)
        pos = haystack.find(needle, pos + 1)
    return starts


def _to_node_ranges(
    block: TextBlock,
    span: tuple[int, int],
    origin_fragment: list[int],
    origin_offset: list[int],
) -> tuple[NodeRange, ...]:
    """Map a normalized [start, end) span to per-node original ranges.

    The highlight covers the minimal continuous run of original code points
    from the first to the last participating one, including ignored
    characters in between but none outside the ends.
    """
    start, end = span
    first = (origin_fragment[start], origin_offset[start])
    last = (origin_fragment[end - 1], origin_offset[end - 1])
    ranges: list[NodeRange] = []
    for frag_index in range(first[0], last[0] + 1):
        node_id = block.fragments[frag_index].node_id
        frag_len = len(block.fragments[frag_index].text)
        range_start = first[1] if frag_index == first[0] else 0
        range_end = last[1] + 1 if frag_index == last[0] else frag_len
        ranges.append(NodeRange(node_id=node_id, start=range_start, end=range_end))
    return tuple(ranges)


class Scanner:
    """Holds the current word list in memory and scans pages (lists of blocks)."""

    def __init__(self, entries: list[WordEntry] | None = None) -> None:
        self._entries: list[tuple[str, str]] = []
        self.replace_entries(entries or [])

    def replace_entries(self, entries: list[WordEntry]) -> None:
        """Replace the whole word list; later scans only use the new list."""
        self._entries = []
        for entry in entries:
            normalized = "".join(normalize_char(ch) for ch in entry.text)
            if normalized:
                self._entries.append((entry.entry_id, normalized))

    def scan(self, blocks: list[TextBlock]) -> list[ScanHit]:
        """Scan a page (blocks in reading order) and return all hits."""
        hits: list[ScanHit] = []
        for block_index, block in enumerate(blocks):
            normalized, origin_fragment, origin_offset = _normalize_block(block)
            if not normalized:
                continue
            for entry_id, needle in self._entries:
                reported: set[tuple[tuple[str, int, int], ...]] = set()
                for start in _find_overlapping(normalized, needle):
                    span = (start, start + len(needle))
                    ranges = _to_node_ranges(
                        block, span, origin_fragment, origin_offset
                    )
                    key = tuple((r.node_id, r.start, r.end) for r in ranges)
                    if key in reported:
                        continue
                    reported.add(key)
                    hits.append(
                        ScanHit(
                            entry_id=entry_id,
                            block_index=block_index,
                            ranges=ranges,
                        )
                    )
        return hits
