# -*- coding: utf-8 -*-
"""
解析 省份/*.md，生成 README.md（总索引）与 按类型索引.md
"""
import os, re, json
from collections import OrderedDict, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
PROV = os.path.join(BASE, "省份")

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

# 类型归一化：受控词表 T01-T18
TYPE_RULES = [
    ("T01", "山岳峰林", ["山岳", "峰林", "山地", "峡谷", "名山"]),
    ("T02", "水域湖泊与湿地", ["水域", "湖泊", "湿地", "海滨", "瀑布", "江 ", "河流", "海滨岛屿", "滨海"]),
    ("T03", "森林草原", ["森林", "草原", "竹海", "草甸", "林海"]),
    ("T04", "地质地貌与洞穴", ["地质", "丹霞", "雅丹", "喀斯特", "石林", "溶洞", "火山", "地貌", "峡谷地貌", "石阵"]),
    ("T05", "沙漠戈壁", ["沙漠", "戈壁", "沙丘"]),
    ("T06", "古典园林", ["园林"]),
    ("T07", "古城古镇古村", ["古城", "古镇", "古村", "历史街区", "古商城", "老城"]),
    ("T08", "宗教圣地与石窟", ["宗教", "寺庙", "道观", "石窟", "佛教", "道教", "妈祖", "圣地"]),
    ("T09", "遗址考古与石刻", ["遗址", "考古", "墓葬", "石刻", "岩画", "故城"]),
    ("T10", "陵寝祠庙", ["陵寝", "陵墓", "祠庙", "陵园", "皇陵"]),
    ("T11", "红色旅游", ["红色", "革命", "长征", "起义", "纪念馆(红"]),
    ("T12", "博物馆与场馆", ["博物馆", "科技馆", "纪念馆", "文化中心", "场馆", "博物院"]),
    ("T13", "主题乐园与度假区", ["主题乐园", "游乐", "影视城", "度假区", "动物园", "休博园", "旅游度假"]),
    ("T14", "城市地标与现代景观", ["城市地标", "现代建筑", "城市公园", "商务旅游", "地标", "广播电视塔", "奥帆"]),
    ("T15", "民族风情与边境", ["民族", "民俗", "边境", "苗寨", "侗寨", "羌城"]),
    ("T16", "乡村田园", ["乡村", "茶园", "农业", "田园", "梯田"]),
    ("T17", "工业遗产", ["工业", "矿山", "酒庄", "厂区"]),
    ("T18", "古建筑与宫殿坛庙", ["古建筑", "宫殿", "坛庙", "府邸", "王府", "古建", "楼阁", "城墙"]),
]
TYPE_ORDER = {t[0]: t[1] for t in TYPE_RULES}


def norm_types(type_str):
    """把类型字符串映射到受控类型编号"""
    hits = []
    for code, name, kws in TYPE_RULES:
        for kw in kws:
            if kw in type_str:
                hits.append(code)
                break
    return hits or ["T00"]


def parse_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")

    # 头部统计
    head = "\n".join(lines[:8])
    m5 = re.search(r"5A级景区[：:]\s*(\d+)\s*家", head)
    declared5 = int(m5.group(1)) if m5 else 0
    m5b = re.search(r"已收录\s*(\d+)\s*家", head)
    written5 = int(m5b.group(1)) if m5b else declared5
    m4 = re.search(r"名录索引收录\s*(\d+)\s*家", head)
    idx4 = int(m4.group(1)) if m4 else 0

    # 切分 一、5A 与 二、4A
    try:
        i2 = next(i for i, l in enumerate(lines) if l.startswith("## 二"))
    except StopIteration:
        i2 = len(lines)
    try:
        i1 = next(i for i, l in enumerate(lines) if l.startswith("## 一"))
    except StopIteration:
        i1 = 0

    entries = []
    cur = None
    for line in lines[i1:i2]:
        mh = re.match(r"^###\s+\d+[\.、]\s*(.+?)\s*$", line)
        if mh:
            if cur:
                entries.append(cur)
            cur = {"name": mh.group(1).strip(), "type": "", "year": "", "place": ""}
            continue
        if cur is None:
            continue
        mt = re.match(r"^\|\s*类型\s*\|\s*(.+?)\s*\|", line)
        if mt and not cur["type"]:
            cur["type"] = mt.group(1).strip()
        my = re.match(r"^\|\s*评定年份\s*\|\s*(.+?)\s*\|", line)
        if my and not cur["year"]:
            cur["year"] = my.group(1).strip()
        mp = re.match(r"^\|\s*所在地\s*\|\s*(.+?)\s*\|", line)
        if mp and not cur["place"]:
            cur["place"] = mp.group(1).strip()
    if cur:
        entries.append(cur)

    # 4A 索引条数（实际表格行数）
    cnt4 = 0
    in_tbl = False
    for line in lines[i2:]:
        if line.startswith("## 三"):
            break
        if line.strip().startswith("| 序号"):
            in_tbl = True
            continue
        if in_tbl:
            if re.match(r"^\|\s*\d+\s*\|", line):
                cnt4 += 1
    return declared5, written5, idx4 or cnt4, entries


def main():
    files = sorted(os.listdir(PROV))
    prov_data = []
    for fn in files:
        if not fn.endswith(".md"):
            continue
        code = fn[:2]
        prov = fn[3:-3]
        d5, w5, i4, entries = parse_file(os.path.join(PROV, fn))
        prov_data.append({
            "code": code, "prov": prov, "file": "省份/" + fn,
            "region": REGION.get(code, "其他"),
            "n5": d5, "w5": len(entries), "n4": i4, "entries": entries,
        })

    total5 = sum(p["w5"] for p in prov_data)
    total4 = sum(p["n4"] for p in prov_data)

    # ---------- README.md ----------
    L = []
    L.append("# 全国 4A 及以上旅游景区导游词库")
    L.append("")
    L.append("> 面向导游、研学讲师、文旅从业者的可长期使用的讲解资料库。")
    L.append(">")
    L.append("> - 数据核对时间：**2026-10**")
    L.append("> - 5A 级景区：**%d 家已撰写精编词条**（简介 + 导游词核心稿 + 讲解要点提示）" % total5)
    L.append("> - 4A 级景区：**%d 条名录索引**（不完全收录，仅含名称/区县/类型，暂未撰写导游词）" % total4)
    L.append("> - 官方口径：截至 2025 年底全国 5A 景区 358 家，4A 景区约 4,700–6,000 家")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 一、怎么用")
    L.append("")
    L.append("| 我想… | 去哪里 |")
    L.append("| --- | --- |")
    L.append("| 按省份/地域查景区 | 本文件第三节「分省索引」，或直接打开 `省份/NN-省名.md` |")
    L.append("| 按景区类型查（如「所有石窟类」「所有古镇类」） | [`按类型索引.md`](按类型索引.md) |")
    L.append("| 看编写规范、补写 4A 词条 | [`_规范与模板.md`](_规范与模板.md) |")
    L.append("| 核对 5A 官方名单 | [`_5A名单核对表.md`](_5A名单核对表.md) |")
    L.append("")
    L.append("**重要提醒**")
    L.append("")
    L.append("1. 导游词为通用讲解稿，使用前请核对最新门票、开放时间、预约与限流政策。")
    L.append("2. A 级景区名单动态变化（新增、复核、降级、摘牌），建议每年复核一次。")
    L.append("3. 4A 名录为**不完全收录**，各省 4A 实际数量远超索引条数，可按需补写词条。")
    L.append("4. 黄河壶口瀑布旅游区为陕西延安与山西临汾共有，在两省文件中各收录一次；新疆兵团部分景区与新疆自治区重叠统计，已在文件内注明，全库计数时请勿重复。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 二、总览统计")
    L.append("")
    L.append("| 地域 | 省区市数 | 5A 词条数 | 4A 索引条数 |")
    L.append("| --- | ---: | ---: | ---: |")
    for rg in ["华北", "东北", "华东", "华中", "华南", "西南", "西北"]:
        ps = [p for p in prov_data if p["region"] == rg]
        if not ps:
            continue
        L.append("| %s | %d | %d | %d |" % (rg, len(ps), sum(p["w5"] for p in ps), sum(p["n4"] for p in ps)))
    L.append("| **合计** | **%d** | **%d** | **%d** |" % (len(prov_data), total5, total4))
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 三、分省索引")
    L.append("")
    for rg in ["华北", "东北", "华东", "华中", "华南", "西南", "西北"]:
        ps = [p for p in prov_data if p["region"] == rg]
        if not ps:
            continue
        L.append("### %s地区" % rg)
        L.append("")
        L.append("| 省区市 | 5A词条 | 4A索引 | 文件 |")
        L.append("| --- | ---: | ---: | --- |")
        for p in ps:
            L.append("| %s | %d | %d | [`%s`](%s) |" % (p["prov"], p["w5"], p["n4"], p["file"], p["file"].replace(" ", "%20")))
        L.append("")
    L.append("---")
    L.append("")
    L.append("## 四、全国 5A 景区一览（按省份）")
    L.append("")
    L.append("> 共 %d 条。标记 `*` 者为跨省共有或跨省重复收录。" % total5)
    L.append("")
    for p in prov_data:
        L.append("### %s（%d 家）" % (p["prov"], p["w5"]))
        L.append("")
        L.append("| 序号 | 景区名称 | 所在地 | 类型 | 评定年份 |")
        L.append("| ---: | --- | --- | --- | --- |")
        for i, e in enumerate(p["entries"], 1):
            L.append("| %d | %s | %s | %s | %s |" % (i, e["name"], e["place"], e["type"], e["year"]))
        L.append("")
    L.append("---")
    L.append("")
    L.append("## 五、已知待核实问题（汇总）")
    L.append("")
    L.append("各省文件第三节「待核实与补充事项」均列有明细，全库层面的共性问题如下：")
    L.append("")
    L.append("1. **4A 名录缺口大**：全国 4A 约 4,700–6,000 家，本库仅收录 %d 条，各省覆盖率约 30%%–80%% 不等，需按省文旅厅最新公告续补。" % total4)
    L.append("2. **部分景区等级处于变动中**：桂林乐满地度假世界（2025 年被降低质量等级，广西文件暂未撰写词条）、乔家大院（2019 摘牌、2024 重新确定）、西夏陵（现为 4A 非 5A）等。")
    L.append("3. **官方合并口径**：三峡大坝与屈原故里在文旅部统计中合并为一家；部分省份的联合评定景区（如云台山-神农山-青天河）近年名称有变动。")
    L.append("4. **硬数据多版本**：景区面积、海拔、年代等在不同来源中存在多个版本，词条中已回避或加注，讲解时建议用「约」。")
    L.append("5. **涉民族宗教内容**：西藏、青海、新疆、云南、贵州等地词条已按客观、非猎奇口径处理，并区分「史实」与「相传」。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*本库由 WorkBuddy 于 2026-10 整理，资料来源为公开网络信息与文化和旅游部公开名录。*")

    with open(os.path.join(BASE, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # ---------- 按类型索引.md ----------
    buckets = OrderedDict((c, []) for c, _, _ in TYPE_RULES)
    buckets["T00"] = []
    for p in prov_data:
        for e in p["entries"]:
            for c in norm_types(e["type"]):
                buckets.setdefault(c, []).append({
                    "prov": p["prov"], "name": e["name"],
                    "place": e["place"], "year": e["year"], "file": p["file"],
                })

    M = []
    M.append("# 全国 5A 旅游景区 · 按类型索引")
    L = M
    L.append("")
    L.append("> 本文件把 `省份/*.md` 中已撰写的 **%d 家 5A 景区** 按景区类型重新排列，与 [`README.md`](README.md) 的地域索引互为交叉检索。" % total5)
    L.append(">")
    L.append("> - 一家景区可能同时归入多个类型（按其真实属性）。")
    L.append("> - 类型标签取自 `_规范与模板.md` 第四节受控词表。")
    L.append("> - 点击文件链接可跳转到该省的精编词条。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 类型速览")
    L.append("")
    L.append("| 编号 | 类型 | 景区数 |")
    L.append("| --- | --- | ---: |")
    for c, name, _kws in TYPE_RULES:
        L.append("| %s | [%s](#%s) | %d |" % (c, name, c.lower(), len(buckets.get(c, []))))
    if buckets.get("T00"):
        L.append("| T00 | [其他待归类](#t00) | %d |" % len(buckets["T00"]))
    L.append("")
    L.append("---")
    L.append("")
    for c, name, _kws in TYPE_RULES:
        items = buckets.get(c, [])
        L.append("## %s %s" % (c, name))
        L.append("")
        if not items:
            L.append("*（本类型暂无收录）*")
            L.append("")
            continue
        L.append("共 %d 家。" % len(items))
        L.append("")
        L.append("| 序号 | 景区名称 | 省区市 | 所在地 | 评定年份 |")
        L.append("| ---: | --- | --- | --- | --- |")
        for i, it in enumerate(items, 1):
            L.append("| %d | %s | %s | %s | %s |" % (i, it["name"], it["prov"], it["place"], it["year"]))
        L.append("")
    if buckets.get("T00"):
        L.append("## T00 其他待归类")
        L.append("")
        L.append("| 序号 | 景区名称 | 省区市 | 类型原文 | 评定年份 |")
        L.append("| ---: | --- | --- | --- | --- |")
        for i, it in enumerate(buckets["T00"], 1):
            L.append("| %d | %s | %s | - | %s |" % (i, it["name"], it["prov"], it["year"]))
        L.append("")
    L.append("---")
    L.append("")
    L.append("## 附：4A 景区按类型检索说明")
    L.append("")
    L.append("4A 景区本库仅做名录索引（未撰写导游词），按类型检索请直接打开对应省份文件，查看「二、4A级景区名录索引」表格中的「类型」列。")
    L.append("")
    L.append("如需把 4A 也纳入本类型索引，可按 `_规范与模板.md` 的格式补写词条后重新生成本文件。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*本索引由脚本从 `省份/*.md` 自动解析生成，随省份文件更新可重新生成。*")

    with open(os.path.join(BASE, "按类型索引.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(M))

    print("5A 词条总数:", total5)
    print("4A 索引总数:", total4)
    for p in prov_data:
        print("%s %s: 5A=%d(声明%d) 4A=%d" % (p["code"], p["prov"], p["w5"], p["n5"], p["n4"]))


if __name__ == "__main__":
    main()
