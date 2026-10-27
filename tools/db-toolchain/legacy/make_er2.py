import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1800, 1100
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

HEI = r"C:\Windows\Fonts\simhei.ttf"
SUN = r"C:\Windows\Fonts\simsun.ttc"

f_title = ImageFont.truetype(HEI, 34)
f_cn = ImageFont.truetype(SUN, 29)
f_key = ImageFont.truetype(SUN, 25)
f_label = ImageFont.truetype(HEI, 29)
f_leg = ImageFont.truetype(SUN, 28)

TABLE_FILL = (234, 240, 248)
TABLE_EDGE = (47, 85, 151)
IMPL_FILL = (253, 238, 226)
IMPL_EDGE = (197, 90, 17)
GREY = (127, 127, 127)

BW, BH = 430, 150
boxes = {}


def text(x, y, s, font, fill=(31, 31, 31), anchor="la"):
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)


def entity(x, y, name, cn, keys, impl=False):
    edge = IMPL_EDGE if impl else TABLE_EDGE
    fill = IMPL_FILL if impl else TABLE_FILL
    d.rectangle([x, y, x + BW, y + BH], fill="white", outline=edge, width=3)
    d.rectangle([x, y, x + BW, y + 64], fill=fill, outline=edge, width=3)
    text(x + 15, y + 32, name, f_title,
         fill=(132, 60, 12) if impl else (31, 56, 100), anchor="lm")
    text(x + 15, y + 90, cn, f_cn, fill=(60, 60, 60), anchor="lm")
    text(x + 15, y + 126, keys, f_key, fill=(90, 90, 90), anchor="lm")
    boxes[name] = (x, y, BW, BH)


entity(30, 30, "poi_facility", "设施网点", "district_id → district")
entity(670, 30, "community_gap", "社区短板", "district_id → district")
entity(1310, 30, "site_candidate", "选址候选点", "district_id → district")

entity(670, 445, "district", "社区片区", "片区主数据，被各表引用")

entity(30, 860, "resident_assessment", "居民生活圈评估", "district_id → district")
entity(670, 860, "assessment_dimension", "评估维度得分", "assessment_id → 评估表")
entity(1310, 860, "simulation_record", "网点增设模拟", "district_id → district")

entity(1310, 445, "merchant_intent", "商户开店意向（已实现）", "当前独立存储，无外键", impl=True)


def get_pt(name, side, off=0):
    x, y, w, h = boxes[name]
    return {"l": (x, y + h / 2 + off), "r": (x + w, y + h / 2 + off),
            "t": (x + w / 2 + off, y), "b": (x + w / 2 + off, y + h)}[side]


def dashed(p1, p2, color=GREY, width=3, dash=16, gap=10):
    x1, y1 = p1
    x2, y2 = p2
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist == 0:
        return
    ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
    t = 0
    while t < dist:
        e = min(t + dash, dist)
        d.line([x1 + ux * t, y1 + uy * t, x1 + ux * e, y1 + uy * e], fill=color, width=width)
        t = e + gap


def edge(a, b, sa, sb, oa=0, ob=0):
    p1, p2 = get_pt(a, sa, oa), get_pt(b, sb, ob)
    dashed(p1, p2)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = max(math.hypot(dx, dy), 1)
    ux, uy = dx / n, dy / n
    # perpendicular offset so labels don't sit on the line
    px, py = -uy * 20, ux * 20
    text(p1[0] + ux * 46 + px, p1[1] + uy * 46 + py, "1", f_label,
         fill=(47, 85, 151), anchor="mm")
    text(p2[0] - ux * 46 + px, p2[1] - uy * 46 + py, "N", f_label,
         fill=(47, 85, 151), anchor="mm")


edge("district", "poi_facility", "l", "r", oa=-45)
edge("district", "community_gap", "t", "b")
edge("district", "site_candidate", "r", "l", oa=-45)
edge("district", "resident_assessment", "l", "r", oa=45)
edge("district", "assessment_dimension", "b", "t")
edge("district", "simulation_record", "r", "l", oa=45)

# legend
ly = 1055
x = 40
for fill, edge_c, label in [
    (IMPL_FILL, IMPL_EDGE, "已实现表"),
    (TABLE_FILL, TABLE_EDGE, "规划扩展表"),
    (None, None, "1:N 关联（外键见方框内说明）"),
]:
    if fill:
        d.rectangle([x, ly - 15, x + 36, ly + 15], fill=fill, outline=edge_c, width=3)
    else:
        dashed((x, ly), (x + 36, ly), width=3)
    text(x + 48, ly, label, f_leg, fill=(60, 60, 60), anchor="lm")
    x += 48 + d.textlength(label, font=f_leg) + 100

img.save(r"C:\Users\123456\Desktop\Pro\work\er_diagram.png")
print("saved", img.size)
