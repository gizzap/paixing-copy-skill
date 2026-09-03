#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词表校验：纯代码、无外部依赖、结果可复现。
知识全部在 tables/*.csv，改表不改码。

用法：
    python check.py 稿子.txt
    python check.py 稿子目录/
    python check.py 稿子.csv --column 初稿
    python check.py 稿子.txt --json
"""
import csv, os, re, sys, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, "tables")

def rows(name):
    p = os.path.join(T, name)
    with open(p, encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if any(v.strip() for v in r.values())]

def load():
    red = [(r["类别"], r["词"].strip(), r["处理建议"]) for r in rows("红线词.csv")]
    plat = [(r["词"].strip(), r["处理建议"]) for r in rows("卡审词.csv")]
    comp = []
    for r in rows("竞品表述.csv"):
        comp.append({
            "组": r["品牌组"],
            "变体": [x for x in r["已知变体"].split("|") if x],
            "候选": [x for x in r["当期候选"].split("|") if x],
        })
    strat = {"停用": [], "主推": []}
    for r in rows("当期策略.csv"):
        strat.setdefault(r["类型"], []).append(r["品牌"].strip())
    return red, plat, comp, strat

def check(text, tables=None):
    red, plat, comp, strat = tables or load()
    out = []
    for cat, w, fix in red:
        for m in re.finditer(re.escape(w), text):
            out.append({"层": "红线·" + cat, "词": w, "位置": m.start(),
                        "上下文": ctx(text, m.start(), m.end()), "建议": fix})
    for w, fix in plat:
        for m in re.finditer(re.escape(w), text):
            out.append({"层": "平台卡审", "词": w, "位置": m.start(),
                        "上下文": ctx(text, m.start(), m.end()), "建议": fix})
    for g in comp:
        used = []
        for v in sorted(g["变体"], key=len, reverse=True):
            for m in re.finditer(re.escape(v), text):
                if any(a <= m.start() < b for a, b, _ in used):
                    continue
                used.append((m.start(), m.end(), v))
        if not used:
            continue
        forms = sorted({u[2] for u in used})
        if not g["候选"]:
            # 本期没有指定候选 = 这一组没有统一要求，单一写法保持原样。
            # 只有同一篇里混用了多种写法才是问题。
            if len(forms) > 1:
                for a, b, v in sorted(used):
                    out.append({"层": "竞品表述", "词": v, "位置": a,
                                "上下文": ctx(text, a, b),
                                "建议": "同篇混用了 %s，统一成其中一种即可"
                                        "（本期无指定候选，不要虚化成「那款」）" % "、".join(forms)})
            continue
        for a, b, v in sorted(used):
            if v in g["候选"]:
                continue
            out.append({"层": "竞品表述", "词": v, "位置": a,
                        "上下文": ctx(text, a, b),
                        "建议": "统一为 " + "、".join(g["候选"])})
    for w in strat.get("停用", []):
        for m in re.finditer(re.escape(w), text):
            out.append({"层": "策略·已停用", "词": w, "位置": m.start(),
                        "上下文": ctx(text, m.start(), m.end()),
                        "建议": "换为当期主推：" + "、".join(strat.get("主推", []))})
    return sorted(out, key=lambda x: x["位置"])

def ctx(t, a, b, pad=12):
    return t[max(0, a - pad):a] + "〖" + t[a:b] + "〗" + t[b:b + pad]

def read_inputs(path, column):
    if os.path.isdir(path):
        for fn in sorted(os.listdir(path)):
            if fn.endswith(".txt"):
                yield fn, open(os.path.join(path, fn), encoding="utf-8").read()
    elif path.endswith(".csv"):
        with open(path, encoding="utf-8-sig") as f:
            for i, r in enumerate(csv.DictReader(f), 1):
                if column not in r:
                    sys.exit("CSV 里没有列「%s」，现有列：%s" % (column, "、".join(r)))
                yield r.get("id") or str(i), r[column]
    else:
        yield os.path.basename(path), open(path, encoding="utf-8").read()

def _next(n):
    print("""
────────────────────────────────
第 1 步（词表校验）完成。这是四步流程的第一步，不要停在这里。

下一步 → 第 2 步 事实核查：prompts/事实核查.md
        参考数值取自 tables/月龄参考.csv
        ⚠ 一篇若分几部分给出，各部分之间也要交叉核对

完整顺序：
  1. check.py            ← 刚做完
  2. 事实核查             硬矛盾：数字、月龄、时间线
  3. 细节可信度           软可信度：哪些细节是编的
  4. 定点修正（按 1、2、3 的清单，只改清单位置）
  5a. 场景化             ← 先动结构
  5b. 口语化             ← 后修措辞
  6. verify.py 越界检查 + 重跑 check.py
────────────────────────────────""")

def main():
    ap = argparse.ArgumentParser(description="派星文案词表校验")
    ap.add_argument("path", help="txt 文件 / 目录 / csv")
    ap.add_argument("--column", default="初稿", help="csv 中稿子所在列名，默认「初稿」")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()
    tables = load()
    result, total = {}, 0
    for name, text in read_inputs(a.path, a.column):
        f = check(text, tables)
        total += len(f)
        if f:
            result[name] = f
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return
    if not result:
        print("未发现词表层问题。")
        _next(0)
        return
    for name, fs in result.items():
        print("\n=== %s ===  %d 条" % (name, len(fs)))
        for x in fs:
            print("  [%s] %s" % (x["层"], x["上下文"]))
            print("        → %s" % x["建议"])
    print("\n合计 %d 篇有问题，共 %d 条。" % (len(result), total))
    _next(total)

if __name__ == "__main__":
    main()
