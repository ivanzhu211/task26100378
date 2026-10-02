"""PageForge Studio 敏感词预审定位库的自动化测试。"""

from __future__ import annotations

from pageforge import (
    LexiconEntry,
    NodeRange,
    PageForgeStudio,
    TextBlock,
    TextFragment,
)


def make_studio(entries: list[LexiconEntry]) -> PageForgeStudio:
    studio = PageForgeStudio()
    studio.replace_lexicon(entries)
    return studio


def ranges_of(hit) -> list[tuple[str, int, int]]:
    return [(r.node_id, r.start, r.end) for r in hit.ranges]


class TestCrossFragmentHit:
    """场景一：同一块的三个片段 “Ｓ”“，tra”“ße”。"""

    blocks = [
        TextBlock(
            (
                TextFragment("n1", "Ｓ"),
                TextFragment("n2", "，tra"),
                TextFragment("n3", "ße"),
            )
        )
    ]

    def test_strasse_spans_three_fragments_and_includes_comma(self):
        studio = make_studio([LexiconEntry("w1", "strasse")])
        hits = studio.scan(self.blocks)
        assert len(hits) == 1
        hit = hits[0]
        assert hit.entry_id == "w1"
        assert hit.entry_text == "strasse"
        # 跨三片段；n2 的区间 [0, 4) 包含开头的全角逗号。
        assert ranges_of(hit) == [("n1", 0, 1), ("n2", 0, 4), ("n3", 0, 2)]

    def test_ss_highlights_only_sharp_s(self):
        studio = make_studio([LexiconEntry("w2", "ss")])
        hits = studio.scan(self.blocks)
        assert len(hits) == 1
        # “ß” 折叠为 “ss”，高亮只落在 ß 上。
        assert ranges_of(hits[0]) == [("n3", 0, 1)]

    def test_s_reports_exactly_two_original_positions(self):
        studio = make_studio([LexiconEntry("w3", "s")])
        hits = studio.scan(self.blocks)
        # “ß” 展开出的两个 s 映射到同一原文区间，只报告一次。
        assert len(hits) == 2
        assert ranges_of(hits[0]) == [("n1", 0, 1)]
        assert ranges_of(hits[1]) == [("n3", 0, 1)]


class TestBlockBoundary:
    """场景二：分到不同文本块后不再命中 strasse。"""

    def test_no_cross_block_hit(self):
        studio = make_studio([LexiconEntry("w1", "strasse")])
        blocks = [
            TextBlock((TextFragment("n1", "Ｓ"),)),
            TextBlock((TextFragment("n2", "，tra"),)),
            TextBlock((TextFragment("n3", "ße"),)),
        ]
        assert studio.scan(blocks) == []

    def test_combining_accent_does_not_match_precomposed(self):
        # 相邻片段分别包含 “e” 和 U+0301，不应命中预组合词条 “é”。
        studio = make_studio([LexiconEntry("w4", "é")])
        blocks = [
            TextBlock(
                (
                    TextFragment("n1", "e"),
                    TextFragment("n2", "́"),
                )
            )
        ]
        assert studio.scan(blocks) == []


class TestLexiconSemantics:
    def test_replace_lexicon_uses_only_new_entries(self):
        studio = make_studio([LexiconEntry("old", "bad")])
        blocks = [TextBlock((TextFragment("n1", "bad word"),))]
        assert len(studio.scan(blocks)) == 1
        studio.replace_lexicon([LexiconEntry("new", "word")])
        hits = studio.scan(blocks)
        assert [h.entry_id for h in hits] == ["new"]

    def test_same_normalized_entries_reported_separately(self):
        studio = make_studio(
            [LexiconEntry("a", "Strasse"), LexiconEntry("b", "ｓｔｒａｓｓｅ")]
        )
        blocks = [TextBlock((TextFragment("n1", "strasse"),))]
        hits = studio.scan(blocks)
        assert [h.entry_id for h in hits] == ["a", "b"]
        assert hits[0].entry_text == "Strasse"
        assert hits[1].entry_text == "ｓｔｒａｓｓｅ"

    def test_empty_normalized_entry_does_not_match(self):
        studio = make_studio(
            [LexiconEntry("empty", "　，"), LexiconEntry("ok", "word")]
        )
        blocks = [TextBlock((TextFragment("n1", "　，word"),))]
        hits = studio.scan(blocks)
        assert [h.entry_id for h in hits] == ["ok"]


class TestMatchingRules:
    def test_substring_without_word_boundary(self):
        studio = make_studio([LexiconEntry("w", "cat")])
        blocks = [TextBlock((TextFragment("n1", "concatenate"),))]
        hits = studio.scan(blocks)
        assert len(hits) == 1
        assert ranges_of(hits[0]) == [("n1", 3, 6)]

    def test_prefix_and_overlapping_hits_kept(self):
        studio = make_studio(
            [LexiconEntry("prefix", "aba"), LexiconEntry("longer", "ababa")]
        )
        blocks = [TextBlock((TextFragment("n1", "ababa"),))]
        hits = studio.scan(blocks)
        got = [(h.entry_id, ranges_of(h)) for h in hits]
        assert got == [
            ("prefix", [("n1", 0, 3)]),
            ("prefix", [("n1", 2, 5)]),
            ("longer", [("n1", 0, 5)]),
        ]

    def test_case_and_fullwidth_evasion(self):
        studio = make_studio([LexiconEntry("w", "hello")])
        blocks = [TextBlock((TextFragment("n1", "ＨｅＬＬｏ"),))]
        hits = studio.scan(blocks)
        assert len(hits) == 1
        assert ranges_of(hits[0]) == [("n1", 0, 5)]

    def test_inserted_punctuation_ignored_inside_hit(self):
        studio = make_studio([LexiconEntry("w", "ab")])
        blocks = [TextBlock((TextFragment("n1", "a, b"),))]
        hits = studio.scan(blocks)
        assert len(hits) == 1
        # 高亮包含中间被忽略的标点与空格，但不向两端扩展。
        assert ranges_of(hits[0]) == [("n1", 0, 4)]

    def test_ignored_chars_at_edges_not_included(self):
        studio = make_studio([LexiconEntry("w", "ab")])
        blocks = [TextBlock((TextFragment("n1", ", ab ,"),))]
        hits = studio.scan(blocks)
        assert ranges_of(hits[0]) == [("n1", 2, 4)]

    def test_same_original_range_reported_once(self):
        # “ßß” 归一化为 “ssss”，词条 “ss” 有 4 个归一化命中，
        # 但映射到同一原文区间的只报告一次，共 3 条。
        studio = make_studio([LexiconEntry("w", "ss")])
        blocks = [TextBlock((TextFragment("n1", "ßß"),))]
        hits = studio.scan(blocks)
        assert [ranges_of(h) for h in hits] == [
            [("n1", 0, 1)],
            [("n1", 0, 2)],
            [("n1", 1, 2)],
        ]

    def test_hit_ranges_carry_entry_identity(self):
        studio = make_studio([LexiconEntry("w1", "x")])
        blocks = [TextBlock((TextFragment("n1", "x"),))]
        hit = studio.scan(blocks)[0]
        assert hit.entry_id == "w1"
        assert hit.entry_text == "x"
        assert hit.ranges == (NodeRange("n1", 0, 1),)
