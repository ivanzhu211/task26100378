"""归一化：词条与页面使用完全相同的规则。

规则：逐个原文 Unicode 码点执行 NFKC，再做默认、非地区相关的完整
大小写折叠；拼接结果后删除 Unicode 类别为 Z、P 或 Cf 的码点。
相邻原文码点不参与联合归一化，不做其他转换。
"""

from __future__ import annotations

import unicodedata


def normalize_codepoint(ch: str) -> str:
    """对单个原文码点做 NFKC + casefold，返回归一化后的码点串（未过滤）。"""
    return unicodedata.normalize("NFKC", ch).casefold()


def is_ignored(ch: str) -> bool:
    """判断归一化后的码点是否应被删除（类别为 Z*、P* 或 Cf）。"""
    category = unicodedata.category(ch)
    return category[0] in ("Z", "P") or category == "Cf"


def normalize_text(text: str) -> str:
    """归一化整段文本，返回过滤后的归一化串。"""
    parts: list[str] = []
    for ch in text:
        for out in normalize_codepoint(ch):
            if not is_ignored(out):
                parts.append(out)
    return "".join(parts)
