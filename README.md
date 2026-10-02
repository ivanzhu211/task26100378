# PageForge Studio 敏感词预审定位库

纯内存的敏感词预审与原文定位库，无接口层、无外部依赖（仅标准库）。

## 功能

- 整体替换词库、扫描页面文本块，词库与扫描数据只保存在内存。
- 统一归一化：逐个原文码点 NFKC → 完整大小写折叠 → 删除 Unicode 类别
  为 Z*/P*/Cf 的码点；相邻原文码点不参与联合归一化。
- 块内跨片段命中（绝不跨文本块），子串匹配、无单词边界要求，
  保留前缀词、重叠词及同一词条的重叠出现。
- 命中映射回原文节点区间（左闭右开、按 Unicode 码点计），可直接用于高亮；
  同一词条映射到同一原文区间的多个命中只报告一次。

## 使用

```python
from pageforge import LexiconEntry, PageForgeStudio, TextBlock, TextFragment

studio = PageForgeStudio()
studio.replace_lexicon([LexiconEntry("w1", "strasse")])

blocks = [
    TextBlock((
        TextFragment("n1", "Ｓ"),
        TextFragment("n2", "，tra"),
        TextFragment("n3", "ße"),
    ))
]
for hit in studio.scan(blocks):
    print(hit.entry_id, [(r.node_id, r.start, r.end) for r in hit.ranges])
# w1 [("n1", 0, 1), ("n2", 0, 4), ("n3", 0, 2)]
```

- `replace_lexicon(entries)`：整体替换词库，后续扫描只使用新词库；
  归一化后相同的词条仍分别报告，归一化为空的词条不参与匹配。
- `scan(blocks)`：返回 `Hit` 列表，每条命中含 `entry_id`、`entry_text`
  及按阅读顺序排列的 `NodeRange(node_id, start, end)` 高亮区间。

## 测试

```bash
python3 -m pytest tests/ -q
```
