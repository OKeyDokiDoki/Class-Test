# -*- coding: utf-8 -*-
"""从 db_model.py 生成《数据库设计说明书》Word 文档，并转换为 PDF。

所属链路
    db_model.py  --本脚本-->  docs/database/数据库设计说明书.docx  +  .pdf
    （正文插图来自 gen_diagrams.py 生成的 docs/database/图/）

产出
    docs/database/数据库设计说明书.docx   完整设计文档：数据项、数据模型、数据规划架构、
                                          表结构、存储规划、建表脚本，含静态目录页码
    docs/database/数据库设计说明书.pdf    由 docx 转换而成

工作原理（两遍编译）
    第一遍：目录页码先填占位符，导出临时 PDF；
    第二遍：用 pypdf 从临时 PDF 提取各章节实际页码，回填后重新生成 docx，再转正式 PDF。

依赖
    pip install python-docx pypdf Pillow
    LibreOffice Kit（docx → pdf 转换），路径可用环境变量覆盖：
        LIBREOFFICE_KIT_CLI  默认指向 DSH 自带的 libreoffice-kit cli.js
        NODE_BIN             默认自动查找 PATH 上的 node

运行
    cd tools/db-toolchain
    python build_design_doc.py

注意
    运行前请先执行 gen_diagrams.py，否则正文插图目录 docs/database/图/ 里没有图片。
"""
import io
import os
import re
import shutil
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import db_model as M
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

# --- 路径约定 ---------------------------------------------------------------
# 本文件位于 <repo>/tools/db-toolchain/，向上两级就是仓库根目录。
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
# 交付物默认直接写进仓库 docs/database/。
OUT_DIR = os.environ.get("DB_DESIGN_OUT") or os.path.join(REPO, "docs", "database")
TEMPLATE = os.path.join(HERE, "template.docx")
FIG_DIR = os.path.join(OUT_DIR, "图")
DOCX = os.path.join(OUT_DIR, "数据库设计说明书.docx")
PDF = os.path.join(OUT_DIR, "数据库设计说明书.pdf")
# 两遍编译的临时文件，统一放这里，避免污染仓库。
TMP_DIR = os.path.join(HERE, ".tmp")
os.makedirs(TMP_DIR, exist_ok=True)

TABLES = M.TABLES
BY = M.TABLE_BY_NAME
DOMAINS = M.DOMAINS

# --------------------------------------------------------------------------
# outline (level 1/2 entries appear in TOC)
# --------------------------------------------------------------------------
OUTLINE = [
    (1, "1 引言"),
    (2, "1.1 编写目的"),
    (2, "1.2 项目范围与数据边界"),
    (2, "1.3 设计依据"),
    (2, "1.4 术语与缩略语"),
    (2, "1.5 数据设计原则"),
    (1, "2 数据项"),
    (2, "2.1 数据项识别方法"),
    (2, "2.2 数据项分类与编码"),
    (2, "2.3 核心数据项清单"),
    (2, "2.4 数据项值域与码表"),
    (2, "2.5 数据项质量规则"),
    (1, "3 数据模型"),
    (2, "3.1 建模方法与 dbdiagram.io"),
    (2, "3.2 概念模型：主题域总体关系"),
    (2, "3.3 逻辑模型：分域实体关系"),
    (2, "3.4 实体关系与基数说明"),
    (2, "3.5 范式与反范式设计"),
    (2, "3.6 DBML 模型文件说明"),
    (1, "4 数据规划架构"),
    (2, "4.1 总体架构"),
    (2, "4.2 分层设计"),
    (2, "4.3 主题域与数据分布"),
    (2, "4.4 数据流转与更新机制"),
    (2, "4.5 数据治理"),
    (2, "4.6 数据安全与隐私"),
    (2, "4.7 数据生命周期"),
    (1, "5 数据库环境与规范"),
    (2, "5.1 运行环境"),
    (2, "5.2 命名规范"),
    (2, "5.3 数据类型映射"),
    (2, "5.4 主键、外键与审计字段"),
    (1, "6 数据表设计"),
    (2, "6.1 数据表清单"),
    (2, "6.2 用户与画像域"),
    (2, "6.3 空间与设施域"),
    (2, "6.4 居民生活圈评估域"),
    (2, "6.5 商户选址与招商域"),
    (2, "6.6 社区治理域"),
    (2, "6.7 数据运营与同步域"),
    (2, "6.8 索引与约束汇总"),
    (2, "6.9 视图设计"),
    (1, "7 存储结构规划"),
    (2, "7.1 存储总体布局"),
    (2, "7.2 表空间与数据文件"),
    (2, "7.3 分区策略"),
    (2, "7.4 索引存储策略"),
    (2, "7.5 LOB 与大对象存储"),
    (2, "7.6 容量估算"),
    (2, "7.7 备份与恢复"),
    (2, "7.8 归档与清理"),
    (2, "7.9 性能与扩展"),
    (1, "8 建表脚本与验证"),
    (2, "8.1 脚本清单"),
    (2, "8.2 Oracle 建表步骤"),
    (2, "8.3 H2 与 MySQL 适配"),
    (2, "8.4 执行验证结果"),
    (2, "8.5 V1 到 V2 迁移"),
    (2, "8.6 后续代码接入"),
    (1, "9 结论"),
]

CHAPTERS = [t for lv, t in OUTLINE if lv == 1]

# --------------------------------------------------------------------------
# stats
# --------------------------------------------------------------------------
N_TABLES = len(TABLES)
N_COLS = sum(len(t["cols"]) for t in TABLES)
N_FKS = sum(1 for t in TABLES for c in t["cols"] if c["fk"])
N_CHECKS = sum(1 for t in TABLES for c in t["cols"] if c["check"]) + sum(len(t["checks"]) for t in TABLES)
N_UNIQ = sum(1 for t in TABLES for c in t["cols"] if c["uniq"]) + sum(1 for t in TABLES for _n, _c, u in t["indexes"] if u)
N_INDEX = sum(len(t["indexes"]) for t in TABLES)
N_ROWS = sum(t["rows_3y"] for t in TABLES)
DOMAIN_TABLES = {dk: [t for t in TABLES if t["domain"] == dk] for dk in DOMAINS}


def storage(t):
    a = t["rows_3y"] * t["row_bytes"] / 1024 / 1024
    b = t["rows_3y"] * t["lob_bytes"] / 1024 / 1024
    c = (a + b) * 0.24
    return a, b, c


TOTAL_DATA = sum(storage(t)[0] for t in TABLES)
TOTAL_LOB = sum(storage(t)[1] for t in TABLES)
TOTAL_IDX = sum(storage(t)[2] for t in TABLES)

# data item numbering
DOMAIN_PREFIX = {dk: 0 for dk in DOMAINS}
DI_ID = {}
for t in TABLES:
    for c in t["cols"]:
        DOMAIN_PREFIX[t["domain"]] += 1
        DI_ID[(t["name"], c["name"])] = f"DI-{t['domain']}-{DOMAIN_PREFIX[t['domain']]:03d}"

# --------------------------------------------------------------------------
# docx globals and helpers
# --------------------------------------------------------------------------
doc = None
CUR_CH = 0
TBL_NO = Counter()
FIG_NO = Counter()
PAGE_MAP = {}


def set_font(run, name="宋体", size=12, bold=False, color="000000", italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), name)


def fmt_para(p, indent=True, line=1.5, before=0, after=0, align=None, keep_next=False):
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = keep_next
    if align is not None:
        p.alignment = align
    pPr = p._p.get_or_add_pPr()
    # Chinese first-line indent: 2 characters
    for el in pPr.findall(qn("w:ind")):
        pPr.remove(el)
    if indent:
        ind = OxmlElement("w:ind")
        ind.set(qn("w:firstLineChars"), "200")
        ind.set(qn("w:firstLine"), "480")
        pPr.append(ind)


def P(text, indent=True, size=12, bold=False, align=None, color="000000", before=0, after=0, keep_next=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_font(r, "宋体", size, bold, color)
    fmt_para(p, indent, 1.5, before, after, align, keep_next)
    return p


def BULLET(text, size=12):
    p = doc.add_paragraph()
    r = p.add_run("• " + text)
    set_font(r, "宋体", size)
    fmt_para(p, False, 1.5)
    p.paragraph_format.left_indent = Cm(0.74)
    p.paragraph_format.first_line_indent = Cm(-0.37)
    return p


def H1(text):
    global CUR_CH
    CUR_CH = int(text.split(" ")[0])
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.page_break_before = True
    r = p.add_run(text)
    set_font(r, "黑体", 20, True, "1F3864")
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.keep_with_next = True
    # bottom rule
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "2F5597")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def H2(text):
    p = doc.add_paragraph(style="Heading 2")
    r = p.add_run(text)
    set_font(r, "黑体", 15, True, "1F3864")
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    return p


def H3(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_font(r, "黑体", 12, True, "2F5597")
    fmt_para(p, False, 1.3, 8, 4, None, True)
    return p


def caption(text, kind="table"):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_font(r, "宋体", 10.5, False, "000000")
    fmt_para(p, False, 1.0, 6 if kind == "table" else 4, 3 if kind == "table" else 6,
             WD_ALIGN_PARAGRAPH.CENTER, keep_next=(kind == "table"))
    if kind == "table" and doc.tables:
        # 表题置于表上方
        doc.tables[-1]._tbl.addprevious(p._p)
    return p


def table_caption(text):
    TBL_NO[CUR_CH] += 1
    return caption(f"表 {CUR_CH}-{TBL_NO[CUR_CH]} {text}", "table")


def fig_caption(text, kind="figure"):
    FIG_NO[CUR_CH] += 1
    return caption(f"图 {CUR_CH}-{FIG_NO[CUR_CH]} {text}", "figure")


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def set_table_borders(table, color="BFBFBF", sz="4"):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    cellMar = OxmlElement("w:tblCellMar")
    for side, w in (("top", "30"), ("left", "70"), ("bottom", "30"), ("right", "70")):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), w)
        el.set(qn("w:type"), "dxa")
        cellMar.append(el)
    tblPr.append(cellMar)


def set_col_widths(table, widths_cm):
    grid = table._tbl.tblGrid
    for c, w in zip(grid.findall(qn("w:gridCol")), widths_cm):
        c.set(qn("w:w"), str(int(w * 567)))
    for row in table.rows:
        i = 0
        for tc in row._tr.tc_lst:
            span = 1
            tcPr = tc.tcPr
            if tcPr is not None and tcPr.gridSpan is not None:
                span = tcPr.gridSpan.val
            w = sum(widths_cm[i:i + span])
            i += span
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.append(tcW)
            tcW.set(qn("w:w"), str(int(w * 567)))
            tcW.set(qn("w:type"), "dxa")


def add_table(headers, rows, widths, font_size=8.5, header_size=9,
              keep_together=True, align_center=None, first_col_center=False):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    hdr = table.rows[0]
    # repeat header
    trPr = hdr._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        shade(cell, "2F5597")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, "宋体", header_size, True, "FFFFFF")
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
    for ri, row in enumerate(rows):
        tr = table.add_row()
        trPr = tr._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        if keep_together and ri < len(rows) - 1:
            for cell in tr.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if ri % 2 == 1:
                shade(cell, "F2F5FA")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            if align_center is not None and ci in align_center:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif first_col_center and ci == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            set_font(r, "宋体", font_size, False, "000000")
    set_col_widths(table, widths)
    return table


def add_image(path, width_cm=14.4, max_h_cm=19.0):
    im = Image.open(path)
    w, h = im.size
    width = width_cm
    height = width * h / w
    if height > max_h_cm:
        height = max_h_cm
        width = height * w / h
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(path, width=Cm(width), height=Cm(height))
    return p


def code_block(text, size=8):
    p = doc.add_paragraph()
    fmt_para(p, False, 1.0, 4, 4)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F5F7FA")
    pPr.append(shd)
    for i, line in enumerate(text.split("\n")):
        if i:
            p.add_run().add_break()
        r = p.add_run(line if line else " ")
        set_font(r, "Consolas", size, False, "333333")
    return p


def bullet_list(items, size=12):
    for it in items:
        BULLET(it, size)


def note_box(text, size=10.5):
    p = doc.add_paragraph()
    fmt_para(p, False, 1.2, 4, 6)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "FFF8E8")
    pPr.append(shd)
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.right_indent = Cm(0.3)
    r = p.add_run(text)
    set_font(r, "宋体", size, False, "7F4F00")
    return p


# --------------------------------------------------------------------------
# cover, toc, header/footer
# --------------------------------------------------------------------------
def setup_cover():
    global doc
    ps = doc.paragraphs
    # cover title
    p = ps[8]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    r = p.add_run("数据库设计说明书")
    set_font(r, "黑体", 30, True, "1F3864")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = ps[9]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    r = p.add_run("城市 15 分钟便民生活圈")
    set_font(r, "黑体", 18, True, "2F5597")
    r.add_break()
    r = p.add_run("与小微开店智能助手")
    set_font(r, "黑体", 18, True, "2F5597")
    r.add_break()
    r = p.add_run("V2.0 ｜ 2026 年 10 月 ｜ 6 组")
    set_font(r, "宋体", 12, False, "595959")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)


def setup_toc_title():
    p = doc.paragraphs[12]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    r = p.add_run("目    录")
    set_font(r, "黑体", 22, True, "1F3864")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def clear_after_toc_title():
    body = doc.element.body
    toc_title = doc.paragraphs[12]._p
    children = list(body.iterchildren())
    start = children.index(toc_title) + 1
    for ch in children[start:]:
        if ch.tag == qn("w:sectPr"):
            continue
        body.remove(ch)


def add_toc_entries():
    toc_title = doc.paragraphs[12]
    anchor = toc_title._p
    for level, title in OUTLINE:
        p_el = OxmlElement("w:p")
        anchor.addnext(p_el)
        anchor = p_el
        from docx.text.paragraph import Paragraph
        p = Paragraph(p_el, toc_title._parent)
        pPr = p._p.get_or_add_pPr()
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:leader"), "dot")
        tab.set(qn("w:pos"), "8280")
        tabs.append(tab)
        pPr.append(tabs)
        page = PAGE_MAP.get(title, "00")
        r = p.add_run(title)
        set_font(r, "宋体", 10.5 if level == 1 else 9.5, level == 1, "000000")
        r = p.add_run("\t" + str(page))
        set_font(r, "Times New Roman", 9.5, level == 1, "000000")
        pf = p.paragraph_format
        pf.line_spacing = 1.2
        pf.space_before = Pt(2 if level == 1 else 0.5)
        pf.space_after = Pt(0)
        if level == 2:
            pf.left_indent = Cm(0.65)


def add_header_footer():
    section = doc.sections[0]
    section.different_first_page_header_footer = True
    # 封面单独使用空页眉，避免出现横线
    first_header = section.first_page_header
    first_header.is_linked_to_previous = False
    for fp in first_header.paragraphs:
        fp.text = ""
        fp.style = doc.styles["Normal"]
        pPr = fp._p.get_or_add_pPr()
        for bdr in pPr.findall(qn("w:pBdr")):
            pPr.remove(bdr)
        for pstyle in pPr.findall(qn("w:pStyle")):
            pPr.remove(pstyle)
    # header
    header = section.header
    hp = header.paragraphs[0]
    hp.text = ""
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run("城市 15 分钟便民生活圈与小微开店智能助手 · 数据库设计说明书")
    set_font(r, "宋体", 8.5, False, "808080")
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "BFBFBF")
    pBdr.append(bottom)
    pPr.append(pBdr)

    # footer
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def field(instr, ph):
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), instr)
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        rFonts = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia"):
            rFonts.set(qn(a), "宋体")
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "18")
        rPr.append(rFonts)
        rPr.append(sz)
        r.append(rPr)
        t = OxmlElement("w:t")
        t.text = ph
        r.append(t)
        fld.append(r)
        fp._p.append(fld)

    r = fp.add_run("第 ")
    set_font(r, "宋体", 9, False, "595959")
    field(" PAGE ", "1")
    r = fp.add_run(" 页  共 ")
    set_font(r, "宋体", 9, False, "595959")
    field(" NUMPAGES ", "1")
    r = fp.add_run(" 页")
    set_font(r, "宋体", 9, False, "595959")


# --------------------------------------------------------------------------
# chapter 1
# --------------------------------------------------------------------------
def ch1():
    H1("1 引言")
    H2("1.1 编写目的")
    P("本文档是“城市 15 分钟便民生活圈与小微开店智能助手”数据库设计阶段的完整成果，用于指导课程项目的开发、联调、测试与验收。文档以项目需求文档、GitHub 仓库 OKeyDokiDoki/Class-Test 中的现有代码以及《数据项约定规范》为基础编写，覆盖数据项识别、数据模型设计、数据规划架构、物理表结构、存储结构规划、建表脚本与执行验证。")
    P("与只描述“当前代码已落库对象”的说明不同，本文档面向系统完整业务闭环进行目标态设计：既保留现有 merchant_intent 表并给出向后兼容的迁移路径，也把居民评估、商户选址、社区治理、数据同步等目前仍使用演示数据的模块纳入统一数据模型。开发阶段可按第 8 章的脚本直接建表，再按第 8.6 节的映射逐步接入 JPA 实体。")
    P(f"文档中的模型共划分 {len(DOMAINS)} 个主题域、{N_TABLES} 张表、{N_COLS} 个字段、{N_FKS} 个外键。全部表结构由同一份模型定义生成 DBML、Oracle/H2/MySQL 建表脚本、数据字典和 ER 图，避免文档、脚本与代码三处不一致。")

    H2("1.2 项目范围与数据边界")
    P("系统面向居民、小微商户和社区管理员三类角色，业务范围包括身份与画像、居民 15 分钟生活圈评估、商户智能选址与招商提报、社区短板识别与网点模拟、后台数据同步与运维五个模块。数据库需要同时承载空间主数据、设施 POI、人口栅格、步行路网、画像权重、评估结果、选址候选点、招商意向和治理台账。")
    P("数据边界如下：")
    bullet_list([
        "纳入范围：公开地图 POI、政务人口栅格、城市路网、用户在系统中主动填写的画像标签与业务表单、系统计算产生的评分与匹配结果。",
        "排除范围：工商注册、行政审批、线上交易与支付结算等行政或交易数据；居民身份证号、精确住址等敏感个人信息。",
        "隐私边界：手机号只保存加盐 SHA-256 哈希；商户联系方式加密存储并单独授权访问；对外展示统一脱敏。",
        "空间边界：以步行方式为主，15 分钟按 1.2 m/s 估算约 1080 米，不计算驾车、公交等其他方式。",
        "时间边界：业务时间统一以 UTC 存储，展示层转换为 Asia/Shanghai；POI 数据更新周期不超过 15 天。",
    ])
    P("按一个街道、12 个社区、约 5 万居民的课程项目规模估算，3 年在线数据约 609 万行、1.5 GB（不含备份与临时空间）。该规模在 Oracle 23ai Free 的 12 GB 用户数据上限内，并预留约 2 倍增长空间。")

    H2("1.3 设计依据")
    bullet_list([
        "《城市 15 分钟便民生活圈与小微开店智能助手》需求文档 V1.0（6 组，2026-09-19）。",
        "GitHub 仓库 https://github.com/OKeyDokiDoki/Class-Test 中的前端、后端与 docs 目录。",
        "《数据项约定规范》docs/DATA_CONVENTIONS.md（字段命名、类型、枚举与空值约定）。",
        "《项目架构》docs/ARCHITECTURE.md（Oracle 读写分离、H2 开发库、模块边界）。",
        "Oracle Database 23ai Free 官方语法；H2 2.2.224（MODE=Oracle）；MySQL 8.0 作为可选方言。",
        "建模工具 dbdiagram.io 及其 DBML 文本建模语言。",
    ])

    H2("1.4 术语与缩略语")
    add_table(
        ["术语", "英文/缩写", "说明"],
        [
            ["生活圈", "Life Circle", "以步行 15 分钟可达范围为边界的社区服务圈，约 1080 米。"],
            ["兴趣点", "POI", "Point of Interest，指菜场、医院、学校、公交站等设施网点。"],
            ["等时圈", "Isochrone", "基于路网与步行速度计算出的等时间可达区域。"],
            ["画像", "Profile", "由标签、维度和权重构成的用户特征集合。"],
            ["原始层", "ODS", "Operational Data Store，原样落地外部接口报文的数据层。"],
            ["明细层", "DWD", "Data Warehouse Detail，经过清洗、标准化后的业务明细数据层。"],
            ["应用层", "ADS", "Application Data Service，面向看板和接口的汇总/快照数据层。"],
            ["DBML", "Database Markup Language", "dbdiagram.io 使用的文本化数据库建模语言。"],
            ["表空间", "Tablespace", "Oracle 中组织数据文件的逻辑存储单元。"],
            ["分区", "Partition", "按时间或范围把大表拆成可独立管理的物理段。"],
            ["SCN", "System Change Number", "Oracle 数据库一致性读使用的系统变更号。"],
        ],
        [2.2, 3.6, 8.8],
        font_size=9,
        first_col_center=False,
    )
    caption("表 1-1 术语与缩略语", "table")

    H2("1.5 数据设计原则")
    bullet_list([
        "业务可解释：每个评分、候选点和匹配结果都能追溯到输入数据、权重和评分项，不用黑盒字段代替过程数据。",
        "一数一源：片区、设施类别、用户、画像标签等主数据只在一个表中维护，其他表通过外键引用，避免重复维护。",
        "分层存放：原始报文进 ODS，清洗后的业务实体进 DWD，评分快照和看板指标进 ADS，职责边界清晰。",
        "适度冗余：为查询性能保留少量派生字段（如评估表中的画像标签、快照表中的覆盖人口），但必须由程序或批处理保证一致。",
        "枚举一致：面向展示的中文枚举（充足/基本满足/待改善、高/中/低）与前端逐字一致；内部状态使用英文编码。",
        "安全最小化：不存明文手机号、身份证号和精确住址；联系方式加密、脱敏、按角色授权。",
        "可扩展：片区采用自关联三级结构，保留 city_code，可按城市水平扩展；大表按时间分区，便于归档。",
        "时间统一：数据库存 UTC，接口返回 ISO Instant，前端按本地时区展示，避免跨时区歧义。",
    ])


# --------------------------------------------------------------------------
# chapter 2
# --------------------------------------------------------------------------
DATA_ITEMS = [
    ("app_user", "user_code"), ("app_user", "role_code"), ("app_user", "phone_hash"),
    ("app_user", "status"),
    ("user_profile", "profile_type"), ("user_profile", "profile_label"),
    ("user_profile", "confidence"), ("user_profile", "is_current"),
    ("profile_tag", "tag_code"), ("profile_tag", "dimension_code"),
    ("profile_dimension_weight", "weight"),
    ("district", "district_code"), ("district", "district_level"),
    ("district", "center_lng"), ("district", "center_lat"), ("district", "resident_count"),
    ("population_grid", "grid_code"), ("population_grid", "population"),
    ("population_grid", "density"), ("population_grid", "data_date"),
    ("road_segment", "segment_code"), ("road_segment", "length_m"),
    ("road_segment", "walk_time_s"), ("facility_category", "category_code"),
    ("poi_facility", "poi_name"), ("poi_facility", "lng"), ("poi_facility", "lat"),
    ("poi_facility", "business_status"), ("poi_facility", "source_poi_id"),
    ("resident_assessment", "resident_code"), ("resident_assessment", "radius_m"),
    ("resident_assessment", "total_score"), ("resident_assessment", "insight"),
    ("assessment_dimension", "dimension_score"), ("assessment_dimension", "weight"),
    ("assessment_facility_stat", "facility_count"),
    ("assessment_facility_stat", "nearest_distance_m"),
    ("assessment_facility_stat", "status"),
    ("district_score_snapshot", "coverage_pct"), ("district_score_snapshot", "avg_score"),
    ("district_score_snapshot", "rank_no"),
    ("site_candidate", "candidate_name"), ("site_candidate", "business_type"),
    ("site_candidate", "population_index"), ("site_candidate", "competitor_count"),
    ("site_candidate", "demand_level"), ("site_candidate", "competition_level"),
    ("site_candidate", "rent_min"), ("site_candidate", "rent_max"),
    ("site_candidate", "site_score"), ("site_score_item", "score_item"),
    ("site_score_item", "item_score"),
    ("merchant_intent", "merchant_name"), ("merchant_intent", "contact"),
    ("merchant_match", "fit_score"),
    ("community_gap", "area_name"), ("community_gap", "issue"),
    ("community_gap", "gap_level"), ("community_gap", "uncovered_residents"),
    ("community_gap", "priority_no"),
    ("simulation_record", "before_coverage"), ("simulation_record", "after_coverage"),
    ("simulation_record", "benefited_residents"),
    ("sync_batch", "batch_no"), ("sync_batch", "sync_type"), ("sync_batch", "status"),
    ("sync_batch", "insert_count"), ("sync_batch", "update_count"),
    ("sync_batch", "close_count"),
    ("poi_change_log", "change_type"), ("data_quality_issue", "rule_code"),
    ("data_quality_issue", "severity"), ("ods_poi_raw", "process_status"),
]

VALUE_DOMAIN = {
    ("app_user", "role_code"): "RESIDENT / MERCHANT / COMMUNITY / ADMIN",
    ("app_user", "status"): "ACTIVE / DISABLED / DELETED",
    ("app_user", "phone_hash"): "64 位十六进制哈希",
    ("user_profile", "profile_type"): "RESIDENT / MERCHANT",
    ("user_profile", "confidence"): "0–100",
    ("profile_tag", "dimension_code"): "FRESH / MEDICAL / EDU / TRAFFIC / NIGHT",
    ("profile_dimension_weight", "weight"): "0–100（%）",
    ("district", "district_level"): "STREET / COMMUNITY / GRID",
    ("population_grid", "population"): "≥ 0，人",
    ("population_grid", "density"): "≥ 0，人/km²",
    ("population_grid", "data_date"): "统计日期",
    ("road_segment", "length_m"): "> 0，米",
    ("road_segment", "walk_time_s"): "> 0，秒",
    ("facility_category", "category_code"): "如 FRESH_MARKET / CLINIC",
    ("poi_facility", "lng"): "−180～180",
    ("poi_facility", "lat"): "−90～90",
    ("poi_facility", "business_status"): "OPEN / CLOSED / MOVED / UNKNOWN",
    ("resident_assessment", "radius_m"): "100–3000，米",
    ("resident_assessment", "total_score"): "0–100",
    ("assessment_dimension", "dimension_score"): "0–100",
    ("assessment_dimension", "weight"): "0–100（%）",
    ("assessment_facility_stat", "status"): "充足 / 基本满足 / 待改善",
    ("district_score_snapshot", "coverage_pct"): "0–100（%）",
    ("district_score_snapshot", "avg_score"): "0–100",
    ("district_score_snapshot", "rank_no"): "≥ 1",
    ("site_candidate", "demand_level"): "高 / 中高 / 中 / 低",
    ("site_candidate", "competition_level"): "低 / 中 / 高",
    ("site_candidate", "rent_min"): "≥ 0，万元/年",
    ("site_candidate", "rent_max"): "≥ 0，万元/年，且 ≥ rent_min",
    ("site_candidate", "site_score"): "0–100",
    ("site_score_item", "item_score"): "0–100",
    ("merchant_intent", "contact"): "AES-256-GCM 密文 Base64",
    ("merchant_match", "fit_score"): "0–100",
    ("community_gap", "gap_level"): "高 / 中 / 低",
    ("community_gap", "priority_no"): "≥ 1，1 为最高",
    ("simulation_record", "before_coverage"): "0–100（%）",
    ("simulation_record", "after_coverage"): "0–100（%）",
    ("sync_batch", "sync_type"): "FULL / INCREMENT",
    ("sync_batch", "status"): "RUNNING / SUCCESS / FAILED / PARTIAL",
    ("sync_batch", "insert_count"): "≥ 0",
    ("sync_batch", "update_count"): "≥ 0",
    ("sync_batch", "close_count"): "≥ 0",
    ("poi_change_log", "change_type"): "INSERT / UPDATE / CLOSE / INVALID",
    ("data_quality_issue", "severity"): "HIGH / MEDIUM / LOW",
    ("ods_poi_raw", "process_status"): "PENDING / PROCESSED / REJECTED",
}


def ch2():
    H1("2 数据项")
    H2("2.1 数据项识别方法")
    P("数据项是数据库中不可再分的最小业务属性，也是接口字段、页面展示和数据字典的共同基础。本章采用“业务流程—业务对象—属性—数据项”的四步识别方法：先梳理三类角色的五条主流程，再抽取流程中产生或使用的业务对象，然后列出对象属性，最后对属性去重、统一命名并确定类型与值域。")
    P("识别过程中同时对照三个来源：一是现有接口和前端 mockData 中的字段，保证已有功能可平滑迁移；二是评分、选址、匹配等算法的输入输出，保证模型可解释；三是社区治理与数据同步台账，保证过程可追溯。对于同一业务含义的字段，只保留一个标准名称，例如片区统一用 district、设施统一用 poi_facility，不再出现“小区/社区/网格”混用。")
    P("数据项编号采用“DI-主题域-三位序号”的规则，主题域编码为 USR（用户与画像）、SIT（空间与设施）、RES（居民评估）、MER（商户招商）、COM（社区治理）、OPS（数据运营）。编号在主题域内唯一，字段改名时编号保持不变，便于数据字典和接口文档引用。")

    H2("2.2 数据项分类与编码")
    P("按数据来源和稳定性，数据项分为五类：主数据（片区、设施类别、用户、画像标签）、业务数据（评估、选址、意向、匹配、模拟）、明细数据（维度得分、评分项、设施盘点）、过程数据（同步批次、变更日志、质量问题）和原始数据（ODS 报文）。分类决定了表的存储位置、更新频率和保留策略。")
    rows = []
    for dk, dn in DOMAINS.items():
        ts = DOMAIN_TABLES[dk]
        rows.append([dk, dn, len(ts), "、".join(t["name"] for t in ts[:4]) + ("…" if len(ts) > 4 else ""),
                     f"DI-{dk}-001 起"])
    add_table(["域编码", "主题域", "表数", "主要数据表", "数据项编号"],
              rows, [1.4, 3.2, 1.2, 7.2, 2.6], font_size=9, align_center={0, 2, 4})
    caption("表 2-1 主题域与数据项分布", "table")

    H2("2.3 核心数据项清单")
    P(f"下表列出各主题域最核心的 {len(DATA_ITEMS)} 个数据项，覆盖业务主键、关键度量、状态枚举和算法输入输出。完整 {N_COLS} 项清单见随文档交付的《数据字典与数据项清单.xlsx》“01 数据项清单”工作表，字段级类型、默认值、约束和说明见“03 字段字典”。")
    rows = []
    for tbl, colname in DATA_ITEMS:
        t = BY[tbl]
        c = next(x for x in t["cols"] if x["name"] == colname)
        vd = VALUE_DOMAIN.get((tbl, colname))
        if not vd:
            vd = c["check"] or c["note"] or c["cn"]
        rows.append([DI_ID[(tbl, colname)], c["cn"], f"{tbl}.{colname}", c["typ"], vd,
                     c["note"] or c["cn"]])
    add_table(["编号", "数据项", "英文标识", "类型", "值域/单位", "说明"],
              rows, [1.7, 2.0, 4.4, 1.9, 2.3, 2.3],
              font_size=7.4, header_size=8.2, keep_together=False,
              first_col_center=True)
    caption("表 2-2 核心数据项清单", "table")

    H2("2.4 数据项值域与码表")
    P("系统同时使用两套枚举：面向前端展示的中文枚举（如“充足/基本满足/待改善”“高/中/低”）和面向内部流转的英文状态码（如 SUBMITTED/MATCHED/CLOSED）。中文枚举必须与前端 constants 逐字一致，英文状态码只用于数据库和接口内部，不在页面直接展示。所有枚举均在数据库层通过 CHECK 约束或字典表约束，避免脏值进入。")
    enum_groups = [
        ("角色与账号", "RESIDENT / MERCHANT / COMMUNITY / ADMIN；ACTIVE / DISABLED / DELETED", "app_user.role_code、status"),
        ("画像", "RESIDENT / MERCHANT；FORM / CHAT / IMPORT", "user_profile.profile_type、source"),
        ("空间", "STREET / COMMUNITY / GRID；GRID_100M / GRID_250M / GRID_500M", "district.district_level、population_grid.grid_level"),
        ("道路", "MAIN / BRANCH / ALLEY；Y / N", "road_segment.road_level、is_walkable"),
        ("POI", "OPEN / CLOSED / MOVED / UNKNOWN；AMAP / GOV / MANUAL", "poi_facility.business_status、source"),
        ("设施状态", "充足 / 基本满足 / 待改善", "assessment_facility_stat.status"),
        ("需求与竞争", "高 / 中高 / 中 / 低；低 / 中 / 高", "site_candidate.demand_level、competition_level"),
        ("缺口等级", "高 / 中 / 低", "community_gap.gap_level"),
        ("意向与匹配", "SUBMITTED / MATCHED / CONTACTED / CLOSED / INVALID；PENDING / ACCEPTED / REJECTED", "merchant_intent.status、merchant_match.status"),
        ("同步与质量", "FULL / INCREMENT；RUNNING / SUCCESS / FAILED / PARTIAL；HIGH / MEDIUM / LOW", "sync_batch、data_quality_issue"),
        ("变更类型", "INSERT / UPDATE / CLOSE / INVALID", "poi_change_log.change_type"),
        ("处理状态", "PENDING / PROCESSED / REJECTED", "ods_*_raw.process_status"),
    ]
    add_table(["枚举组", "取值", "典型字段"],
              [list(x) for x in enum_groups],
              [2.2, 8.0, 4.4], font_size=8.4, keep_together=True)
    caption("表 2-3 主要枚举与码表", "table")
    P("完整码表（含每个取值的中文含义和使用字段）见 Excel“04 码表与枚举”工作表。新增枚举值时，必须同步修改前端常量、后端校验、数据库 CHECK 约束和本文档，四处一次提交。")

    H2("2.5 数据项质量规则")
    P("数据质量规则分为唯一性、完整性、值域、格式、时效、一致性、空间合理性和引用完整性八类，在 ODS 入仓和 DWD 合并两个环节执行。校验发现的问题写入 data_quality_issue，严重问题阻断批次，一般问题允许带病入库并标记。")
    add_table(
        ["类别", "规则", "校验对象", "处理方式"],
        [
            ["唯一性", "同一来源的 source_poi_id 不得重复", "ods_poi_raw、poi_facility", "保留最新一条，旧记录写变更日志"],
            ["完整性", "名称、坐标、类别、来源编号不能为空", "poi_facility", "拦截并记录 HIGH 级问题"],
            ["值域", "评分 0–100、权重 0–100、覆盖率 0–100", "评估、选址、快照", "越界值置空并告警"],
            ["格式", "经纬度为十进制度，保留 6 位小数", "POI、片区、路网", "格式错误剔除"],
            ["时效", "POI 最近发现时间不超过 15 天", "poi_facility", "标记 stale，触发补采"],
            ["一致性", "评估得分与维度加权结果偏差不超过 1 分", "resident_assessment", "重算并修正"],
            ["空间", "坐标落在城市行政边界内，且不在水域", "poi_facility", "标记坐标异常"],
            ["引用", "外键必须指向存在的主数据", "全部业务表", "阻断写入并回滚事务"],
        ],
        [1.7, 5.0, 4.2, 3.7], font_size=8.6,
    )
    caption("表 2-4 数据项质量规则", "table")
    P("质量规则编码统一使用大写下划线，例如 DUP_POI（重复 POI）、COORD_OUT_OF_RANGE（坐标越界）、CATEGORY_MISSING（类别缺失）、SOURCE_ID_MISSING（来源编号缺失）、STATUS_CONFLICT（状态冲突）、STALE_DATA（数据过期）。规则编码写入 data_quality_issue.rule_code，便于统计和追责。")


# --------------------------------------------------------------------------
# chapter 3
# --------------------------------------------------------------------------
def ch3():
    H1("3 数据模型")
    H2("3.1 建模方法与 dbdiagram.io")
    P("建模遵循“概念模型—逻辑模型—物理模型”三层递进。概念模型只关心业务对象及其关系，用主题域总览图表达；逻辑模型细化到实体、属性、主键、外键和基数，用 dbdiagram.io 的 DBML 表达；物理模型再补充 Oracle 数据类型、表空间、分区、索引和约束，由脚本生成。")
    P("选择 dbdiagram.io 的原因有三点：一是 DBML 是纯文本，能纳入 Git 版本管理，字段变更可 diff、可评审；二是关系线由 Ref 自动生成，修改字段后图形同步更新，适合课程项目多人协作；三是支持 TableGroup、Note、Indexes 等语义，能直接导出 PNG/PDF 用于文档。")
    add_image(os.path.join(FIG_DIR, "11_dbdiagram建模流程.png"), 13.6, 17.0)
    fig_caption("从业务调研到建表验证的建模流程", "figure")
    P("建模约定如下：表名使用小写单数名词加下划线；主键统一为 id；外键为“被引用表名_id”；时间字段以 _at 结尾；评分字段以 _score 结尾；布尔语义用 CHAR(1) 的 Y/N，不使用数据库方言的 BOOLEAN，保证 Oracle、MySQL、H2 三套脚本一致。")
    code_block("""Table app_user {
  id bigint [pk, increment]
  user_code varchar(64) [not null, unique]
  role_code varchar(20) [not null, default: 'RESIDENT']
  ...
}
Ref: user_profile.user_id > app_user.id
TableGroup "用户与画像" { app_user user_profile ... }""")
    P("上图为最小 DBML 片段。完整文件 class_test_full.dbml 共约 2.1 万字符，包含 27 张表、258 个字段、41 条 Ref 和 6 个 TableGroup，可直接粘贴到 https://dbdiagram.io/d 复现。")

    H2("3.2 概念模型：主题域总体关系")
    P("系统数据按六个主题域组织。USR 负责账号、画像标签与维度权重；SIT 负责片区、人口栅格、路网、设施类别和 POI；RES 负责居民评估、维度得分、设施盘点和片区评分快照；MER 负责选址候选点、评分明细、开店意向和招商匹配；COM 负责社区短板与网点模拟；OPS 负责同步批次、变更日志、质量问题和 ODS 原始数据。")
    P("六个域不是孤立的：片区 district 是全局空间主键，被设施、评估、候选点、短板和模拟共同引用；用户画像通过 profile_dimension_weight 为居民评估提供个性化权重；POI 与人口栅格同时为居民评估和商户选址提供输入；每次同步批次又为评估、候选点和快照提供数据版本。总体关系如图 3-1 所示。")
    add_image(os.path.join(FIG_DIR, "01_总体ER图.png"), 14.4, 19.0)
    fig_caption("主题域总体关系（实体明细见 3.3 节分域图）", "figure")

    H2("3.3 逻辑模型：分域实体关系")
    P("为避免单张图过大导致字段不可读，按主题域拆成六张逻辑模型图。每张图突出主键、外键和关键业务字段；完整字段见第 6 章和 Excel 字段字典。图中灰色实体为外部引用表，仅显示主键，表示跨域外键。")
    domains_figs = [
        ("USR", "3.3.1 用户与画像域", "02_用户与画像域.png",
         "用户与画像域由 app_user、user_profile、profile_tag、user_profile_tag 和 profile_dimension_weight 五张表组成。一个用户可以有多版画像，但只有一条 is_current='Y' 的当前画像；画像通过标签明细关联标签字典，通过维度权重表固化五维权重，保证历史评估可复算。"),
        ("SIT", "3.3.2 空间与设施域", "03_空间与设施域.png",
         "空间与设施域由 district、population_grid、road_node、road_segment、facility_category 和 poi_facility 六张表组成。district 自关联形成街道—社区—网格三级结构；road_node 与 road_segment 构成步行图；facility_category 把 POI 类别映射到五个评分维度；poi_facility 以 source+source_poi_id 唯一，支撑增量去重。"),
        ("RES", "3.3.3 居民生活圈评估域", "04_居民评估域.png",
         "居民评估域由 resident_assessment、assessment_dimension、assessment_facility_stat 和 district_score_snapshot 四张表组成。主表保存一次评估的汇总结果，两张明细表分别保存五维得分/权重和设施类别盘点，快照表保存每次同步后片区维度的评分与排名，供社区看板直接查询。"),
        ("MER", "3.3.4 商户选址与招商域", "05_商户招商域.png",
         "商户招商域由 site_candidate、site_score_item、merchant_intent 和 merchant_match 四张表组成。候选点保存人口指数、竞争数、租金和总分；评分明细按评分项拆开，保证推荐理由可解释；开店意向在原有 5 个字段基础上扩展片区、候选点、预算和状态；匹配表把意向与社区短板关联起来。"),
        ("COM", "3.3.5 社区治理域", "06_社区治理域.png",
         "社区治理域由 community_gap 和 simulation_record 两张表组成。短板表记录问题类别、缺口等级、未覆盖人口和改造优先级；模拟表记录新增网点前后的覆盖率、受益人口和操作人，用于比较不同改造方案。"),
        ("OPS", "3.3.6 数据运营与同步域", "07_数据运营与同步域.png",
         "数据运营域由 sync_batch、poi_change_log、data_quality_issue 和三张 ODS 原始表组成。批次表是一次同步的台账；变更日志记录 POI 的增、改、关停和清洗无效；质量问题表记录校验发现的问题；ODS 表原样保存接口报文，按月分区，支撑重放与审计。"),
    ]
    for dk, title, fig, desc in domains_figs:
        H3(title)
        P(desc)
        add_image(os.path.join(FIG_DIR, fig), 14.2, 18.6)
        fig_caption(f"{M.DOMAINS[dk]}逻辑模型", "figure")

    H2("3.4 实体关系与基数说明")
    P(f"模型共有 {N_FKS} 个外键，全部在图 3-1 至图 3-7 中以 Ref 或关系线表示。下表给出每个外键的主表、引用表、基数和删除策略。除特别说明外，均为“多对一”：主表可以有 0 到多行指向引用表的一行；删除策略中 CASCADE 表示随父表删除，SET NULL 表示父表删除后置空，NO ACTION 表示有子记录时禁止删除。")
    rows = []
    i = 0
    for t in TABLES:
        for c in t["cols"]:
            if c["fk"]:
                i += 1
                ref_t, ref_c = c["fk"].split(".")
                rows.append([i, f"{t['name']}.{c['name']}", f"{ref_t}.{ref_c}", "N:1",
                             c["on_delete"] or "NO ACTION", c["cn"]])
    add_table(["序号", "外键（主表.字段）", "引用（表.字段）", "基数", "删除策略", "说明"],
              rows, [0.8, 4.5, 4.3, 1.0, 1.9, 2.1],
              font_size=7.8, header_size=8.2, keep_together=False,
              align_center={0, 3, 4})
    caption("表 3-1 外键关系与基数", "table")

    H2("3.5 范式与反范式设计")
    P("主数据与业务表整体满足第三范式：片区、设施类别、标签、用户等重复出现的数据拆为独立表，业务表只保存外键；评估维度、评分项、设施盘点等多值属性拆为明细表，避免一行内出现重复列组。这样能消除插入、更新和删除异常，也便于按维度聚合。")
    P("模型中有少量有意的反范式设计，均以“读多写少、可接受最终一致”为前提：")
    bullet_list([
        "resident_assessment.profile_label 冗余画像标签，避免评估列表每次关联画像表；写入时从画像复制，画像更新不回改历史评估。",
        "district_score_snapshot.resident_count 冗余覆盖人口，快照一旦生成即冻结，保证历史排名可复现。",
        "merchant_intent.contact_masked 冗余脱敏号码，列表页无需解密即可展示，减少敏感数据访问。",
        "site_score_item 把评分项拆成行而不是 JSON，兼顾可解释与可查询；仅 district.boundary_geojson 使用 CLOB 保存几何，因为边界只整体读写、不做关系查询。",
        "district_score_snapshot 是典型的 ADS 快照，允许与明细存在分钟级延迟，由同步批次号保证版本一致。",
    ])

    H2("3.6 DBML 模型文件说明")
    P("建模源文件位于 dbml 目录，主文件为 class_test_full.dbml，另按六个主题域提供子文件，便于单独评审。DBML 使用 Table、Ref、TableGroup、Note、Indexes 五类语法；字段注释使用 note，表说明使用 Note，索引写在 indexes 块中。")
    add_table(
        ["文件", "内容", "用途"],
        [
            ["class_test_full.dbml", "全部 27 表、41 条 Ref、6 个 TableGroup", "导入 dbdiagram.io 生成完整 ER 图"],
            ["class_test_usr.dbml", "用户与画像域 5 表", "分域评审、局部修改"],
            ["class_test_sit.dbml", "空间与设施域 6 表", "分域评审"],
            ["class_test_res.dbml", "居民评估域 4 表", "分域评审"],
            ["class_test_mer.dbml", "商户招商域 4 表", "分域评审"],
            ["class_test_com.dbml", "社区治理域 2 表", "分域评审"],
            ["class_test_ops.dbml", "数据运营域 6 表", "分域评审"],
        ],
        [4.2, 6.4, 4.0], font_size=9,
    )
    caption("表 3-2 DBML 模型文件清单", "table")
    P("复现步骤：打开 https://dbdiagram.io/d，清空左侧示例，粘贴 class_test_full.dbml 全文；右侧自动生成图形，可在 Export 中导出 PNG/PDF。修改字段时先改 DBML，再执行 gen_artifacts.py 重新生成 SQL、Excel 和本文档，确保模型只有一个事实来源。")


# --------------------------------------------------------------------------
# chapter 4
# --------------------------------------------------------------------------
def ch4():
    H1("4 数据规划架构")
    H2("4.1 总体架构")
    P("数据架构按“数据源—接入治理—ODS—DWD—ADS—服务应用”六层组织。外部 POI、人口和路网数据先原样落到 ODS，再经质量校验和标准化进入 DWD；评分、排名等派生结果写入 ADS 快照并刷新缓存；API 与 Agent 只访问 DWD/ADS，不直接读 ODS。这样既保证原始数据可追溯，又避免业务查询被大报文拖慢。")
    add_image(os.path.join(FIG_DIR, "08_数据规划架构.png"), 13.6, 19.0)
    fig_caption("数据规划总体架构", "figure")
    P("架构的关键取舍：一是 ODS 与 DWD 分表空间，原始报文可压缩、可归档，不占用业务表的高性能存储；二是评估与选址结果落表而不是只放缓存，保证结论可复现、可审计；三是缓存只承载热点查询，数据库仍是唯一事实来源，缓存失效由批次号驱动。")

    H2("4.2 分层设计")
    add_table(
        ["层次", "定位", "主要表", "更新频率", "保留策略"],
        [
            ["ODS 原始层", "原样落地外部报文，支持重放与审计", "ods_poi_raw、ods_population_raw、ods_road_raw", "每半月", "在线 6 个月，归档 12 个月"],
            ["DWD 明细层", "清洗、去重、标准化后的业务实体", "27 表中的 24 张业务/明细/字典表", "实时 + 每半月", "业务数据 3 年"],
            ["ADS 应用层", "评分快照、看板视图、缓存", "district_score_snapshot、v_district_dashboard、缓存", "每次同步后", "快照 3 年"],
            ["治理层", "批次、变更、质量、权限、元数据", "sync_batch、poi_change_log、data_quality_issue", "随批次", "3 年"],
        ],
        [2.2, 4.4, 4.6, 1.7, 1.7], font_size=8.6,
    )
    caption("表 4-1 数据分层设计", "table")

    H2("4.3 主题域与数据分布")
    P("按业务对象把 27 张表划分到六个主题域，每个域有明确的所有者和生命周期。片区、设施类别等主数据由社区管理员维护；POI、人口、路网由同步任务维护；画像由用户行为生成；评估、选址、匹配、模拟等业务结果由对应角色触发写入。")
    rows = []
    kinds = Counter(t["kind"] for t in TABLES)
    for dk, dn in DOMAINS.items():
        ts = DOMAIN_TABLES[dk]
        rows.append([dk, dn, len(ts), sum(len(t["cols"]) for t in ts),
                     f"{sum(t['rows_3y'] for t in ts):,}", "、".join(t["name"] for t in ts[:3]) + ("…" if len(ts) > 3 else "")])
    add_table(["域", "主题域", "表数", "字段数", "3 年行数", "代表表"],
              rows, [1.0, 3.2, 1.0, 1.3, 2.1, 6.0], font_size=8.6,
              align_center={0, 2, 3, 4})
    caption("表 4-2 主题域数据分布", "table")

    H2("4.4 数据流转与更新机制")
    P("外部数据每半月同步一次，定在每月 1 日和 16 日凌晨 02:00 触发，避开业务高峰。同步任务按“建批次—拉取—落 ODS—质量校验—合并 DWD—重算 ADS—刷新缓存—关批次”的顺序执行，任一步失败都把批次置为 FAILED 或 PARTIAL，并保留已落地的原始数据供重放。")
    add_image(os.path.join(FIG_DIR, "09_半月数据流转.png"), 14.2, 15.0)
    fig_caption("半月数据同步与业务写入流程", "figure")
    P("增量策略以 source+source_poi_id 为业务唯一键：新键插入，已有键比较名称、坐标、类别、营业状态，有变化则更新并写 poi_change_log；本次未出现且超过两个周期的记录标记 CLOSED；坐标越界、类别缺失等异常写 data_quality_issue。全过程以 batch_id 串联，评估和候选点记录使用的批次号，保证结论可追溯到具体数据版本。")
    P("业务写入与同步任务解耦：居民评估、商户意向、社区模拟走在线事务，直接写 DWD；同步任务只更新主数据和派生快照，不修改用户业务记录。写后立即读的场景（如提交意向后的列表）走主库，普通查询走只读库，沿用现有读写分离配置。")

    H2("4.5 数据治理")
    bullet_list([
        "标准管理：表、字段、枚举、命名规范以本文件和 DATA_CONVENTIONS.md 为准，变更走“文档—脚本—代码”三步。",
        "质量管理：八类规则在 ODS 和 DWD 两个环节执行，问题落表、分级、闭环处理，批次结束输出质量报告。",
        "元数据管理：每张表有中文名、业务说明、主题域、更新频率和责任人；字段有中文名、类型、值域和说明。",
        "血缘管理：ODS 表→DWD 表→ADS 快照→视图的依赖在 data-model.json 和本文档第 4.4 节中明确。",
        "版本管理：DBML、SQL、Excel、文档同仓管理；每次结构变更生成迁移脚本，不使用手工改库。",
    ])

    H2("4.6 数据安全与隐私")
    P("按最小权限原则划分数据库账号：life_circle_app 负责业务读写，life_circle_readonly 负责只读查询，life_circle_etl 负责 ODS/DWD 同步，DBA 负责表空间与备份。业务账号不授予 DROP ANY TABLE、ALTER SYSTEM 等系统权限；只读账号只授予 SELECT 和必要的视图权限。")
    add_table(
        ["数据类别", "示例", "保护措施"],
        [
            ["个人身份信息", "手机号", "只存加盐 SHA-256 哈希，不可逆；不存身份证号、精确住址"],
            ["联系方式", "merchant_intent.contact", "AES-256-GCM 加密后 Base64 存储；列表只展示 contact_masked"],
            ["空间数据", "片区边界、POI 坐标", "按角色授权；对外接口只返回聚合结果，不返回全量原始坐标"],
            ["业务台账", "意向、匹配、模拟", "按 district_id 做行级权限；社区账号只能看本辖区"],
            ["原始报文", "ods_*_raw", "仅 ETL 和 DBA 可读；保留 6 个月后归档"],
        ],
        [2.6, 4.4, 7.6], font_size=8.8,
    )
    caption("表 4-3 数据分类与保护措施", "table")
    P("传输层启用 TLS；备份文件加密；审计开启对 merchant_intent、app_user、data_quality_issue 的 SELECT/UPDATE 审计。涉及敏感字段的查询必须带明确业务目的，禁止在日志中打印明文联系方式。")

    H2("4.7 数据生命周期")
    add_table(
        ["数据类别", "在线保留", "归档保留", "到期处理"],
        [
            ["ODS 原始报文", "6 个月", "12 个月", "导出压缩文件后删除分区"],
            ["POI 变更日志", "12 个月", "3 年", "按年归档，保留变更摘要"],
            ["居民评估与明细", "2 年", "3 年", "按评估时间分区归档，匿名化后保留统计值"],
            ["选址候选点与评分项", "2 年", "3 年", "按批次归档，删除失效候选点"],
            ["商户意向与匹配", "关闭后 1 年", "3 年", "联系人信息脱敏后保留业务台账"],
            ["片区评分快照", "3 年", "5 年", "按年归档，保留年度趋势"],
            ["同步批次与质量问题", "3 年", "5 年", "归档后仅保留统计结果"],
        ],
        [3.6, 2.4, 2.4, 6.0], font_size=8.8,
    )
    caption("表 4-4 数据生命周期与保留策略", "table")


# --------------------------------------------------------------------------
# chapter 5
# --------------------------------------------------------------------------
def ch5():
    H1("5 数据库环境与规范")
    H2("5.1 运行环境")
    add_table(
        ["环境", "数据库", "部署方式", "访问方式", "用途"],
        [
            ["开发", "H2 2.2.224", "Spring Boot 进程内，MODE=Oracle", "jdbc:h2:mem:lifecircle", "单元测试、联调、快速建表"],
            ["生产", "Oracle 23ai Free", "Docker 或独立主从服务器，FREEPDB1", "HikariCP + JPA", "正式数据存储，主库写、只读库查"],
            ["可选", "MySQL 8.0", "本地或容器", "JDBC", "教学演示、跨方言验证"],
        ],
        [1.4, 3.2, 5.2, 3.0, 2.8], font_size=8.8,
    )
    caption("表 5-1 数据库运行环境", "table")
    P("H2 通过 MODE=Oracle 保持与生产库一致的语法和类型行为，但 H2 不支持表空间、分区和 SecureFiles，因此开发脚本只保留表、约束和索引；Oracle 专属的存储属性在 02_schema_oracle.sql 中实现。生产库字符集建议 AL32UTF8，开发库使用 Unicode。")

    H2("5.2 命名规范")
    add_table(
        ["对象", "规则", "示例"],
        [
            ["表名", "小写单数名词 + 下划线，不用拼音、不用表前缀", "poi_facility、merchant_intent"],
            ["字段名", "小写 + 下划线；布尔语义用 is_ 前缀", "source_poi_id、is_current"],
            ["主键", "统一为 id", "id"],
            ["外键", "被引用表名 + _id", "district_id、assessment_id"],
            ["时间字段", "以 _at 结尾", "created_at、assessed_at"],
            ["评分字段", "以 _score 结尾", "total_score、site_score"],
            ["普通索引", "idx_表名_字段名", "idx_poi_district_cat"],
            ["唯一约束", "uk_表名_字段名", "uk_user_profile_ver"],
            ["外键约束", "fk_表名_字段名", "fk_poi_district_id"],
            ["检查约束", "ck_表名_字段名", "ck_site_candidate_site_score"],
            ["视图", "v_业务含义", "v_district_dashboard"],
        ],
        [2.2, 7.4, 5.0], font_size=8.8,
    )
    caption("表 5-2 数据库对象命名规范", "table")

    H2("5.3 数据类型映射")
    add_table(
        ["逻辑类型", "Oracle", "MySQL", "H2", "Java"],
        [
            ["BIGINT", "NUMBER(19)", "BIGINT", "BIGINT", "Long"],
            ["INT", "NUMBER(10)", "INT", "INT", "Integer"],
            ["VARCHAR(n)", "VARCHAR2(n)", "VARCHAR(n)", "VARCHAR(n)", "String"],
            ["CHAR(1)", "CHAR(1)", "CHAR(1)", "CHAR(1)", "String"],
            ["DECIMAL(p,s)", "NUMBER(p,s)", "DECIMAL(p,s)", "DECIMAL(p,s)", "BigDecimal"],
            ["DATE", "DATE", "DATE", "DATE", "LocalDate"],
            ["TIMESTAMP", "TIMESTAMP(6)", "DATETIME(6)", "TIMESTAMP(6)", "Instant / LocalDateTime"],
            ["CLOB", "CLOB", "LONGTEXT", "CLOB", "String"],
        ],
        [2.4, 3.4, 3.2, 3.2, 3.0], font_size=8.8,
    )
    caption("表 5-3 逻辑类型与各方言映射", "table")
    P("金额类字段统一用 DECIMAL，不使用 FLOAT/DOUBLE，避免浮点误差；坐标用 DECIMAL(10,6)，保留约 0.1 米精度；评分和权重用整数或 DECIMAL(5,2)，不用字符串拼接。")

    H2("5.4 主键、外键与审计字段")
    bullet_list([
        "主键统一使用 BIGINT 自增（Oracle IDENTITY、MySQL AUTO_INCREMENT、H2 IDENTITY），避免业务编号变更影响关联。",
        "业务唯一键单独建唯一约束，例如 user_code、district_code、batch_no、source+source_poi_id，不把业务编号当主键。",
        "外键默认 NO ACTION，删除父表前必须先处理子表；画像标签、评估明细、评分项等从属数据使用 CASCADE；引用主数据的历史记录使用 SET NULL，保留台账。",
        "审计字段：created_at、updated_at 由数据库默认值和应用共同维护；不在每张表重复 created_by，操作人记录在业务表（如 simulation_record.operator）或审计日志中。",
        "软删除只在 app_user、poi_facility 等需要保留历史的表使用 is_valid/status；业务表不做物理删除，改为状态关闭。",
    ])


# --------------------------------------------------------------------------
# chapter 6
# --------------------------------------------------------------------------
DOMAIN_INTROS = {
    "USR": "用户与画像域承载三类角色的账号、画像版本、标签和维度权重。设计重点是把“当前画像”和“历史画像”分开、把标签字典和用户标签分开，使个性化评分可复算。",
    "SIT": "空间与设施域是整个系统的空间底座：片区提供统计口径，人口栅格提供需求强度，路网提供步行可达计算，设施类别把 POI 映射到评分维度，POI 表保存设施事实。",
    "RES": "居民评估域保存“一次评估”的主记录、五维明细和设施盘点，并用片区快照支撑社区看板。评估记录带数据批次号，保证不同时间的结论可追溯。",
    "MER": "商户招商域把“候选点—评分项—意向—匹配”串成闭环：候选点由算法生成，评分项解释得分，意向由商户提交，匹配由社区完成。",
    "COM": "社区治理域记录辖区短板和网点增设模拟。短板是招商匹配的输入，模拟是改造决策的依据，两者都以片区和设施类别为维度。",
    "OPS": "数据运营域保存同步批次、POI 变更、质量问题和 ODS 原始报文，是数据可追溯、可重放、可审计的基础。",
}


def detail_table(t):
    TBL_NO[CUR_CH] += 1
    no = TBL_NO[CUR_CH]
    rows = []
    for c in t["cols"]:
        keys = []
        if c["pk"]:
            keys.append("PK")
        if c["fk"]:
            keys.append("FK")
        if c["uniq"]:
            keys.append("UK")
        desc = c["note"] or c["cn"]
        if c["fk"]:
            desc = "外键→" + c["fk"].split(".")[0] + "；" + desc
        if c["default"]:
            desc += f"；默认 {c['default']}"
        rows.append([c["name"], c["cn"], c["typ"], "否" if (not c["null"] or c["pk"]) else "是",
                     "、".join(keys) or "", desc])
    add_table(["字段", "中文名", "类型", "空", "键", "说明"],
              rows, [3.35, 2.75, 2.7, 0.65, 1.15, 3.9],
              font_size=8.0, header_size=8.4, keep_together=False,
              align_center={3})
    caption(f"表 {CUR_CH}-{no} {t['name']} {t['cn']}", "table")
    return no


def ch6():
    H1("6 数据表设计")
    H2("6.1 数据表清单")
    P(f"模型共 {N_TABLES} 张表，按主题域分布为：用户与画像 5 张、空间与设施 6 张、居民评估 4 张、商户招商 4 张、社区治理 2 张、数据运营 6 张。表类型包括主数据 4 张、字典 2 张、业务 10 张、明细 5 张、快照 1 张、日志 2 张、ODS 3 张。")
    rows = []
    for i, t in enumerate(TABLES, 1):
        tm, lm, im = storage(t)
        rows.append([i, t["name"], t["cn"], t["domain"], t["kind"], f"{t['rows_3y']:,}",
                     f"{tm + lm + im:.1f}", "是" if t["partition"] else "否"])
    add_table(["#", "表名", "中文名", "域", "类型", "3 年行数", "容量(MB)", "分区"],
              rows, [0.65, 3.45, 2.85, 1.15, 1.15, 1.55, 1.45, 1.75],
              font_size=7.8, header_size=8.2, keep_together=False,
              align_center={0, 3, 4, 5, 6, 7})
    caption("表 6-1 数据表清单", "table")
    P("容量为在线数据估算，不含索引、LOB、备份与临时空间；分区列为“是”表示按时间做 RANGE 分区，详见 7.3 节。")

    for dk, title in [("USR", "6.2 用户与画像域"), ("SIT", "6.3 空间与设施域"),
                      ("RES", "6.4 居民生活圈评估域"), ("MER", "6.5 商户选址与招商域"),
                      ("COM", "6.6 社区治理域"), ("OPS", "6.7 数据运营与同步域")]:
        H2(title)
        P(DOMAIN_INTROS[dk])
        for t in DOMAIN_TABLES[dk]:
            P(f"{t['name']}（{t['cn']}）：{t['note']}预计 3 年 {t['rows_3y']:,} 行。", indent=False,
              size=10.5, color="404040")
            detail_table(t)

    H2("6.8 索引与约束汇总")
    P(f"模型共创建 {N_INDEX} 组索引/唯一约束，其中单列唯一约束 {N_UNIQ - sum(1 for t in TABLES for _n, _c, u in t['indexes'] if u)} 个、复合唯一约束 {sum(1 for t in TABLES for _n, _c, u in t['indexes'] if u)} 个；另有 {N_CHECKS} 个检查约束和 {N_FKS} 个外键约束。主键、唯一约束和检查约束在 Oracle 建表时内联创建，普通索引在表创建后单独创建并指定索引表空间。")
    add_table(
        ["对象类型", "数量", "说明"],
        [
            ["表", N_TABLES, "含 3 张 ODS 表"],
            ["字段", N_COLS, "平均每表约 9.6 个字段"],
            ["主键", N_TABLES, "全部为 BIGINT 自增"],
            ["外键", N_FKS, "覆盖 27 张表，删除策略见 3.4 节"],
            ["唯一约束", N_UNIQ, "业务唯一键 + 复合唯一键"],
            ["检查约束", N_CHECKS, "枚举、范围、金额上下限"],
            ["普通索引", N_INDEX - sum(1 for t in TABLES for _n, _c, u in t["indexes"] if u), "按查询模式设计"],
            ["分区表", sum(1 for t in TABLES if t["partition"]), "POI 变更、评估、ODS 三表"],
        ],
        [3.0, 2.0, 9.6], font_size=9, align_center={1},
    )
    caption("表 6-2 索引与约束统计", "table")
    P("索引设计遵循“高频等值/范围查询建复合索引、低选择性列不单建、写多表控制索引数量”的原则。例如 poi_facility 建 (district_id, category_id) 支撑片区设施盘点，建 (source, source_poi_id) 唯一约束支撑增量去重；resident_assessment 建 (district_id, assessed_at) 支撑片区时间趋势；site_candidate 建 (district_id, business_type, site_score) 支撑按业态排序推荐。")

    H2("6.9 视图设计")
    P("为简化社区看板和设施统计查询，设计两个视图。视图只读，不承担写入；后续数据量增大时可把 v_district_dashboard 改为物化视图，按批次刷新。")
    code_block("""CREATE OR REPLACE VIEW v_district_dashboard AS
SELECT d.id, d.district_code, d.district_name,
       s.coverage_pct, s.avg_score, s.rank_no, d.resident_count,
       (SELECT COUNT(*) FROM community_gap g
         WHERE g.district_id = d.id AND g.gap_level = '高') AS high_gap_count,
       (SELECT COUNT(*) FROM merchant_intent i
         WHERE i.district_id = d.id AND i.status = 'SUBMITTED') AS pending_intent_count,
       s.scored_at
  FROM district d
  LEFT JOIN district_score_snapshot s ON s.district_id = d.id
   AND s.scored_at = (SELECT MAX(s2.scored_at) FROM district_score_snapshot s2
                       WHERE s2.district_id = d.id)
 WHERE d.status = 'ACTIVE';""", size=7.6)
    P("v_poi_category_stat 按片区和设施类别统计有效 POI 数量，供居民端设施清单和社区端热力图使用。两个视图的完整定义见 sql/06_views_oracle.sql。")


# --------------------------------------------------------------------------
# chapter 7
# --------------------------------------------------------------------------
def ch7():
    H1("7 存储结构规划")
    H2("7.1 存储总体布局")
    P("Oracle 侧按数据用途划分四个表空间：业务数据、索引、LOB 和 ODS。业务数据与索引分离，便于独立调整存储参数、单独重建索引；LOB 单独存放，避免大字段把业务表撑大；ODS 使用独立表空间并开启压缩，便于按分区归档和清理。")
    add_image(os.path.join(FIG_DIR, "10_存储结构布局.png"), 13.4, 18.0)
    fig_caption("Oracle 表空间与存储对象布局", "figure")

    H2("7.2 表空间与数据文件")
    add_table(
        ["表空间", "存放对象", "初始大小", "自动扩展", "上限", "说明"],
        [
            ["TBS_LIFECIRCLE_DATA", "业务表、字典表、快照表", "1 GB", "每次 256 MB", "6 GB", "ASSM 自动段空间管理"],
            ["TBS_LIFECIRCLE_IDX", "主键、唯一约束、普通索引", "512 MB", "每次 128 MB", "3 GB", "与数据分离，便于重建"],
            ["TBS_LIFECIRCLE_LOB", "CLOB、GeoJSON、JSON 快照", "512 MB", "每次 128 MB", "3 GB", "SecureFiles + 压缩"],
            ["TBS_LIFECIRCLE_ODS", "三张 ODS 原始表、变更日志分区", "1 GB", "每次 256 MB", "4 GB", "按月分区，可压缩归档"],
        ],
        [3.4, 4.2, 1.6, 2.0, 1.2, 2.2], font_size=8.4,
        align_center={2, 3, 4},
    )
    caption("表 7-1 表空间规划", "table")
    P("建表脚本通过 TABLESPACE 子句把表、索引、LOB 分别落到对应表空间；表空间由 DBA 预先创建，业务用户不授予 CREATE TABLESPACE 权限。数据文件使用 AUTOEXTEND，但设置 MAXSIZE，防止单个表空间耗尽挂载点。")

    H2("7.3 分区策略")
    P("五张表按时间做 RANGE 分区，并用 INTERVAL 自动按月扩展：poi_change_log 按 changed_at、resident_assessment 按 assessed_at、ods_poi_raw/ods_population_raw/ods_road_raw 按 load_at。分区带来三个好处：查询自然带时间条件时只扫相关分区；历史数据可按分区归档或删除；ODS 分区可单独压缩。")
    add_table(
        ["表", "分区键", "粒度", "保留", "压缩/归档"],
        [
            ["poi_change_log", "changed_at", "按月", "12 个月在线 + 3 年归档", "压缩，按年归档"],
            ["resident_assessment", "assessed_at", "按月", "2 年在线 + 3 年归档", "压缩，匿名化归档"],
            ["ods_poi_raw", "load_at", "按月", "6 个月在线 + 12 个月归档", "压缩高，导出后删除"],
            ["ods_population_raw", "load_at", "按月", "6 个月在线 + 12 个月归档", "压缩高，导出后删除"],
            ["ods_road_raw", "load_at", "按月", "6 个月在线 + 12 个月归档", "压缩高，导出后删除"],
        ],
        [3.4, 2.4, 1.2, 4.0, 3.6], font_size=8.6,
        align_center={2},
    )
    caption("表 7-2 分区策略", "table")
    P("分区表的主键仍为 id，分区键不是主键的一部分；Oracle 允许本地索引和全局索引，模型统一使用本地索引，保证分区维护（DROP/TRUNCATE PARTITION）不影响其他分区。MySQL 方言不启用分区，避免分区表不支持外键的限制。")

    H2("7.4 索引存储策略")
    P("索引统一放在 TBS_LIFECIRCLE_IDX，使用本地索引；主键和唯一约束的索引由 Oracle 自动创建，也指定到索引表空间。普通索引按查询模式设计，避免在低选择性字段上单独建索引；复合索引把等值条件放前、范围/排序条件放后。")
    bullet_list([
        "poi_facility：(district_id, category_id) 支撑片区设施盘点；(source, source_poi_id) 唯一约束支撑同步去重；(category_id, is_valid) 支撑类别统计。",
        "resident_assessment：(district_id, assessed_at) 支撑片区趋势；(user_id, assessed_at) 支撑个人历史；分区表使用本地索引。",
        "site_candidate：(district_id, business_type, site_score) 支撑按业态排序推荐；评分项通过 candidate_id 关联，避免宽表。",
        "merchant_intent：(status, created_at) 支撑待办列表；(district_id) 支撑社区按辖区查询。",
        "索引维护：批量同步后如索引膨胀超过 30%，在维护窗口重建；删除长期未使用索引前先看 AWR/执行计划。",
    ])

    H2("7.5 LOB 与大对象存储")
    P("模型共有 8 个 CLOB 字段：district.boundary_geojson、poi_change_log.before_json/after_json、ods_poi_raw.raw_json、ods_population_raw.raw_json、ods_road_raw.raw_json。Oracle 使用 SecureFiles 存储，开启 COMPRESS HIGH，减少 JSON 文本占用；业务表只整体读写 GeoJSON 和快照，不对 LOB 内容做关系查询，因此不需要把 JSON 拆成关系表。")
    P("如果后续需要按 JSON 内部字段查询（例如按 POI 类别过滤原始报文），可在 Oracle 23ai 中使用 JSON 数据类型和 JSON_TABLE，或把高频字段提升为普通列；当前设计优先保证模型简单和跨方言可移植。")

    H2("7.6 容量估算")
    P(f"按 3 年在线数据估算，表数据约 {TOTAL_DATA:.0f} MB，LOB 约 {TOTAL_LOB:.0f} MB，索引约 {TOTAL_IDX:.0f} MB，合计约 {TOTAL_DATA + TOTAL_LOB + TOTAL_IDX:.0f} MB（约 {(TOTAL_DATA + TOTAL_LOB + TOTAL_IDX) / 1024:.2f} GB）。加上 UNDO、TEMP、归档和备份，建议初始规划 4 GB 业务空间，按 2 倍增长预留。")
    top = sorted(TABLES, key=lambda t: sum(storage(t)), reverse=True)[:9]
    rows = []
    for t in top:
        tm, lm, im = storage(t)
        rows.append([t["name"], f"{t['rows_3y']:,}", f"{tm:.1f}", f"{lm:.1f}", f"{im:.1f}",
                     f"{tm + lm + im:.1f}", "ODS" if t["tablespace"] == "ODS" else "DATA"])
    rows.append(["合计（27 表）", f"{N_ROWS:,}", f"{TOTAL_DATA:.0f}", f"{TOTAL_LOB:.0f}",
                 f"{TOTAL_IDX:.0f}", f"{TOTAL_DATA + TOTAL_LOB + TOTAL_IDX:.0f}", "—"])
    add_table(["表名", "3 年行数", "数据(MB)", "LOB(MB)", "索引(MB)", "合计(MB)", "表空间"],
              rows, [4.0, 1.8, 1.6, 1.5, 1.5, 1.7, 2.0], font_size=8.4,
              align_center={1, 2, 3, 4, 5, 6})
    caption("表 7-3 主要表容量估算", "table")
    P("估算假设：一个街道 12 个社区、约 5 万居民、8000 个有效 POI、1000 个路网节点；居民每人每年评估 2 次；POI 每半月同步一次，每次约 5% 变化；ODS 只保留 12 个月。实际运行时按季度采集段空间统计并修正估算。")

    H2("7.7 备份与恢复")
    add_table(
        ["项目", "策略", "说明"],
        [
            ["全量备份", "每周日 01:00 RMAN 全备", "保留 4 周，异地保存 1 份"],
            ["增量备份", "每日 01:00 增量", "保留 14 天"],
            ["归档日志", "持续归档，保留 30 天", "支持时间点恢复"],
            ["RPO", "≤ 15 分钟", "归档日志 + 增量备份"],
            ["RTO", "≤ 2 小时", "单实例恢复演练验证"],
            ["恢复演练", "每季度一次", "随机抽取表做表级恢复"],
            ["导出", "每季度 Data Pump 逻辑导出", "用于跨环境迁移和长期归档"],
        ],
        [2.6, 5.8, 6.2], font_size=8.8,
    )
    caption("表 7-4 备份与恢复策略", "table")
    P("开发库 H2 为内存库，不承担持久化，进程退出即清空；需要保留演示数据时使用文件模式或执行 05_seed_data.sql 重建。生产库必须开启归档模式，禁止在 NOARCHIVELOG 模式下运行。")

    H2("7.8 归档与清理")
    P("归档采用“先导出、再验证、后删除”的流程：按分区导出为压缩文件并校验行数，确认备份可用后，用 ALTER TABLE ... DROP PARTITION 或 TRUNCATE PARTITION 清理；ODS 分区优先转储到归档表空间，再删除在线分区。所有清理操作记录在运维日志中，保留操作人、时间、分区名和行数。")
    P("清理任务建议放在每月 1 日 03:00，与同步任务错开；清理前检查是否有评估、候选点或快照引用该批次。由于业务表通过 batch_id 引用同步批次，删除 ODS 批次前应保留 sync_batch 台账和 poi_change_log 摘要，避免结论无法追溯。")

    H2("7.9 性能与扩展")
    bullet_list([
        "读写分离：沿用现有 ReadWriteRoutingDataSource，写事务走主库，@Transactional(readOnly=true) 走只读库；写后立即读的场景强制走主库。",
        "分区裁剪：评估、变更、ODS 查询必须带时间范围，避免全分区扫描；看板查询走 district_score_snapshot，不聚合全量评估明细。",
        "缓存：片区评分、设施类别、画像标签等低频变更数据放 Redis，key 带 batch_id，批次切换时整体失效。",
        "批量写入：同步任务使用 JDBC batch，每 500 行提交一次；合并前先按业务唯一键排序，减少索引随机写。",
        "扩展：当前按单城市设计，保留 city_code 和 district 层级；未来扩城市时按 city_code 做逻辑分库或分区，不改业务模型。",
        "空间查询：当前用经纬度范围 + 应用层 haversine 计算；若 POI 增至十万级，再引入 Oracle Spatial 的 SDO_GEOMETRY 和 R 树索引。",
    ])


# --------------------------------------------------------------------------
# chapter 8
# --------------------------------------------------------------------------
def ch8():
    H1("8 建表脚本与验证")
    H2("8.1 脚本清单")
    add_table(
        ["脚本", "内容", "执行者", "说明"],
        [
            ["01_tablespace_oracle.sql", "4 个表空间与数据文件", "DBA", "需 CREATE TABLESPACE 权限"],
            ["02_schema_oracle.sql", f"{N_TABLES} 张表、注释、索引、分区", "life_circle", "按外键拓扑排序，可直接执行"],
            ["03_schema_h2.sql", "H2 开发库表、约束、索引", "开发", "已用 H2 2.2.224 执行验证"],
            ["04_schema_mysql.sql", "MySQL 8.0 方言", "开发（可选）", "字符集 utf8mb4，InnoDB"],
            ["05_seed_data.sql", "设施类别、标签、演示片区/POI", "life_circle", "可选初始化数据（Oracle）"],
            ["05_seed_data_h2.sql", "同一份初始化数据的 H2 版本", "开发", "已实际执行验证"],
            ["06_views_oracle.sql", "两个看板/统计视图", "life_circle", "依赖表已创建"],
            ["07_migration_v1_to_v2.sql", "merchant_intent 扩展字段与索引", "life_circle", "保留已有数据"],
            ["08_validation_report.txt", "H2 建表与初始化数据验证记录", "开发", "交付验证证据"],
        ],
        [4.6, 5.6, 2.0, 2.4], font_size=8.4,
    )
    caption("表 8-1 建表脚本清单", "table")

    H2("8.2 Oracle 建表步骤")
    P("以 DBA 身份创建表空间，再以业务用户 life_circle 连接 FREEPDB1 执行建表、种子数据和视图脚本。脚本开头 SET DEFINE OFF，避免注释或数据中的 & 被 SQL*Plus 当作替换变量。")
    code_block("""-- 1. DBA 创建表空间
@01_tablespace_oracle.sql
-- 2. 业务用户建表（按外键依赖顺序）
@02_schema_oracle.sql
-- 3. 可选：初始化字典和演示数据
@05_seed_data.sql
-- 4. 创建视图
@06_views_oracle.sql
-- 5. 已有 V1 库升级
@07_migration_v1_to_v2.sql""", size=8)
    P("Oracle 脚本包含表注释、字段注释、主键、唯一约束、检查约束、外键、普通索引、LOB 存储和分区子句。建表顺序按外键依赖拓扑排序，先建 app_user、district、profile_tag、facility_category、sync_batch 等被引用表，再建业务表。")

    H2("8.3 H2 与 MySQL 适配")
    P("H2 脚本去掉表空间、分区、SecureFiles 和 ON DELETE RESTRICT 等 Oracle 专属语法，保留表、字段、主键、唯一、检查、外键和普通索引，用于 Spring Boot 启动和单元测试。MySQL 脚本把 NUMBER 映射为 BIGINT/INT/DECIMAL，把 CLOB 映射为 LONGTEXT，把 TIMESTAMP 映射为 DATETIME(6)，字符集统一 utf8mb4。")
    P("三套脚本的字段顺序、约束名称和索引名称保持一致，便于对照排查。MySQL 脚本不启用分区，因为 MySQL 分区表不支持外键；如未来以 MySQL 为生产库，需要把分区表改为普通表并调整归档策略。")

    H2("8.4 执行验证结果")
    P("H2 2.2.224（MODE=Oracle）已实际执行 03_schema_h2.sql，建表过程无错误；随后查询 INFORMATION_SCHEMA 验证对象数量。验证命令与结果如下：")
    code_block("""java -cp h2-2.2.224.jar org.h2.tools.RunScript ^
  -url "jdbc:h2:file:./h2lifecircle;MODE=Oracle" -user sa ^
  -script 03_schema_h2.sql
-- 输出：无异常，退出码 0

SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
 WHERE TABLE_SCHEMA='PUBLIC' AND TABLE_TYPE='BASE TABLE';
-- 27
SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
 WHERE CONSTRAINT_TYPE='FOREIGN KEY';
-- 41""", size=7.8)
    add_table(
        ["验证项", "预期", "实际", "结论"],
        [
            ["表数量", "27", "27", "通过"],
            ["字段数量", "258", "258", "通过"],
            ["外键约束", "41", "41", "通过"],
            ["检查约束", "83", "83", "通过"],
            ["建表错误", "0", "0", "通过"],
            ["Oracle 语法审查", "人工复核", "完成", "通过（未在真实 Oracle 实例执行）"],
            ["MySQL 脚本", "语法审查", "完成", "通过（未在真实 MySQL 实例执行）"],
        ],
        [3.6, 3.0, 3.0, 5.0], font_size=9, align_center={1, 2, 3},
    )
    caption("表 8-2 建表脚本验证结果", "table")
    P("在同一 H2 文件库上继续执行 05_seed_data_h2.sql，初始化数据全部写入成功：设施类别 13 条、画像标签 8 条、片区 3 条、同步批次 1 条、演示 POI 6 条。验证命令与结果已整理为 sql/08_validation_report.txt，随交付包一并提供。")
    note_box("说明：H2 验证覆盖表、字段、主键、唯一、检查、外键和索引；Oracle 的表空间、分区、SecureFiles、IDENTITY 等专属语法已按 Oracle 23ai 文档逐项核对，但当前环境没有可用的 Oracle 实例，正式上线前需在目标库执行一次 01/02 脚本并复核告警。")

    H2("8.5 V1 到 V2 迁移")
    P("现有工程只有 merchant_intent 一张业务表，V1 结构为 id、merchant_name、business_type、contact、created_at。V2 保留这 5 个字段，新增 contact_masked、district_id、candidate_id、budget_min、budget_max、area_sqm、remark、status、updated_at，并把 contact 扩展到 200 字符用于存放密文。")
    P("迁移脚本先修改 contact 长度，再添加可空字段和带默认值的 status/updated_at，最后补外键和索引。历史明文 contact 需要在应用层一次性加密并回写，迁移脚本不直接处理明文，避免在 SQL 日志中泄露。升级完成后，接口返回值由服务层解密，列表页只返回 contact_masked。")

    H2("8.6 后续代码接入")
    P("数据库设计完成后，后端按“实体—Repository—Service—Controller”的顺序接入。建议先接居民评估与设施查询，再接商户选址和意向，最后接社区治理和同步任务；每接一个模块，补一组接口测试和数据库集成测试。")
    add_table(
        ["模块", "优先接入表", "建议实体", "说明"],
        [
            ["用户画像", "app_user、user_profile、profile_tag、user_profile_tag、profile_dimension_weight", "AppUser、UserProfile、ProfileTag 等", "登录与画像生成"],
            ["居民评估", "resident_assessment、assessment_dimension、assessment_facility_stat", "ResidentAssessment、AssessmentDimension", "替换 DemoController 的演示数据"],
            ["商户选址", "site_candidate、site_score_item、merchant_intent、merchant_match", "SiteCandidate、SiteScoreItem、MerchantIntent", "merchant_intent 扩展现有实体"],
            ["社区治理", "community_gap、simulation_record、district_score_snapshot", "CommunityGap、SimulationRecord", "看板与模拟"],
            ["数据同步", "sync_batch、poi_change_log、data_quality_issue、ods_*", "SyncBatch、PoiChangeLog", "半月任务与质量报告"],
        ],
        [2.4, 6.2, 4.4, 1.6], font_size=8.4,
    )
    caption("表 8-3 模块与实体接入建议", "table")
    P("JPA 映射注意三点：一是 Oracle IDENTITY 对应 @GeneratedValue(strategy = GenerationType.IDENTITY)；二是 Instant 映射 TIMESTAMP(6)，统一用 UTC；三是 CLOB 字段用 @Lob 或 columnDefinition 指定，避免 Hibernate 默认生成不匹配的类型。开发库 ddl-auto 建议改为 validate，以脚本为准，避免实体自动改表。")


# --------------------------------------------------------------------------
# chapter 9
# --------------------------------------------------------------------------
def ch9():
    H1("9 结论")
    P(f"本文档完成了城市 15 分钟便民生活圈与小微开店智能助手的数据库设计：识别了 6 个主题域、{N_COLS} 个数据项，建立了 {N_TABLES} 张表、{N_FKS} 个外键的数据模型，给出了 ODS/DWD/ADS 三层数据规划架构，完成了 Oracle、H2、MySQL 三套建表脚本，并对表空间、分区、索引、LOB、容量、备份和归档做了系统规划。")
    P("模型在覆盖业务闭环的同时保持了可实施性：一方面保留现有 merchant_intent 并给出迁移路径，另一方面为居民评估、商户选址、社区治理和数据同步预留了完整的持久化结构；所有枚举、命名、类型和安全口径与现有工程及《数据项约定规范》对齐。")
    P("下一阶段建议按第 8.6 节的顺序接入代码：先用 H2 脚本跑通实体与 Repository，再在 Oracle 测试库执行 01/02/05/06 脚本验证真实方言，最后补接口测试、数据质量报告和看板查询。数据库结构变更时，坚持“先改 DBML/文档，再生成脚本，最后改代码”的顺序，保持模型、脚本、文档和代码四处一致。")


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def build(page_map, out_path):
    global doc, PAGE_MAP, CUR_CH, TBL_NO, FIG_NO
    PAGE_MAP = page_map
    CUR_CH = 0
    TBL_NO = Counter()
    FIG_NO = Counter()
    doc = Document(TEMPLATE)
    setup_cover()
    setup_toc_title()
    clear_after_toc_title()
    add_toc_entries()
    add_header_footer()

    # content
    ch1()
    ch2()
    ch3()
    ch4()
    ch5()
    ch6()
    ch7()
    ch8()
    ch9()

    # core properties
    cp = doc.core_properties
    cp.title = "城市15分钟便民生活圈与小微开店智能助手 数据库设计说明书"
    cp.subject = "数据库设计 V2.0"
    cp.author = "6组"
    cp.keywords = "数据库设计, dbdiagram.io, DBML, Oracle, 数据项, 存储结构"
    cp.comments = "由统一数据模型自动生成"

    # remove trailing empty paragraphs
    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    children = list(body.iterchildren())
    idx = children.index(sect)
    for ch in reversed(children[:idx]):
        if ch.tag == qn("w:p") and not "".join(ch.itertext()).strip() and ch.find(".//" + qn("w:drawing")) is None:
            body.remove(ch)
        else:
            break

    doc.save(out_path)
    print("saved", out_path)


def extract_page_map(pdf_path, titles):
    # pypdf 从当前环境导入；这里保留脚本目录在 sys.path 上，便于放本地依赖。
    sys.path.insert(0, HERE)
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    texts = []
    for p in reader.pages:
        t = p.extract_text() or ""
        t = re.sub(r"\s+", "", t)
        texts.append(t)

    def norm(s):
        return re.sub(r"\s+", "", s)

    # locate body start: page containing 1.1 and 1.2 but not the TOC page
    body_start = None
    for i, t in enumerate(texts):
        if "1.1编写目的" in t and "1.2项目范围与数据边界" in t and "目录" not in t[:50]:
            body_start = i
            break
    if body_start is None:
        body_start = 3
    page_map = {}
    last = body_start
    for title in titles:
        key = norm(title)
        found = None
        for i in range(last, len(texts)):
            if key in texts[i]:
                found = i + 1
                last = i
                break
        if found is None:
            # try without numbering
            short = re.sub(r"^[0-9.]+", "", key)
            for i in range(last, len(texts)):
                if short and short in texts[i]:
                    found = i + 1
                    last = i
                    break
        page_map[title] = found if found else "—"
    print("body_start", body_start + 1, "pages", len(texts), "mapped", sum(1 for v in page_map.values() if v != "—"))
    return page_map


if __name__ == "__main__":
    # pass 1: 目录页码先用占位符，导出临时 PDF 用于提取真实页码
    tmp = os.path.join(TMP_DIR, "design_pass1.docx")
    build({}, tmp)
    # convert pass 1 to PDF
    import subprocess
    # 可用环境变量覆盖这两个路径，适配不同机器上的 Node 与 LibreOffice Kit 安装位置。
    node = os.environ.get("NODE_BIN") or shutil.which("node") or r"D:\AI\deepseek\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
    cli = os.environ.get("LIBREOFFICE_KIT_CLI") or (
        r"D:\AI\deepseek\resources\app.asar.unpacked\dsh\node_modules"
        r"\@deepseek-ai\libreoffice-kit\lib\cli.js"
    )
    pdf1 = os.path.join(TMP_DIR, "design_pass1.pdf")
    for f in (pdf1,):
        if os.path.exists(f):
            os.remove(f)
    subprocess.run([node, cli, "convert", "--input", tmp, "--output", pdf1], check=True)
    titles = [t for lv, t in OUTLINE if lv <= 2]
    pm = extract_page_map(pdf1, titles)
    # pass 2: 回填真实页码后生成正式文档
    build(pm, DOCX)
    if os.path.exists(PDF):
        os.remove(PDF)
    subprocess.run([node, cli, "convert", "--input", DOCX, "--output", PDF], check=True)
    # check body start stable
    pm2 = extract_page_map(PDF, titles)
    changed = [(k, pm.get(k), pm2.get(k)) for k in titles if pm.get(k) != pm2.get(k)]
    print("page-map changes:", len(changed))
    for x in changed[:10]:
        print(" ", x)
