# -*- coding: utf-8 -*-
"""
解析 省份/*.md -> web/assets/data.js
生成网页版资料库所需的结构化数据。
"""
import os, re, json

BASE = os.path.dirname(os.path.abspath(__file__))
PROV = os.path.join(BASE, "省份")
WEB = os.path.join(BASE, "web")
ASSETS = os.path.join(WEB, "assets")

REGION = {
    "01": "华北", "02": "华北", "03": "华北", "04": "华北", "05": "华北",
    "06": "东北", "07": "东北", "08": "东北",
    "09": "华东", "10": "华东", "11": "华东", "12": "华东", "13": "华东",
    "14": "华东", "15": "华东",
    "16": "华中", "17": "华中", "18": "华中",
    "19": "华南", "20": "华南", "21": "华南",
    "22": "西南", "23": "西南", "24": "西南", "25": "西南", "26": "西南",
    "27": "西北", "28": "西北", "29": "西北", "30": "西北", "31": "西北", "32": "西北",
}
REGION_ORDER = ["华北", "东北", "华东", "华中", "华南", "西南", "西北"]

TYPE_RULES = [
    ("T01", "山岳峰林", ["山岳", "峰林", "山地", "峡谷", "名山"]),
    ("T02", "水域湖泊与湿地", ["水域", "湖泊", "湿地", "海滨", "瀑布", "河流", "滨海", "岛屿"]),
    ("T03", "森林草原", ["森林", "草原", "竹海", "草甸", "林海"]),
    ("T04", "地质地貌与洞穴", ["地质", "丹霞", "雅丹", "喀斯特", "石林", "溶洞", "火山", "地貌", "石阵"]),
    ("T05", "沙漠戈壁", ["沙漠", "戈壁", "沙丘"]),
    ("T06", "古典园林", ["园林"]),
    ("T07", "古城古镇古村", ["古城", "古镇", "古村", "历史街区", "古商城", "老城"]),
    ("T08", "宗教圣地与石窟", ["宗教", "寺庙", "道观", "石窟", "佛教", "道教", "妈祖", "圣地"]),
    ("T09", "遗址考古与石刻", ["遗址", "考古", "墓葬", "石刻", "岩画", "故城", "长城"]),
    ("T10", "陵寝祠庙", ["陵寝", "陵墓", "祠庙", "陵园", "皇陵"]),
    ("T11", "红色旅游", ["红色", "革命", "长征", "起义"]),
    ("T12", "博物馆与场馆", ["博物馆", "科技馆", "纪念馆", "文化中心", "场馆", "博物院"]),
    ("T13", "主题乐园与度假区", ["主题乐园", "游乐", "影视城", "度假区", "动物园", "休博园"]),
    ("T14", "城市地标与现代景观", ["城市地标", "现代建筑", "城市公园", "商务旅游", "地标", "广播电视塔"]),
    ("T15", "民族风情与边境", ["民族", "民俗", "边境", "苗寨", "侗寨", "羌城"]),
    ("T16", "乡村田园", ["乡村", "茶园", "农业", "田园", "梯田"]),
    ("T17", "工业遗产", ["工业", "矿山", "酒庄", "厂区"]),
    ("T18", "古建筑与宫殿坛庙", ["古建筑", "宫殿", "坛庙", "府邸", "王府", "楼阁", "城墙"]),
]

TIP_KEYS = [
    ("must", ["必讲"]),
    ("data", ["数据锚点", "数据点"]),
    ("myth", ["常见误区", "误区", "纠偏"]),
    ("ask", ["互动", "提问设计", "互动设计"]),
]


def norm_types(s):
    hits = []
    for code, _name, kws in TYPE_RULES:
        for kw in kws:
            if kw in s:
                hits.append(code)
                break
    return hits or ["T00"]


def to_paras(raw):
    """把一段文本切成段落列表，去掉空行"""
    return [x.strip() for x in raw.strip().split("\n") if x.strip()]


def parse_spots(block):
    """解析 5A 词条区块"""
    lines = block.split("\n")
    spots = []
    cur = None
    field = None  # None / intro / script / tips
    buf = []

    def flush():
        if cur is None:
            return
        if field == "intro":
            cur["intro"] = to_paras("\n".join(buf))
        elif field == "script":
            cur["script"] = to_paras("\n".join(buf))
        elif field == "tips":
            cur["tips"] = parse_tips("\n".join(buf))
        buf.clear()

    def parse_tips(raw):
        out = {}
        for line in raw.split("\n"):
            line = line.strip()
            if not line.startswith("-"):
                continue
            body = re.sub(r"^-\s*", "", line)
            body = re.sub(r"\*\*", "", body)
            if not body or set(body) <= set("-—*"):   # 分隔线，跳过
                continue
            key = None
            for k, kws in TIP_KEYS:
                for kw in kws:
                    # 允许「互动/提问设计：」「常见误区①②③」等复合写法
                    m = re.match(r"^%s[^：:]{0,14}?\s*[：:]\s*(.+)$" % re.escape(kw), body)
                    if m:
                        key, body = k, m.group(1).strip()
                        break
                if key:
                    break
            if key:
                out[key] = body
            else:
                out.setdefault("other", [])
                out["other"].append(body)
        return out

    for line in lines:
        mh = re.match(r"^###\s+(\d+)[\.、]\s*(.+?)\s*$", line)
        if mh:
            flush()
            cur = {"name": mh.group(2).strip(), "level": "5A", "place": "", "type": "",
                   "year": "", "duration": "", "grade": "", "intro": [], "script": [], "tips": {}}
            field = None
            spots.append(cur)
            continue
        if cur is None:
            continue

        if line.startswith("**【景区简介】**") or line.startswith("**【景区简介】"):
            flush()
            field = "intro"
            continue
        if line.startswith("**【导游词核心稿】**") or line.startswith("**【导游词核心稿】"):
            flush()
            field = "script"
            continue
        if line.startswith("**【讲解要点提示】**") or line.startswith("**【讲解要点提示】"):
            flush()
            field = "tips"
            continue

        if field in ("intro", "script"):
            if line.strip() == "---":
                flush()
                field = None
                continue
            buf.append(line)
            continue
        if field == "tips":
            buf.append(line)
            continue

        # 信息表
        for key, pat in (("grade", "等级"), ("place", "所在地"), ("type", "类型"),
                         ("year", "评定年份"), ("duration", "建议游览时长")):
            m = re.match(r"^\|\s*%s\s*\|\s*(.+?)\s*\|\s*$" % pat, line)
            if m:
                cur[key] = m.group(1).strip()
                break
    flush()
    return spots


def parse_a4(block):
    """解析 4A 名录索引表格（可能有多个表 / 分组标题）"""
    rows = []
    header = None
    group = ""
    for line in block.split("\n"):
        m = re.match(r"^#{4,6}\s+(.+?)\s*$", line)
        if m:
            group = m.group(1).strip()
            header = None
            continue
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if any("序号" in c for c in cells):
                header = cells
                continue
            if header is None:
                continue
            rec = {}
            for i, h in enumerate(header):
                if i < len(cells):
                    rec[h] = cells[i]
            name = rec.get("景区名称") or rec.get("名称") or (cells[1] if len(cells) > 1 else "")
            if not name or not re.match(r"^\d+$", rec.get("序号", "1")):
                continue
            rows.append({
                "name": name,
                "county": rec.get("所在区县") or rec.get("区县") or rec.get("所在地") or "",
                "type": rec.get("类型") or "",
                "status": rec.get("词条状态") or rec.get("状态") or "",
                "group": group,
            })
    return rows


def main():
    os.makedirs(ASSETS, exist_ok=True)
    files = sorted(f for f in os.listdir(PROV) if f.endswith(".md"))

    provinces = []
    for fn in files:
        code = fn[:2]
        name = fn[3:-3]
        text = open(os.path.join(PROV, fn), encoding="utf-8").read()
        lines = text.split("\n")

        def idx_of(prefix):
            for i, l in enumerate(lines):
                if l.startswith(prefix):
                    return i
            return None

        i1 = idx_of("## 一") or 0
        i2 = idx_of("## 二") or len(lines)
        i3 = idx_of("## 三") or len(lines)

        # 头部信息
        head = "\n".join(lines[:i1])
        m5 = re.search(r"5A级景区[：:][^\d]*(\d+)\s*家", head)
        n5_declared = int(m5.group(1)) if m5 else 0
        m4 = re.search(r"名录索引收录\s*(\d+)\s*家", head)
        note = ""
        for l in lines[:i1]:
            if l.startswith("> - 编写说明") or l.startswith("> - 5A级景区") and "兵团" in l:
                note += re.sub(r"^>\s*-?\s*", "", l) + " "

        spots = parse_spots("\n".join(lines[i1:i2]))
        a4 = parse_a4("\n".join(lines[i2:i3]))

        # 待核实事项
        pending = []
        for l in lines[i3:]:
            ls = l.strip()
            if ls.startswith("- ") or re.match(r"^\d+\.\s", ls):
                t = re.sub(r"^[-*]\s*|^\d+\.\s*", "", ls)
                if t and not t.startswith("*"):
                    pending.append(t)

        provinces.append({
            "code": code, "name": name, "region": REGION.get(code, "其他"),
            "n5": len(spots), "n5declared": n5_declared, "n4": len(a4),
            "note": note.strip(),
            "spots": spots, "a4": a4, "pending": pending,
        })

    total5 = sum(p["n5"] for p in provinces)
    total4 = sum(p["n4"] for p in provinces)

    # 类型索引
    types = {c: {"code": c, "name": n, "items": []} for c, n, _ in TYPE_RULES}
    types["T00"] = {"code": "T00", "name": "其他", "items": []}
    for p in provinces:
        for s in p["spots"]:
            s["types"] = norm_types(s["type"])
            s["prov"] = p["name"]
            s["pcode"] = p["code"]
            for c in s["types"]:
                types.setdefault(c, {"code": c, "name": "其他", "items": []})["items"].append(
                    {"name": s["name"], "prov": p["name"], "pcode": p["code"],
                     "year": s["year"], "type": s["type"]}
                )

    # 4A 也做类型归并（用于类型视图下的 4A 列表）
    for p in provinces:
        for r in p["a4"]:
            r["prov"] = p["name"]
            r["pcode"] = p["code"]
            r["types"] = norm_types(r["type"])

    data = {
        "meta": {"total5": total5, "total4": total4, "provinces": len(provinces),
                 "updated": "2026-10", "unique": total5 - 2},
        "regions": REGION_ORDER,
        "types": [types[c] for c in [t[0] for t in TYPE_RULES] + ["T00"] if types.get(c)],
        "provinces": provinces,
    }

    js = "window.SITE_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(ASSETS, "data.js"), "w", encoding="utf-8") as f:
        f.write(js)

    print("5A:", total5, " 4A:", total4, " 省:", len(provinces))
    print("data.js: %.1f KB" % (os.path.getsize(os.path.join(ASSETS, "data.js")) / 1024))
    for p in provinces:
        empty = sum(1 for s in p["spots"] if not s["script"] or not s["intro"])
        print("  %s %s: 5A=%d 4A=%d 空词条=%d" % (p["code"], p["name"], p["n5"], p["n4"], empty))


if __name__ == "__main__":
    main()
