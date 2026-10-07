# -*- coding: utf-8 -*-
"""
把 README / 按类型索引 / 省份/*.md / 规范 / 名单底稿
合并为单一文件：全国4A及以上景区导游词库.md
章节用显式 <a id="secN"> 锚点，保证目录可跳转。
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
PROV = os.path.join(BASE, "省份")
OUT = os.path.join(BASE, "全国4A及以上景区导游词库.md")

FENCE = re.compile(r"^\s{0,3}`{3,}")


def shift(text, n):
    """把所有 markdown 标题统一降级 n 级；跳过代码块"""
    out = []
    fence = None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if m:
            ticks = m.group(0).strip()
            if fence is None:
                fence = ticks
                out.append(line)
                continue
            elif len(ticks) >= len(fence):
                fence = None
                out.append(line)
                continue
        if fence is not None:
            out.append(line)
            continue
        m = re.match(r"^(#{1,6})(\s+.*)$", line)
        if m:
            lvl = min(len(m.group(1)) + n, 6)
            out.append("#" * lvl + m.group(2))
            continue
        out.append(line)
    return "\n".join(out)


def strip_links(text):
    """单文件化后内部相对链接失效，降级为纯文本"""
    text = re.sub(r"\[(`?[^`\]]+?`?)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"省份/(\d\d)-([^.`]+)\.md", r"\1 \2", text)
    return text


def main():
    files = sorted(f for f in os.listdir(PROV) if f.endswith(".md"))
    p = []

    # ============ 封面 ============
    p.append("# 全国 4A 及以上旅游景区导游词库（单文件合集）\n")
    p.append(
        "> 面向导游、研学讲师、文旅从业者的可长期使用的讲解资料库。\n"
        ">\n"
        "> - 数据核对时间：**2026-10**\n"
        "> - 5A 级景区：**360 篇精编词条**（简介 + 导游词核心稿 + 讲解要点提示），唯一景区 358 家\n"
        "> - 4A 级景区：**2,894 条名录索引**（不完全收录，仅名称/区县/类型，未撰写导游词）\n"
        "> - 官方口径：截至 2025 年底全国 5A 景区 358 家、4A 景区约 4,700–6,000 家\n"
        ">\n"
        "> **目录**\n"
        ">\n"
        "> | 章节 | 内容 |\n"
        "> | --- | --- |\n"
        "> | [一、怎么用](#sec1) | 导航说明与三条重要提醒 |\n"
        "> | [二、总览统计](#sec2) | 七大地域的 5A/4A 数量 |\n"
        "> | [三、分省索引](#sec3) | 32 个省级行政区速查表 |\n"
        "> | [四、按类型索引](#sec4) | 按 T01–T18 景区类型重排 |\n"
        "> | [五、全国 5A 一览](#sec5) | 360 家景区名称/所在地/类型/年份 |\n"
        "> | [六、已知待核实问题](#sec6) | 全库共性遗留问题 |\n"
        "> | [七、分省导游词正文](#sec7) | **正文主体**：32 省 × 5A 精编词条 + 4A 名录 |\n"
        "> | [八、附录一](#sec8) | 编写规范与词条模板 |\n"
        "> | [九、附录二](#sec9) | 5A 名单核对表 |\n"
    )
    p.append("\n---\n")

    # ============ README 拆分 ============
    readme = strip_links(open(os.path.join(BASE, "README.md"), encoding="utf-8").read())
    # README 本身层级即为 # 总标题 / ## 章 / ### 节，删掉总标题后可直接用
    readme = readme.split("\n", 1)[1]

    cut = re.search(r"^## 四、全国 5A 景区一览", readme, flags=re.M)
    head, tail = (readme[:cut.start()], readme[cut.start():]) if cut else (readme, "")
    tail = tail.replace("## 四、全国 5A 景区一览", "## 五、全国 5A 景区一览")
    tail = tail.replace("## 五、已知待核实问题", "## 六、已知待核实问题")
    # 正文导读改为正文章节
    head = head.replace("本文件第三节「分省索引」，或直接打开 `省份/NN-省名.md`",
                        "「三、分省索引」与「七、分省导游词正文」")
    head = head.replace("查看「二、4A级景区名录索引」表格中的「类型」列",
                        "查看该省「二、4A级景区名录索引」表格中的「类型」列")

    p.append('<a id="sec1"></a>\n')
    p.append(head.rstrip() + "\n")
    p.append("\n---\n")

    # ============ 四、按类型索引 ============
    ti = strip_links(open(os.path.join(BASE, "按类型索引.md"), encoding="utf-8").read())
    ti = ti.split("\n", 1)[1]
    ti = shift(ti, 1)
    p.append('<a id="sec4"></a>\n')
    p.append("## 四、按类型索引\n")
    p.append(ti.rstrip() + "\n")
    p.append("\n---\n")

    # ============ 五、六（来自 README 后半） ============
    p.append('<a id="sec5"></a>\n')
    p.append(tail.rstrip() + "\n")
    p.append("\n---\n")

    # ============ 七、分省正文 ============
    p.append('<a id="sec7"></a>\n')
    p.append("## 七、分省导游词正文\n")
    p.append(
        "> 共 32 个省级行政区，**本合集的内容主体**。\n"
        ">\n"
        "> - 每家 5A 景区：信息表 + 景区简介 + 导游词核心稿 + 讲解要点提示（必讲／数据锚点／常见误区／互动设计）\n"
        "> - 每省 4A：名录索引表格（**不完全收录**，仅名称／区县／类型）\n"
        "> - 每省末尾列有该省的「待核实与补充事项」\n"
        ">\n"
        "> **省份速跳**：\n"
        "> " + "　".join("[%s %s](#p%s)" % (f[:2], f[3:-3], f[:2]) for f in files) + "\n"
    )
    for fn in files:
        txt = open(os.path.join(PROV, fn), encoding="utf-8").read()
        body = strip_links(txt.split("\n", 1)[1])
        body = shift(body, 2)
        p.append('\n<a id="p%s"></a>\n' % fn[:2])
        p.append("### %s %s\n" % (fn[:2], fn[3:-3]))
        p.append(body.rstrip() + "\n")
        p.append("\n---\n")

    # ============ 八、附录一 ============
    spec = open(os.path.join(BASE, "_规范与模板.md"), encoding="utf-8").read()
    sb = shift(spec.split("\n", 1)[1], 1)
    p.append('<a id="sec8"></a>\n')
    p.append("## 八、附录一：编写规范与模板\n")
    p.append(sb.rstrip() + "\n")
    p.append("\n---\n")

    # ============ 九、附录二 ============
    lst = open(os.path.join(BASE, "_5A名单核对表.md"), encoding="utf-8").read()
    lb = shift(lst.split("\n", 1)[1], 1)
    p.append('<a id="sec9"></a>\n')
    p.append("## 九、附录二：5A 名单核对表\n")
    p.append(lb.rstrip() + "\n")
    p.append(
        "\n---\n\n*本合集由 WorkBuddy 于 2026-10 整理，资料来源为公开网络信息与文化和旅游部公开名录。*"
        "\n*A 级景区名单动态变化（新增／复核／降级／摘牌），使用前请核对最新公告；门票、开放时间、预约政策请出行前另行确认。*\n"
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(p))

    print("输出：", OUT)
    print("大小：%.1f KB" % (os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
