# -*- coding: utf-8 -*-
import sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

SRC = r"C:\Users\123456\Desktop\Pro\work\template.docx"
DST = r"C:\Users\123456\Desktop\Pro\10月25日任务\数据库设计说明书.docx"
ER = r"C:\Users\123456\Desktop\Pro\work\er_final.png"

doc = Document(SRC)
body = doc.element.body
paras = doc.paragraphs


def ptext(p):
    return p.text


def find_para(text, start=0):
    for i in range(start, len(paras)):
        if paras[i].text.strip() == text:
            return i
    raise KeyError(text)


def set_run(run, font="宋体", size=14, bold=False, color="000000"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = False
    run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), font)
    rFonts.set(qn("w:hAnsi"), font)
    rFonts.set(qn("w:eastAsia"), font)
    rFonts.set(qn("w:cs"), font)


def clear_runs(p):
    for child in list(p._p):
        if child.tag in (qn("w:r"), qn("w:hyperlink"), qn("w:fldSimple")):
            p._p.remove(child)
        elif child.tag == qn("w:bookmarkStart") or child.tag == qn("w:bookmarkEnd"):
            p._p.remove(child)


def style_para(p, indent_chars=200, line=360, before=0, after=0, align=None, size=14):
    pPr = p._p.get_or_add_pPr()
    for tag in ("w:ind", "w:spacing", "w:jc", "w:snapToGrid"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    rPr = pPr.find(qn("w:rPr"))

    def add(el):
        if rPr is not None:
            rPr.addprevious(el)
        else:
            pPr.append(el)

    snap = OxmlElement("w:snapToGrid")
    snap.set(qn("w:val"), "false")
    add(snap)
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:line"), str(line))
    sp.set(qn("w:lineRule"), "auto")
    sp.set(qn("w:before"), str(before))
    sp.set(qn("w:after"), str(after))
    add(sp)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:firstLineChars"), str(indent_chars))
    ind.set(qn("w:firstLine"), str(int(indent_chars / 100 * size * 20)))
    add(ind)
    if align is not None:
        jc = OxmlElement("w:jc")
        jc.set(qn("w:val"), align)
        add(jc)


def new_para_after(anchor_el, text, size=14, bold=False, indent=200, line=360,
                   before=0, after=0, font="宋体", align=None):
    p_el = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    pStyle = OxmlElement("w:pStyle")
    pStyle.set(qn("w:val"), "Normal")
    pPr.append(pStyle)
    p_el.append(pPr)
    anchor_el.addnext(p_el)
    p = Paragraph(p_el, doc)
    run = p.add_run(text)
    set_run(run, font, size, bold)
    style_para(p, indent, line, before, after, align, size)
    return p


def fill_para(p, text, size=14, bold=False, indent=200, line=360, align=None):
    clear_runs(p)
    run = p.add_run(text)
    set_run(run, "宋体", size, bold)
    style_para(p, indent, line, 0, 0, align, size)


# ---------------------------------------------------------------- cover
i = find_para("（模板）")
p = paras[i]
clear_runs(p)
r = p.add_run("城市 15 分钟便民生活圈")
set_run(r, "黑体", 20, True)
r.add_break()
r2 = p.add_run("与小微开店智能助手")
set_run(r2, "黑体", 20, True)

# ---------------------------------------------------------------- 1.1
i = find_para("编写目的")
anchor = paras[i + 1]  # empty paragraph after heading
purpose = [
    "本文档用于说明“城市 15 分钟便民生活圈与小微开店智能助手”的数据库设计，作为课程项目开发、联调和验收的依据。文档以本地工程 Project/Class-Test 与 GitHub 仓库 https://github.com/OKeyDokiDoki/Class-Test 的现有代码为基础编写，明确当前版本的数据存储范围、数据库环境、命名规则、逻辑关系、物理表结构和建表脚本，使前后端开发对字段名称、数据类型和约束保持一致。",
    "当前代码中真正落库的业务对象只有商户开店意向 MerchantIntent，对应接口 POST /api/merchant/intents 与 GET /api/merchant/intents；居民生活圈评估、商户选址推荐、社区综合概览和网点模拟等接口仍返回演示数据，尚未建立持久化表。因此本文档在物理设计中把 merchant_intent 作为已实现表，其余表按接口字段和后续迭代计划作为规划表列出，便于下一阶段直接建表接入。",
    "文档随代码同步演进：表结构、字段或枚举取值发生变化时，应先修订本文档，再修改实体类、建表脚本和前端字段，保证三处一致。",
]
fill_para(anchor, purpose[0])
cur = anchor._p
for t in purpose[1:]:
    cur = new_para_after(cur, t)._p

# ---------------------------------------------------------------- 1.2 terms
terms = [
    ("1", "H2", "嵌入式内存数据库，开发环境使用；应用启动时按实体自动建表，进程退出后数据清空"),
    ("2", "Oracle", "生产环境关系型数据库，使用 Oracle Database 23ai Free，服务名 FREEPDB1"),
    ("3", "POI", "Point of Interest，兴趣点，指社区周边的生鲜、医疗、教育、交通等设施网点"),
]
t = doc.tables[0]
for ri, (no, name, desc) in enumerate(terms, start=1):
    vals = [no, name, desc]
    for ci, v in enumerate(vals):
        cell = t.cell(ri, ci)
        p = cell.paragraphs[0]
        clear_runs(p)
        run = p.add_run(v)
        set_run(run, "仿宋", 12)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 2 else WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

# ---------------------------------------------------------------- 2 environment
env = [
    ("开发", "H2 2.x", "本地 Spring Boot 进程内", "JPA / Hibernate",
     "Oracle 模式（MODE=Oracle）；连接 jdbc:h2:mem:lifecircle，启动自动建表，用于联调与测试"),
    ("生产", "Oracle 23ai Free", "Docker 或独立主从服务器", "HikariCP + JPA",
     "主库 life_circle 写入，只读库 life_circle_readonly 查询；未配置只读库时回退主库"),
]
t = doc.tables[1]
for ri, row in enumerate(env, start=1):
    for ci, v in enumerate(row):
        cell = t.cell(ri, ci)
        p = cell.paragraphs[0]
        clear_runs(p)
        run = p.add_run(v)
        set_run(run, "仿宋", 9)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 4 else WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

# ---------------------------------------------------------------- 3 naming rules
i = find_para("//此处对所有数据库对象命名规则进行说明；")
rules = [
    "（1）表名：采用小写字母加下划线的单数名词，不使用拼音和表前缀，例如 merchant_intent、poi_facility。",
    "（2）字段名：小写字母加下划线，单词之间以下划线分隔，例如 merchant_name、created_at；布尔含义的字段以 is_ 开头。",
    "（3）主键统一命名为 id；外键命名为“被引用表名_id”，例如 district_id、assessment_id；时间字段以 _at 结尾，评分字段以 _score 结尾。",
    "（4）索引：普通索引 idx_表名_字段名，唯一索引 uk_表名_字段名；约束：主键 pk_表名，外键 fk_表名_字段名，检查约束 ck_表名_字段名。",
    "（5）Oracle 标识符不区分大小写，统一按大写存储；H2 开发库通过 MODE=Oracle 保持与生产库一致的语法和类型行为。",
    "（6）Java 实体使用驼峰命名，由 Hibernate 默认命名策略转换为下划线列名，例如 merchantName 对应 merchant_name；接口 JSON 字段保持驼峰，与前端数据项约定一致。",
    "（7）枚举类字段以 VARCHAR 存储中文业务值（如“充足”“基本满足”“待改善”），取值必须与前端展示逐字一致，不使用数字编码。",
]
fill_para(paras[i], rules[0])
cur = paras[i]._p
for t_ in rules[1:]:
    cur = new_para_after(cur, t_)._p

# ---------------------------------------------------------------- 4 logical design
i = find_para("//此处导出用相关设计工具绘制的数据对象关系图；")
p4 = paras[i]
fill_para(p4, "系统按“片区—设施—评估—选址—模拟”组织数据，各数据对象的关系如图 4-1 所示。片区 district 是全局主数据，设施网点、居民评估、选址候选点、社区短板和模拟记录均通过 district_id 关联到片区，评估维度通过 assessment_id 关联评估记录；商户开店意向 merchant_intent 当前独立存储，未设置片区外键。关系图使用 PlantUML 绘制，以 SVG 矢量图插入正文，可无损缩放，源文件 er.puml 随文档一并提交。")

pic_p = new_para_after(p4._p, "", indent=0, line=240, before=120, after=0, align="center")
run = pic_p.add_run()
run.add_picture(ER, width=Cm(13.2))
pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

cap = new_para_after(pic_p._p, "图 4-1 数据对象关系图", size=10.5, indent=0, line=240, before=60, after=120, align="center")

# ---------------------------------------------------------------- 5.1 table summary
tables = [
    ("merchant_intent", "商户开店意向表（已实现）"),
    ("district", "社区片区基础信息表"),
    ("poi_facility", "社区设施网点 POI 表"),
    ("resident_assessment", "居民生活圈评估记录表"),
    ("assessment_dimension", "评估维度得分明细表"),
    ("site_candidate", "商户选址候选点表"),
    ("community_gap", "社区短板片区表"),
    ("simulation_record", "网点增设模拟记录表"),
]
t = doc.tables[2]
# delete extra rows (keep header + len(tables))
while len(t.rows) - 1 > len(tables):
    t._tbl.remove(t.rows[-1]._tr)
for ri, (name, desc) in enumerate(tables, start=1):
    for ci, v in enumerate((name, desc)):
        cell = t.cell(ri, ci)
        p = cell.paragraphs[0]
        clear_runs(p)
        run = p.add_run(v)
        set_run(run, "仿宋", 10.5)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

# ---------------------------------------------------------------- 5.2 table designs
designs = [
    ("表4-1 merchant_intent 商户开店意向表", "merchant_intent", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("merchant_name", "VARCHAR", "100", "否", "", "商户名称"),
        ("business_type", "VARCHAR", "100", "否", "", "经营业态"),
        ("contact", "VARCHAR", "100", "否", "", "联系方式"),
        ("created_at", "TIMESTAMP", "6", "否", "", "创建时间"),
    ]),
    ("表4-2 district 社区片区表", "district", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("district_name", "VARCHAR", "100", "否", "", "片区名称"),
        ("city_code", "VARCHAR", "20", "是", "", "行政区划代码"),
        ("center_lng", "DECIMAL", "10,6", "是", "", "中心点经度"),
        ("center_lat", "DECIMAL", "10,6", "是", "", "中心点纬度"),
        ("resident_count", "INT", "11", "是", "", "服务人口"),
        ("created_at", "TIMESTAMP", "6", "否", "", "创建时间"),
    ]),
    ("表4-3 poi_facility 设施网点表", "poi_facility", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("district_id", "BIGINT", "19", "否", "", "所属片区，外键"),
        ("poi_name", "VARCHAR", "200", "否", "", "设施名称"),
        ("category", "VARCHAR", "50", "否", "", "设施类别"),
        ("lng", "DECIMAL", "10,6", "否", "", "经度"),
        ("lat", "DECIMAL", "10,6", "否", "", "纬度"),
        ("address", "VARCHAR", "255", "是", "", "详细地址"),
        ("facility_status", "VARCHAR", "20", "是", "", "设施状态"),
        ("source", "VARCHAR", "20", "是", "", "数据来源"),
        ("updated_at", "TIMESTAMP", "6", "否", "", "更新时间"),
    ]),
    ("表4-4 resident_assessment 居民生活圈评估表", "resident_assessment", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("resident_code", "VARCHAR", "64", "否", "", "居民标识（脱敏）"),
        ("district_id", "BIGINT", "19", "否", "", "所属片区，外键"),
        ("total_score", "INT", "3", "否", "", "综合评分，0-100"),
        ("profile_label", "VARCHAR", "50", "是", "", "人群画像标签"),
        ("insight", "VARCHAR", "500", "是", "", "诊断建议"),
        ("assessed_at", "TIMESTAMP", "6", "否", "", "评估时间"),
    ]),
    ("表4-5 assessment_dimension 评估维度得分表", "assessment_dimension", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("assessment_id", "BIGINT", "19", "否", "", "评估记录，外键"),
        ("dimension_name", "VARCHAR", "50", "否", "", "维度名称"),
        ("dimension_score", "INT", "3", "否", "", "维度得分，0-100"),
    ]),
    ("表4-6 site_candidate 商户选址候选点表", "site_candidate", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("district_id", "BIGINT", "19", "否", "", "所属片区，外键"),
        ("candidate_name", "VARCHAR", "100", "否", "", "候选点名称"),
        ("business_type", "VARCHAR", "100", "是", "", "适配经营业态"),
        ("demand_level", "VARCHAR", "10", "是", "", "需求强度"),
        ("competition_level", "VARCHAR", "10", "是", "", "竞争度"),
        ("rent_range", "VARCHAR", "50", "是", "", "租金区间"),
        ("site_score", "INT", "3", "是", "", "选址评分，0-100"),
        ("lng", "DECIMAL", "10,6", "是", "", "经度"),
        ("lat", "DECIMAL", "10,6", "是", "", "纬度"),
        ("created_at", "TIMESTAMP", "6", "否", "", "创建时间"),
    ]),
    ("表4-7 community_gap 社区短板片区表", "community_gap", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("district_id", "BIGINT", "19", "否", "", "所属片区，外键"),
        ("area_name", "VARCHAR", "100", "否", "", "短板片区名称"),
        ("issue", "VARCHAR", "200", "否", "", "短板描述"),
        ("gap_level", "VARCHAR", "10", "否", "", "缺口等级"),
        ("created_at", "TIMESTAMP", "6", "否", "", "创建时间"),
    ]),
    ("表4-8 simulation_record 网点增设模拟记录表", "simulation_record", [
        ("id", "BIGINT", "19", "否", "是", "主键，自增"),
        ("district_id", "BIGINT", "19", "否", "", "所属片区，外键"),
        ("business_type", "VARCHAR", "100", "否", "", "模拟新增业态"),
        ("before_coverage", "INT", "3", "否", "", "模拟前覆盖率（%）"),
        ("after_coverage", "INT", "3", "否", "", "模拟后覆盖率（%）"),
        ("benefited_residents", "INT", "11", "否", "", "受益人口"),
        ("operator", "VARCHAR", "50", "是", "", "操作人"),
        ("simulated_at", "TIMESTAMP", "6", "否", "", "模拟时间"),
    ]),
]

i35 = find_para("//用工具导出各个表结构设计明细；")
fill_para(paras[i35], "各表结构如下：表 4-1 为当前代码已落库的表，字段与 MerchantIntent 实体一一对应；表 4-2 至表 4-8 为规划表，字段按现有接口返回值和前端数据项约定设计，供后续迭代建表使用。")

cap_tpl = paras[find_para("表4-1 XXX表")]
tbl_tpl = doc.tables[3]

# fill first caption/table
cap_tpl_text = designs[0][0]
clear_runs(cap_tpl)
r = cap_tpl.add_run(cap_tpl_text)
set_run(r, "宋体", 10.5, False)
cap_tpl.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap_tpl.paragraph_format.keep_with_next = True


def fill_table(tbl, table_name, rows):
    # table name row (merged cell 0,1)
    c = tbl.cell(0, 1)
    p = c.paragraphs[0]
    clear_runs(p)
    run = p.add_run(table_name)
    set_run(run, "仿宋", 12)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # data rows: header + 2 placeholders -> need len(rows)
    while len(tbl.rows) - 2 > len(rows):
        tbl._tbl.remove(tbl.rows[-1]._tr)
    while len(tbl.rows) - 2 < len(rows):
        new_tr = copy.deepcopy(tbl.rows[-1]._tr)
        tbl._tbl.append(new_tr)
    for ri, row in enumerate(rows, start=2):
        for ci, v in enumerate(row):
            cell = tbl.cell(ri, ci)
            p = cell.paragraphs[0]
            clear_runs(p)
            run = p.add_run(str(v))
            set_run(run, "仿宋", 10.5)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


fill_table(tbl_tpl, designs[0][1], designs[0][2])

# append the remaining 7 caption+table pairs after tbl_tpl
anchor_el = tbl_tpl._tbl
for caption, tname, rows in designs[1:]:
    cap_el = copy.deepcopy(cap_tpl._p)
    anchor_el.addnext(cap_el)
    cap = Paragraph(cap_el, doc)
    clear_runs(cap)
    r = cap.add_run(caption)
    set_run(r, "宋体", 10.5, False)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.keep_with_next = True

    tbl_el = copy.deepcopy(tbl_tpl._tbl)
    cap_el.addnext(tbl_el)
    from docx.table import Table
    new_tbl = Table(tbl_el, doc)
    fill_table(new_tbl, tname, rows)
    anchor_el = tbl_el


def set_col_widths(tbl, widths):
    grid = tbl._tbl.tblGrid
    for c, w in zip(grid.findall(qn("w:gridCol")), widths):
        c.set(qn("w:w"), str(w))
    for tr in tbl._tbl.tr_lst:
        i = 0
        for tc in tr.tc_lst:
            span = 1
            tcPr = tc.tcPr
            if tcPr is not None and tcPr.gridSpan is not None:
                span = tcPr.gridSpan.val
            w = sum(widths[i:i + span])
            i += span
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.append(tcW)
            tcW.set(qn("w:w"), str(w))
            tcW.set(qn("w:type"), "dxa")


DETAIL_WIDTHS = [2400, 1500, 850, 800, 800, 2122]
for tbl in doc.tables[3:]:
    set_col_widths(tbl, DETAIL_WIDTHS)
set_col_widths(doc.tables[2], [2600, 5814])

# start physical design on a new page so the table summary is not split
i = find_para("5物理设计")
pPr = paras[i]._p.get_or_add_pPr()
pb = OxmlElement("w:pageBreakBefore")
pStyle = pPr.find(qn("w:pStyle"))
if pStyle is not None:
    pStyle.addnext(pb)
else:
    pPr.insert(0, pb)

# drop blank paragraphs right before page-break headings, otherwise an empty
# paragraph can spill onto the new page and create a blank sheet
for heading in ("数据库的命名规则", "4逻辑设计", "5物理设计", "6 脚本文件"):
    h = paras[find_para(heading)]._p
    prev = h.getprevious()
    while prev is not None and prev.tag == qn("w:p") and not "".join(prev.itertext()).strip() \
            and prev.find(".//" + qn("w:drawing")) is None and prev.find(".//" + qn("w:pict")) is None:
        nxt = prev.getprevious()
        h.getparent().remove(prev)
        prev = nxt

# ---------------------------------------------------------------- 6 scripts
i40 = find_para("//用工具导出各个数据对象的运行sql文件；")
fill_para(paras[i40], "（1）开发环境 H2：应用启动时由 JPA 按实体自动建表（ddl-auto=update），无需手工执行。完整建表脚本已导出为 schema-h2.sql，与实体定义等价；已实现表 merchant_intent 的语句如下，其余规划表见脚本文件。")

H2_SQL = """CREATE TABLE merchant_intent (
    id            BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    merchant_name VARCHAR(100) NOT NULL,
    business_type VARCHAR(100) NOT NULL,
    contact       VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP(6) NOT NULL
);
CREATE INDEX idx_merchant_intent_created_at ON merchant_intent (created_at);"""

ORA_DDL = """-- 商户开店意向表（已实现，对应实体 MerchantIntent）
CREATE TABLE merchant_intent (
    id            NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    merchant_name VARCHAR2(100) NOT NULL,
    business_type VARCHAR2(100) NOT NULL,
    contact       VARCHAR2(100) NOT NULL,
    created_at    TIMESTAMP(6)  NOT NULL,
    CONSTRAINT pk_merchant_intent PRIMARY KEY (id)
);
COMMENT ON TABLE merchant_intent IS '商户开店意向表';
COMMENT ON COLUMN merchant_intent.merchant_name IS '商户名称';
COMMENT ON COLUMN merchant_intent.business_type IS '经营业态';
COMMENT ON COLUMN merchant_intent.contact IS '联系方式';
COMMENT ON COLUMN merchant_intent.created_at IS '创建时间';
CREATE INDEX idx_merchant_intent_created_at ON merchant_intent (created_at);

-- 社区片区表（规划）
CREATE TABLE district (
    id            NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    district_name VARCHAR2(100) NOT NULL,
    city_code     VARCHAR2(20),
    center_lng    NUMBER(10,6),
    center_lat    NUMBER(10,6),
    resident_count NUMBER(11),
    created_at    TIMESTAMP(6)  DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT pk_district PRIMARY KEY (id)
);

-- 设施网点表（规划）
CREATE TABLE poi_facility (
    id              NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    district_id     NUMBER(19)    NOT NULL,
    poi_name        VARCHAR2(200) NOT NULL,
    category        VARCHAR2(50)  NOT NULL,
    lng             NUMBER(10,6)  NOT NULL,
    lat             NUMBER(10,6)  NOT NULL,
    address         VARCHAR2(255),
    facility_status VARCHAR2(20),
    source          VARCHAR2(20),
    updated_at      TIMESTAMP(6)  NOT NULL,
    CONSTRAINT pk_poi_facility PRIMARY KEY (id),
    CONSTRAINT fk_poi_district FOREIGN KEY (district_id) REFERENCES district (id)
);
CREATE INDEX idx_poi_facility_district ON poi_facility (district_id, category);

-- 居民生活圈评估表（规划）
CREATE TABLE resident_assessment (
    id            NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    resident_code VARCHAR2(64)  NOT NULL,
    district_id   NUMBER(19)    NOT NULL,
    total_score   NUMBER(3)     NOT NULL,
    profile_label VARCHAR2(50),
    insight       VARCHAR2(500),
    assessed_at   TIMESTAMP(6)  NOT NULL,
    CONSTRAINT pk_resident_assessment PRIMARY KEY (id),
    CONSTRAINT fk_assessment_district FOREIGN KEY (district_id) REFERENCES district (id)
);

-- 评估维度得分表（规划）
CREATE TABLE assessment_dimension (
    id             NUMBER(19)   GENERATED BY DEFAULT AS IDENTITY,
    assessment_id  NUMBER(19)   NOT NULL,
    dimension_name VARCHAR2(50) NOT NULL,
    dimension_score NUMBER(3)   NOT NULL,
    CONSTRAINT pk_assessment_dimension PRIMARY KEY (id),
    CONSTRAINT fk_dimension_assessment FOREIGN KEY (assessment_id)
        REFERENCES resident_assessment (id),
    CONSTRAINT uk_dimension UNIQUE (assessment_id, dimension_name)
);

-- 商户选址候选点表（规划）
CREATE TABLE site_candidate (
    id                NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    district_id       NUMBER(19)    NOT NULL,
    candidate_name    VARCHAR2(100) NOT NULL,
    business_type     VARCHAR2(100),
    demand_level      VARCHAR2(10),
    competition_level VARCHAR2(10),
    rent_range        VARCHAR2(50),
    site_score        NUMBER(3),
    lng               NUMBER(10,6),
    lat               NUMBER(10,6),
    created_at        TIMESTAMP(6)  NOT NULL,
    CONSTRAINT pk_site_candidate PRIMARY KEY (id),
    CONSTRAINT fk_candidate_district FOREIGN KEY (district_id) REFERENCES district (id)
);

-- 社区短板片区表（规划）
CREATE TABLE community_gap (
    id          NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    district_id NUMBER(19)    NOT NULL,
    area_name   VARCHAR2(100) NOT NULL,
    issue       VARCHAR2(200) NOT NULL,
    gap_level   VARCHAR2(10)  NOT NULL,
    created_at  TIMESTAMP(6)  NOT NULL,
    CONSTRAINT pk_community_gap PRIMARY KEY (id),
    CONSTRAINT fk_gap_district FOREIGN KEY (district_id) REFERENCES district (id)
);

-- 网点增设模拟记录表（规划）
CREATE TABLE simulation_record (
    id                  NUMBER(19)    GENERATED BY DEFAULT AS IDENTITY,
    district_id         NUMBER(19)    NOT NULL,
    business_type       VARCHAR2(100) NOT NULL,
    before_coverage     NUMBER(3)     NOT NULL,
    after_coverage      NUMBER(3)     NOT NULL,
    benefited_residents NUMBER(11)    NOT NULL,
    operator            VARCHAR2(50),
    simulated_at        TIMESTAMP(6)  NOT NULL,
    CONSTRAINT pk_simulation_record PRIMARY KEY (id),
    CONSTRAINT fk_simulation_district FOREIGN KEY (district_id) REFERENCES district (id)
);"""


def add_code_block(anchor, code):
    cur = anchor
    for line in code.split("\n"):
        p = new_para_after(cur, line if line else " ", size=9, indent=0, line=240,
                           before=0, after=0, font="宋体", align="left")
        # no first line indent
        cur = p._p
    return cur


cur = paras[i40]._p
cur = add_code_block(cur, H2_SQL)
cur = new_para_after(cur, "（2）生产环境 Oracle：同一结构按 Oracle 类型映射后导出为 schema-oracle.sql，在 FREEPDB1 中以 life_circle 用户执行。已实现表可直接创建；规划表在对应功能开发时启用，外键已按前文逻辑关系建立。两份脚本均使用 H2 2.2.224 的 RunScript 工具在 MODE=Oracle 下执行验证，8 张表全部创建成功，正式 Oracle 库执行前请按目标库规范复核。",
                     size=14, before=120)._p
cur = add_code_block(cur, ORA_DDL)
cur = new_para_after(cur, "脚本文件 schema-h2.sql、schema-oracle.sql 与关系图源文件 er.puml 均与本文档同目录存放。脚本字段长度、非空约束和主键策略以本文档第 5 章为准，数据库结构变更时应同步更新脚本并纳入版本管理。",
                     size=14, before=120)._p

# ---------------------------------------------------------------- keep tables intact
for tbl in doc.tables:
    rows = tbl.rows
    for row in rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True

# start logical design and script sections on new pages
for heading in ("数据库的命名规则", "4逻辑设计", "6 脚本文件"):
    idx = find_para(heading)
    pPr = paras[idx]._p.get_or_add_pPr()
    pb = OxmlElement("w:pageBreakBefore")
    pStyle = pPr.find(qn("w:pStyle"))
    if pStyle is not None:
        pStyle.addnext(pb)
    else:
        pPr.insert(0, pb)

# drop trailing empty paragraphs so they cannot produce a blank last page
body_el = doc.element.body
for child in list(body_el.iterchildren()):
    if child.tag == qn("w:sectPr"):
        continue
last = body_el[-1]
if last.tag == qn("w:sectPr"):
    last = last.getprevious()
while last is not None and last.tag == qn("w:p") and not "".join(last.itertext()).strip() \
        and last.find(".//" + qn("w:drawing")) is None and last.find(".//" + qn("w:pict")) is None:
    prev = last.getprevious()
    body_el.remove(last)
    last = prev

# ---------------------------------------------------------------- footer page numbers
section = doc.sections[0]
section.different_first_page_header_footer = True
footer = section.footer
fp = footer.paragraphs[0]
fp.text = ""
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_field_run(par, instr, placeholder):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "宋体")
    rFonts.set(qn("w:hAnsi"), "宋体")
    rFonts.set(qn("w:eastAsia"), "宋体")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "18")
    rPr.append(rFonts)
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = placeholder
    r.append(t)
    fld.append(r)
    par._p.append(fld)


r = fp.add_run("第 ")
set_run(r, "宋体", 9)
add_field_run(fp, " PAGE ", "1")
r = fp.add_run(" 页  共 ")
set_run(r, "宋体", 9)
add_field_run(fp, " NUMPAGES ", "1")
r = fp.add_run(" 页")
set_run(r, "宋体", 9)

# Word 2013+ compatibility so the SVG picture survives a Word save
try:
    for cs in doc.settings.element.iter(qn("w:compatSetting")):
        if cs.get(qn("w:name")) == "compatibilityMode":
            cs.set(qn("w:val"), "15")
except Exception as exc:
    print("compat mode update skipped:", exc)

doc.save(DST)
print("saved", DST)


# ---------------------------------------------------------------- embed SVG alongside the PNG fallback
def embed_svg(docx_path, svg_path):
    """Add the vector SVG as the primary image with the inserted PNG as fallback."""
    import zipfile, shutil, os, re
    tmp = docx_path + ".tmp"
    with zipfile.ZipFile(docx_path) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    rels = data["word/_rels/document.xml.rels"].decode("utf-8")
    docxml = data["word/document.xml"].decode("utf-8")
    ctypes = data["[Content_Types].xml"].decode("utf-8")

    # find the image relationship used by the picture (the PNG fallback)
    m = re.search(r'<Relationship Id="(rId\d+)" Type="[^"]*/image" Target="(media/[^"]+\.png)"', rels)
    if not m:
        print("no image relationship found, skip svg embed")
        return
    png_rid, png_target = m.group(1), m.group(2)

    svg_name = "media/er_diagram.svg"
    svg_rid = "rIdSvg1"
    if 'Id="%s"' % svg_rid in rels:
        svg_rid = "rIdSvg2"

    rels = rels.replace(
        "</Relationships>",
        '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="%s"/></Relationships>'
        % (svg_rid, svg_name))

    blip = '<a:blip r:embed="%s"/>' % png_rid
    if blip not in docxml:
        print("blip not found, skip svg embed")
        return
    docxml = docxml.replace(
        blip,
        '<a:blip r:embed="%s"><a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
        '<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="%s"/>'
        '</a:ext></a:extLst></a:blip>' % (png_rid, svg_rid), 1)

    if 'Extension="svg"' not in ctypes:
        ctypes = ctypes.replace("</Types>", '<Default Extension="svg" ContentType="image/svg+xml"/></Types>')

    data["word/_rels/document.xml.rels"] = rels.encode("utf-8")
    data["word/document.xml"] = docxml.encode("utf-8")
    data["[Content_Types].xml"] = ctypes.encode("utf-8")
    data["word/" + svg_name] = open(svg_path, "rb").read()

    order = [n for n in names if n in data] + ["word/" + svg_name]
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in order:
            zout.writestr(n, data[n])
    shutil.move(tmp, docx_path)
    print("svg embedded", svg_name, "as", svg_rid)


embed_svg(DST, r"C:\Users\123456\Desktop\Pro\work\er.svg")









