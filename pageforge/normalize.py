"""Per-code-point normalization shared by word entries and page text."""

import unicodedata


def _is_ignored(ch: str) -> bool:
    """True for code points in Unicode categories Z*, P* or Cf."""
    category = unicodedata.category(ch)
    return category[0] in ("Z", "P") or category == "Cf"


def normalize_char(ch: str) -> str:
    """Normalize a single original code point; may expand to 0..n code points.

    Steps, applied to one original code point at a time (never jointly):
    NFKC, then default locale-independent full case folding, then drop
    code points in categories Z*, P* or Cf.
    """
    folded = unicodedata.normalize("NFKC", ch).casefold()
    return "".join(c for c in folded if not _is_ignored(c))
