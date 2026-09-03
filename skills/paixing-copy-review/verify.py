#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定点修正的越界检查：确认所有改动都落在问题清单标出的范围内。

用法：
    python verify.py 原文.txt 修正后.txt --findings 清单.json
    python verify.py --pair 修正结果.json     # 含 原文/corrected/清单 的单文件
"""
import json, sys, argparse, difflib, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import check, load

def flagged_spans(text, findings, pad=6):
    """清单标出的位置，前后放宽 pad 个字（改法可能略微溢出词边界）。
    同一个词在文中多处出现时，全部位置都算在清单内——例如人称代词统一，
    清单只报一处，但修正必然要动到所有出现的地方。"""
    s = set()
    for f in findings:
        w = (f.get("词") or f.get("where") or "").strip()
        if not w:
            continue
        starts = []
        p = f.get("位置")
        if p is not None and p >= 0:
            starts.append(p)
        start = 0
        while True:
            k = text.find(w, start)
            if k < 0:
                break
            starts.append(k)
            start = k + 1
        for k in set(starts):
            s.update(range(max(0, k - pad), min(len(text), k + len(w) + pad)))
    return s

def verify(orig, fixed, findings):
    ok_span = flagged_spans(orig, findings)
    out, bad = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, orig, fixed).get_opcodes():
        if tag == "equal":
            continue
        touched = set(range(i1, i2)) if i2 > i1 else {min(i1, len(orig) - 1)}
        inside = touched <= ok_span if touched else True
        rec = {"改动": "%s→%s" % (orig[i1:i2] or "∅", fixed[j1:j2] or "∅"),
               "位置": i1, "在清单内": inside,
               "上下文": orig[max(0, i1 - 10):i1] + "〖" + orig[i1:i2] + "〗" + orig[i2:i2 + 10]}
        out.append(rec)
        if not inside:
            bad.append(rec)
    return out, bad

def main():
    ap = argparse.ArgumentParser(description="定点修正越界检查")
    ap.add_argument("orig", nargs="?"); ap.add_argument("fixed", nargs="?")
    ap.add_argument("--findings"); ap.add_argument("--pair")
    a = ap.parse_args()
    if a.pair:
        d = json.load(open(a.pair, encoding="utf-8"))
        orig, fixed, fs = d["原文"], d["corrected"], d.get("清单", [])
    else:
        orig = open(a.orig, encoding="utf-8").read()
        fixed = open(a.fixed, encoding="utf-8").read()
        fs = json.load(open(a.findings, encoding="utf-8")) if a.findings else []
        if isinstance(fs, dict):
            fs = [x for v in fs.values() for x in v]
    all_c, bad = verify(orig, fixed, fs)
    print("共 %d 处改动，其中 %d 处在清单外" % (len(all_c), len(bad)))
    for r in bad:
        print("  ✗ 越界：%s   %s" % (r["改动"], r["上下文"]))
    # 二次校验：修正后是否引入新的词表问题
    tables = load()
    b0 = {(x["层"], x["词"]) for x in check(orig, tables)}
    b1 = [x for x in check(fixed, tables) if (x["层"], x["词"]) not in b0]
    if b1:
        print("\n修正后新引入 %d 条词表问题：" % len(b1))
        for x in b1:
            print("  ✗ [%s] %s" % (x["层"], x["上下文"]))
    left = check(fixed, tables)
    print("\n修正后仍剩 %d 条词表问题（应尽量为 0）" % len(left))
    sys.exit(1 if (bad or b1) else 0)

if __name__ == "__main__":
    main()
