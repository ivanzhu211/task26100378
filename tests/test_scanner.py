"""Automated tests for the PageForge Studio pre-screening library."""

import unittest

from pageforge import NodeRange, Scanner, TextBlock, TextFragment, WordEntry


def make_block(*fragments):
    return TextBlock(tuple(TextFragment(node_id=nid, text=t) for nid, t in fragments))


def hit_keys(hits):
    return {
        (h.entry_id, h.block_index, tuple((r.node_id, r.start, r.end) for r in h.ranges))
        for h in hits
    }


class CrossFragmentCaseFoldingTest(unittest.TestCase):
    """Fragments: fullwidth-S / comma+tra / sharp-s+e in one block."""

    def setUp(self):
        self.block = make_block(("n1", "Ｓ"), ("n2", "，tra"), ("n3", "ße"))

    def scan_one(self, word):
        scanner = Scanner([WordEntry("w", word)])
        return scanner.scan([self.block])

    def test_strasse_matches_across_three_fragments_including_comma(self):
        hits = self.scan_one("strasse")
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(hit.entry_id, "w")
        self.assertEqual(hit.block_index, 0)
        self.assertEqual(
            hit.ranges,
            (
                NodeRange("n1", 0, 1),
                NodeRange("n2", 0, 4),
                NodeRange("n3", 0, 2),
            ),
        )

    def test_ss_highlights_only_sharp_s(self):
        hits = self.scan_one("ss")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].ranges, (NodeRange("n3", 0, 1),))

    def test_s_reports_two_positions_despite_sharp_s_expansion(self):
        hits = self.scan_one("s")
        self.assertEqual(len(hits), 2)
        self.assertEqual(
            hit_keys(hits),
            {("w", 0, (("n1", 0, 1),)), ("w", 0, (("n3", 0, 1),))},
        )


class BlockBoundaryTest(unittest.TestCase):
    def test_no_match_across_blocks(self):
        blocks = [
            make_block(("n1", "Ｓ")),
            make_block(("n2", "，tra")),
            make_block(("n3", "ße")),
        ]
        scanner = Scanner([WordEntry("w", "strasse")])
        self.assertEqual(scanner.scan(blocks), [])

    def test_decomposed_accent_does_not_match_precomposed_entry(self):
        blocks = [make_block(("n1", "e"), ("n2", "́"))]
        scanner = Scanner([WordEntry("w", "é")])
        self.assertEqual(scanner.scan(blocks), [])


class WordListReplacementTest(unittest.TestCase):
    def setUp(self):
        self.blocks = [make_block(("n1", "Alpha beta"))]

    def test_scan_uses_only_the_new_word_list(self):
        scanner = Scanner([WordEntry("old", "alpha")])
        self.assertEqual(len(scanner.scan(self.blocks)), 1)
        scanner.replace_entries([WordEntry("new", "beta")])
        hits = scanner.scan(self.blocks)
        self.assertEqual([h.entry_id for h in hits], ["new"])

    def test_entries_normalizing_to_same_text_are_reported_separately(self):
        scanner = Scanner([WordEntry("a", "ＳＳ"), WordEntry("b", "ss")])
        hits = scanner.scan([make_block(("n1", "ss"))])
        self.assertEqual({h.entry_id for h in hits}, {"a", "b"})

    def test_entries_normalizing_to_empty_are_ignored(self):
        scanner = Scanner([WordEntry("punct", "，。！")])
        self.assertEqual(scanner.scan(self.blocks), [])


class MatchingSemanticsTest(unittest.TestCase):
    def scan_one(self, word, text):
        scanner = Scanner([WordEntry("w", word)])
        return scanner.scan([make_block(("n1", text))])

    def test_prefix_and_overlapping_words_all_reported(self):
        scanner = Scanner([WordEntry("he", "he"), WordEntry("she", "she")])
        hits = scanner.scan([make_block(("n1", "she"))])
        self.assertEqual({h.entry_id for h in hits}, {"he", "she"})

    def test_overlapping_occurrences_of_same_entry(self):
        hits = self.scan_one("aa", "aaa")
        self.assertEqual(
            hit_keys(hits),
            {("w", 0, (("n1", 0, 2),)), ("w", 0, (("n1", 1, 3),))},
        )

    def test_no_word_boundary_required(self):
        hits = self.scan_one("cat", "concatenate")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].ranges, (NodeRange("n1", 3, 6),))

    def test_ignored_chars_at_ends_not_included(self):
        hits = self.scan_one("ab", ",a b,")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].ranges, (NodeRange("n1", 1, 4),))


if __name__ == "__main__":
    unittest.main()
