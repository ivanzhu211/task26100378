# PageForge Studio 敏感词预审定位库

纯内存的敏感词预审与原文定位库，无接口层、无外部依赖（仅标准库）。

## 使用

```python
from pageforge import Scanner, TextBlock, TextFragment, WordEntry

scanner = Scanner([WordEntry("w1", "strasse")])
blocks = [
    TextBlock((
        TextFragment("n1", "Ｓ"),
        TextFragment("n2", "，tra"),
        TextFragment("n3", "ße"),
    )),
]
for hit in scanner.scan(blocks):
    print(hit.entry_id, hit.block_index, hit.ranges)
# w1 0 (NodeRange('n1', 0, 1), NodeRange('n2', 0, 4), NodeRange('n3', 0, 2))

scanner.replace_entries([WordEntry("w2", "ss")])  # 整体替换词库
```

- `Scanner(entries)` / `replace_entries(entries)`：整体替换词库，之后扫描只用新词库。
  归一化后相同的词条分别报告；归一化为空的词条不参与匹配。
- `scan(blocks)`：扫描一个页面（按阅读顺序排列的 `TextBlock` 列表），返回 `ScanHit` 列表。
  命中可跨同一片段内的相邻片段，绝不跨文本块。
- 每条 `ScanHit` 含 `entry_id`、`block_index` 和 `ranges`（`NodeRange` 元组）。
  `NodeRange` 给出节点上的高亮区间，偏移按原文 Unicode 码点计，左闭右开；
  范围覆盖首尾参与匹配的原文码点之间的最小连续区间（含中间被忽略的字符）。

## 归一化规则

词条与页面共用同一规则：逐个原文码点做 NFKC，再做默认完整大小写折叠，
拼接后删除 Unicode 类别为 Z*、P*、Cf 的码点。相邻码点不联合归一化。

## 运行测试

```bash
python3 -m pytest tests/ -q     # 或 python3 -m unittest discover tests -v
```
