"""扫描器：在归一化后的块内查找所有子串命中并映射回原文区间。"""

from __future__ import annotations

from .models import Hit, LexiconEntry, NodeRange, TextBlock
from .normalize import is_ignored, normalize_codepoint, normalize_text


def _build_normalized_block(
    block: TextBlock,
) -> tuple[str, list[tuple[int, int]]]:
    """拼接块内各片段的归一化串，并记录每个归一化码点对应的原文位置。

    返回 (归一化串, 映射表)；映射表元素为 (片段下标, 原文码点偏移)。
    """
    normalized: list[str] = []
    mapping: list[tuple[int, int]] = []
    for frag_index, fragment in enumerate(block.fragments):
        for offset, ch in enumerate(fragment.text):
            for out in normalize_codepoint(ch):
                if not is_ignored(out):
                    normalized.append(out)
                    mapping.append((frag_index, offset))
    return "".join(normalized), mapping


def _ranges_for_occurrence(
    block: TextBlock,
    mapping: list[tuple[int, int]],
    start: int,
    end: int,
) -> tuple[NodeRange, ...]:
    """把归一化区间 [start, end) 映射为各节点上的原文高亮区间。

    高亮范围是首尾参与匹配的原文码点之间的最小连续区间，
    包含中间被忽略的字符，不包含两端之外的被忽略字符。
    """
    first_frag, first_offset = mapping[start]
    last_frag, last_offset = mapping[end - 1]
    ranges: list[NodeRange] = []
    for frag_index in range(first_frag, last_frag + 1):
        fragment = block.fragments[frag_index]
        lo = first_offset if frag_index == first_frag else 0
        hi = last_offset + 1 if frag_index == last_frag else len(fragment.text)
        if lo < hi:
            ranges.append(NodeRange(fragment.node_id, lo, hi))
    return tuple(ranges)


def _find_overlapping(haystack: str, needle: str) -> list[int]:
    """查找所有（含重叠）出现位置。"""
    positions: list[int] = []
    start = haystack.find(needle)
    while start != -1:
        positions.append(start)
        start = haystack.find(needle, start + 1)
    return positions


def scan_blocks(
    entries: list[LexiconEntry], blocks: list[TextBlock]
) -> list[Hit]:
    """对每个文本块独立扫描，返回全部命中（按块、词条、位置排序）。"""
    normalized_entries: list[tuple[LexiconEntry, str]] = []
    for entry in entries:
        normalized_entry = normalize_text(entry.text)
        if normalized_entry:
            normalized_entries.append((entry, normalized_entry))

    hits: list[Hit] = []
    for block in blocks:
        normalized_block, mapping = _build_normalized_block(block)
        if not normalized_block:
            continue
        for entry, normalized_entry in normalized_entries:
            seen_ranges: set[tuple[NodeRange, ...]] = set()
            for start in _find_overlapping(normalized_block, normalized_entry):
                ranges = _ranges_for_occurrence(
                    block, mapping, start, start + len(normalized_entry)
                )
                if ranges in seen_ranges:
                    continue
                seen_ranges.add(ranges)
                hits.append(Hit(entry.entry_id, entry.text, ranges))
    return hits
