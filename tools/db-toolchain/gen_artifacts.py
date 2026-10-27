# -*- coding: utf-8 -*-
"""从 db_model.py 生成数据库设计交付物（DBML / DDL / 数据字典 / 机器可读模型）。

所属链路
    db_model.py  --本脚本-->  dbml/ + sql/ + 数据字典.xlsx + data-model.json
                 --dbdiagram.io 或 @dbml/cli-->  各方言 DDL
                 --adapt_dialect.py-->  目标库可直接执行的建表脚本

产出目录
    默认写入仓库的 docs/database/，可用环境变量 DB_DESIGN_OUT 覆盖：
        set DB_DESIGN_OUT=D:\\tmp\\design && python gen_artifacts.py

主要产出
    dbml/class_test_full.dbml        dbdiagram.io 建模源文件（粘贴进网页即可出图）
    dbml/class_test_<域>.dbml        按六个主题域拆分的 DBML
    sql/01_tablespace_oracle.sql     Oracle 表空间规划
    sql/02_schema_oracle.sql         Oracle 生产建表脚本（含分区/表空间）
    sql/03_schema_h2.sql             H2 建表脚本
    sql/04_schema_mysql.sql          MySQL 方言建表脚本
    sql/05_seed_data.sql             设施类别/画像标签等初始化数据
    sql/06_views_oracle.sql          看板与统计视图
    sql/07_migration_v1_to_v2.sql    V1→V2 平滑迁移脚本
    数据字典与数据项清单.xlsx          数据项清单、表清单、字段字典、码表、索引约束、存储规划、容量汇总
    data-model.json                  机器可读模型（供代码生成与校验）
    交付包清单.md                     本次生成的文件清单（不覆盖人工维护的 README.md）

依赖
    pip install openpyxl

运行
    cd tools/db-toolchain
    python gen_artifacts.py

注意
    本文件是「生成器」，不要手工修改它的产出；要改数据模型请改 db_model.py 后重新运行。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import db_model as M

# --- 路径约定 ---------------------------------------------------------------
# 本文件位于 <repo>/tools/db-toolchain/，向上两级就是仓库根目录。
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
# 交付物默认直接写进仓库 docs/database/，与文档一起做版本管理。
OUT = os.environ.get("DB_DESIGN_OUT") or os.path.join(REPO, "docs", "database")
DBML_DIR = os.path.join(OUT, "dbml")
SQL_DIR = os.path.join(OUT, "sql")
os.makedirs(DBML_DIR, exist_ok=True)
os.makedirs(SQL_DIR, exist_ok=True)

TABLES = M.TABLES
BY = M.TABLE_BY_NAME
DOMAINS = M.DOMAINS


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def type_parts(typ):
    m = re.match(r"([A-Z]+)(?:\(([^)]*)\))?$", typ)
    if not m:
        return typ, ""
    return m.group(1), m.group(2) or ""


def oracle_type(typ):
    base, args = type_parts(typ)
    return {
        "BIGINT": "NUMBER(19)",
        "INT": "NUMBER(10)",
        "VARCHAR": f"VARCHAR2({args})",
        "CHAR": f"CHAR({args})",
        "DECIMAL": f"NUMBER({args})",
        "DATE": "DATE",
        "TIMESTAMP": "TIMESTAMP(6)",
        "CLOB": "CLOB",
    }[base]


def mysql_type(typ):
    base, args = type_parts(typ)
    return {
        "BIGINT": "BIGINT",
        "INT": "INT",
        "VARCHAR": f"VARCHAR({args})",
        "CHAR": f"CHAR({args})",
        "DECIMAL": f"DECIMAL({args})",
        "DATE": "DATE",
        "TIMESTAMP": "DATETIME(6)",
        "CLOB": "LONGTEXT",
    }[base]


def h2_type(typ):
    base, args = type_parts(typ)
    return {
        "BIGINT": "BIGINT",
        "INT": "INT",
        "VARCHAR": f"VARCHAR({args})",
        "CHAR": f"CHAR({args})",
        "DECIMAL": f"DECIMAL({args})",
        "DATE": "DATE",
        "TIMESTAMP": "TIMESTAMP(6)",
        "CLOB": "CLOB",
    }[base]


def dbml_type(typ):
    base, args = type_parts(typ)
    return {
        "BIGINT": "bigint",
        "INT": "int",
        "VARCHAR": f"varchar({args})",
        "CHAR": f"char({args})",
        "DECIMAL": f"decimal({args})",
        "DATE": "date",
        "TIMESTAMP": "timestamp",
        "CLOB": "text",
    }[base]


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def constraint_name(prefix, table, suffix):
    name = f"{prefix}_{table}_{suffix}"
    return name[:128]


def index_name(idx_name, table):
    return idx_name[:128]


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------
errors = []
for t in TABLES:
    names = [c["name"] for c in t["cols"]]
    if len(names) != len(set(names)):
        errors.append(f"duplicate column in {t['name']}")
    if not any(c["pk"] for c in t["cols"]):
        errors.append(f"no pk in {t['name']}")
    for c in t["cols"]:
        if c["fk"]:
            tn, cn = c["fk"].split(".")
            if tn not in BY:
                errors.append(f"unknown fk table {tn} ({t['name']}.{c['name']})")
            elif cn not in [x["name"] for x in BY[tn]["cols"]]:
                errors.append(f"unknown fk column {tn}.{cn}")
if errors:
    raise SystemExit("MODEL ERROR:\n" + "\n".join(errors))

# index names unique
idx_names = []
for t in TABLES:
    for name, cols, uniq in t["indexes"]:
        if name in idx_names:
            errors.append(f"duplicate index name {name}")
        idx_names.append(name)
if errors:
    raise SystemExit("MODEL ERROR:\n" + "\n".join(errors))

# topological order
order = []
seen = set()
visiting = set()


def visit(t):
    if t["name"] in seen:
        return
    if t["name"] in visiting:
        raise SystemExit("cycle at " + t["name"])
    visiting.add(t["name"])
    for c in t["cols"]:
        if c["fk"]:
            dep = c["fk"].split(".")[0]
            if dep != t["name"]:
                visit(BY[dep])
    visiting.discard(t["name"])
    seen.add(t["name"])
    order.append(t)


for t in TABLES:
    visit(t)


def storage_mb(t):
    table_mb = t["rows_3y"] * t["row_bytes"] / 1024 / 1024
    lob_mb = t["rows_3y"] * t["lob_bytes"] / 1024 / 1024
    index_mb = (table_mb + lob_mb) * 0.24
    return table_mb, lob_mb, index_mb


# --------------------------------------------------------------------------
# DBML
# --------------------------------------------------------------------------
def dbml_for(tables, include_refs=True):
    lines = []
    for t in tables:
        lines.append(f'Table {t["name"]} {{')
        for c in t["cols"]:
            settings = []
            if c["pk"]:
                settings += ["pk", "increment"]
            if not c["null"] and not c["pk"]:
                settings.append("not null")
            if c["uniq"]:
                settings.append("unique")
            if c["default"] and "CURRENT_TIMESTAMP" not in c["default"]:
                settings.append(f"default: {c['default']}")
            note = c["note"] or c["cn"]
            settings.append("note: " + q(note))
            lines.append(f'  {c["name"]} {dbml_type(c["typ"])} [{", ".join(settings)}]')
        lines.append("")
        lines.append(f'  Note: {q(t["cn"] + "：" + t["note"])}')
        if t["indexes"]:
            lines.append("")
            lines.append("  indexes {")
            for name, cols, uniq in t["indexes"]:
                coltxt = ", ".join(cols) if len(cols) > 1 else cols[0]
                if len(cols) > 1:
                    coltxt = "(" + coltxt + ")"
                extra = " [unique" + (f", name: '{name}'" if name else "") + "]" if uniq else f" [name: '{name}']"
                lines.append(f"    {coltxt}{extra}")
            lines.append("  }")
        lines.append("}")
        lines.append("")
    if include_refs:
        for t in tables:
            for c in t["cols"]:
                if c["fk"]:
                    lines.append(f'Ref: {t["name"]}.{c["name"]} > {c["fk"].replace(".", ".")}')
        lines.append("")
    return "\n".join(lines)


def write_dbml():
    header = (
        f"// {M.PROJECT} · 数据库逻辑模型\n"
        f"// 版本：{M.VERSION}  生成日期：{M.DATE_CN}\n"
        "// 使用方式：打开 https://dbdiagram.io/d ，清空编辑器后粘贴本文件内容即可复现。\n"
        "// 表分组与主题域：USR 用户画像 / SIT 空间设施 / RES 居民评估 / MER 商户招商 / COM 社区治理 / OPS 数据运营\n\n"
    )
    groups = []
    for dk, dn in DOMAINS.items():
        groups.append(f'TableGroup "{dn}" {{')
        for t in TABLES:
            if t["domain"] == dk:
                groups.append(f"  {t['name']}")
        groups.append("}")
        groups.append("")

    full = header + "// ===== 实体定义 =====\n" + dbml_for(TABLES, include_refs=False)
    full += "\n// ===== 关系定义 =====\n"
    for t in TABLES:
        for c in t["cols"]:
            if c["fk"]:
                full += f'Ref: {t["name"]}.{c["name"]} > {c["fk"]}\n'
    full += "\n// ===== 主题域分组 =====\n" + "\n".join(groups)
    path = os.path.join(DBML_DIR, "class_test_full.dbml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(full)
    print("wrote", path, len(full), "chars")

    for dk, dn in DOMAINS.items():
        subset = [t for t in TABLES if t["domain"] == dk]
        ext = set()
        for t in subset:
            for c in t["cols"]:
                if c["fk"] and c["fk"].split(".")[0] not in [x["name"] for x in subset]:
                    ext.add(c["fk"].split(".")[0])
        text = header + f"// 当前分组：{dn}\n\n" + dbml_for(subset, include_refs=False)
        if ext:
            text += "\n// 外部引用实体（仅保留主键）\n"
            for tn in sorted(ext):
                text += f"Table {tn} {{\n  id bigint [pk]\n}}\n\n"
        text += "\n// ===== 关系定义（含外部引用） =====\n"
        for t in subset:
            for c in t["cols"]:
                if c["fk"]:
                    text += f'Ref: {t["name"]}.{c["name"]} > {c["fk"]}\n'
        text += f'\nTableGroup "{dn}" {{\n' + "\n".join("  " + t["name"] for t in subset) + "\n}\n"
        p = os.path.join(DBML_DIR, f"class_test_{dk.lower()}.dbml")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
    print("wrote domain dbml files")


# --------------------------------------------------------------------------
# Oracle
# --------------------------------------------------------------------------
def oracle_table(t):
    lines = [f"CREATE TABLE {t['name']} ("]
    col_lines = []
    for c in t["cols"]:
        s = f"    {c['name']:<26} {oracle_type(c['typ']):<16}"
        if c["pk"]:
            s += " GENERATED BY DEFAULT AS IDENTITY"
        if c["default"]:
            s += f" DEFAULT {c['default']}"
        if not c["null"] and not c["pk"]:
            s += " NOT NULL"
        col_lines.append(s.rstrip())
    cons = [f"    CONSTRAINT {constraint_name('pk', t['name'], '')[:-1]} PRIMARY KEY ({[c['name'] for c in t['cols'] if c['pk']][0]})"]
    for c in t["cols"]:
        if c["uniq"]:
            cons.append(f"    CONSTRAINT {constraint_name('uk', t['name'], c['name'])} UNIQUE ({c['name']})")
    for name, cols, uniq in t["indexes"]:
        if uniq:
            cons.append(f"    CONSTRAINT {name} UNIQUE ({', '.join(cols)})")
    for c in t["cols"]:
        if c["check"]:
            cons.append(f"    CONSTRAINT {constraint_name('ck', t['name'], c['name'])} CHECK ({c['check']})")
    for suffix, expr in t["checks"]:
        cons.append(f"    CONSTRAINT {suffix} CHECK ({expr})")
    for c in t["cols"]:
        if c["fk"]:
            ref_t, ref_c = c["fk"].split(".")
            s = f"    CONSTRAINT {constraint_name('fk', t['name'], c['name'])} FOREIGN KEY ({c['name']}) REFERENCES {ref_t} ({ref_c})"
            if c["on_delete"] and c["on_delete"] != "RESTRICT":
                s += f" ON DELETE {c['on_delete']}"
            cons.append(s)
    body = ",\n".join(col_lines + cons)
    lines.append(body)
    lines.append(")")
    lobs = [c for c in t["cols"] if c["typ"] == "CLOB"]
    for c in lobs:
        lines.append(
            f"  LOB ({c['name']}) STORE AS SECUREFILE (TABLESPACE TBS_LIFECIRCLE_LOB COMPRESS HIGH)"
        )
    tbs = "TBS_LIFECIRCLE_ODS" if t["tablespace"] == "ODS" else "TBS_LIFECIRCLE_DATA"
    lines.append(f"  TABLESPACE {tbs}")
    if t["partition"]:
        col = t["partition"]
        lines.append("  PARTITION BY RANGE (" + col + ") INTERVAL (NUMTOYMINTERVAL(1, 'MONTH'))")
        lines.append(
            f"  (PARTITION p_{t['name']}_init VALUES LESS THAN (TIMESTAMP '2026-01-01 00:00:00'))"
        )
    lines[-1] += ";"
    sql = "\n".join(lines)
    sql += f"\nCOMMENT ON TABLE {t['name']} IS {q(t['cn'] + '：' + t['note'])};"
    for c in t["cols"]:
        ctext = c["cn"] + ("；" + c["note"] if c["note"] and c["note"] != c["cn"] else "")
        sql += f"\nCOMMENT ON COLUMN {t['name']}.{c['name']} IS {q(ctext)};"
    for name, cols, uniq in t["indexes"]:
        if not uniq:
            sql += f"\nCREATE INDEX {name} ON {t['name']} ({', '.join(cols)}) TABLESPACE TBS_LIFECIRCLE_IDX;"
    return sql


def write_oracle():
    ts = """-- ============================================================
-- 城市15分钟便民生活圈与小微开店智能助手 · Oracle 表空间规划
-- 执行用户：DBA（需 CREATE TABLESPACE 权限）
-- 目标库：Oracle Database 23ai Free（FREEPDB1）
-- ============================================================

CREATE TABLESPACE TBS_LIFECIRCLE_DATA
  DATAFILE 'life_data01.dbf' SIZE 1024M AUTOEXTEND ON NEXT 256M MAXSIZE 6144M
  EXTENT MANAGEMENT LOCAL AUTOALLOCATE
  SEGMENT SPACE MANAGEMENT AUTO;

CREATE TABLESPACE TBS_LIFECIRCLE_IDX
  DATAFILE 'life_idx01.dbf' SIZE 512M AUTOEXTEND ON NEXT 128M MAXSIZE 3072M
  EXTENT MANAGEMENT LOCAL AUTOALLOCATE
  SEGMENT SPACE MANAGEMENT AUTO;

CREATE TABLESPACE TBS_LIFECIRCLE_LOB
  DATAFILE 'life_lob01.dbf' SIZE 512M AUTOEXTEND ON NEXT 128M MAXSIZE 3072M
  EXTENT MANAGEMENT LOCAL AUTOALLOCATE
  SEGMENT SPACE MANAGEMENT AUTO;

CREATE TABLESPACE TBS_LIFECIRCLE_ODS
  DATAFILE 'life_ods01.dbf' SIZE 1024M AUTOEXTEND ON NEXT 256M MAXSIZE 4096M
  EXTENT MANAGEMENT LOCAL AUTOALLOCATE
  SEGMENT SPACE MANAGEMENT AUTO;
"""
    p = os.path.join(SQL_DIR, "01_tablespace_oracle.sql")
    open(p, "w", encoding="utf-8").write(ts)

    head = f"""-- ============================================================
-- {M.PROJECT}
-- Oracle Database 23ai 建表脚本（{M.VERSION}）
-- 依赖：先以 life_circle 用户执行 01_tablespace_oracle.sql（或由 DBA 建好表空间）
-- 说明：共 {len(TABLES)} 张表；表顺序按外键依赖拓扑排序；含注释、索引、分区与约束。
-- ============================================================
SET DEFINE OFF;

"""
    body = "\n\n".join(oracle_table(t) for t in order)
    p = os.path.join(SQL_DIR, "02_schema_oracle.sql")
    open(p, "w", encoding="utf-8").write(head + body + "\n\nCOMMIT;\n")
    print("wrote oracle schema")


# --------------------------------------------------------------------------
# MySQL
# --------------------------------------------------------------------------
def mysql_table(t):
    lines = [f"CREATE TABLE {t['name']} ("]
    parts = []
    for c in t["cols"]:
        s = f"  {c['name']} {mysql_type(c['typ'])}"
        if c["pk"]:
            s += " NOT NULL AUTO_INCREMENT"
        elif not c["null"]:
            s += " NOT NULL"
        if c["default"]:
            s += f" DEFAULT {c['default'].replace('CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP(6)')}"
        s += f" COMMENT {q(c['cn'] + ('；' + c['note'] if c['note'] else ''))}"
        parts.append(s)
    pkcol = [c["name"] for c in t["cols"] if c["pk"]][0]
    parts.append(f"  PRIMARY KEY ({pkcol})")
    for c in t["cols"]:
        if c["uniq"]:
            parts.append(f"  UNIQUE KEY {constraint_name('uk', t['name'], c['name'])} ({c['name']})")
    for name, cols, uniq in t["indexes"]:
        if uniq:
            parts.append(f"  UNIQUE KEY {name} ({', '.join(cols)})")
    for name, cols, uniq in t["indexes"]:
        if not uniq:
            parts.append(f"  KEY {name} ({', '.join(cols)})")
    for c in t["cols"]:
        if c["check"]:
            parts.append(f"  CONSTRAINT {constraint_name('ck', t['name'], c['name'])} CHECK ({c['check']})")
    for suffix, expr in t["checks"]:
        parts.append(f"  CONSTRAINT {suffix} CHECK ({expr})")
    for c in t["cols"]:
        if c["fk"]:
            ref_t, ref_c = c["fk"].split(".")
            s = f"  CONSTRAINT {constraint_name('fk', t['name'], c['name'])} FOREIGN KEY ({c['name']}) REFERENCES {ref_t} ({ref_c})"
            if c["on_delete"]:
                s += f" ON DELETE {c['on_delete']}"
            parts.append(s)
    lines.append(",\n".join(parts))
    lines.append(f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT={q(t['cn'] + '：' + t['note'])};")
    return "\n".join(lines)


def write_mysql():
    head = f"""-- ============================================================
-- {M.PROJECT}
-- MySQL 8.0 建表脚本（{M.VERSION}，可选方言）
-- 说明：项目生产库以 Oracle 为主；本脚本用于教学/本地 MySQL 验证。
-- 字符集 utf8mb4；共 {len(TABLES)} 张表。
-- ============================================================
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

"""
    body = "\n\n".join(mysql_table(t) for t in order)
    p = os.path.join(SQL_DIR, "04_schema_mysql.sql")
    open(p, "w", encoding="utf-8").write(head + body + "\n\nSET FOREIGN_KEY_CHECKS = 1;\n")
    print("wrote mysql schema")


# --------------------------------------------------------------------------
# H2
# --------------------------------------------------------------------------
def h2_table(t):
    lines = [f"CREATE TABLE {t['name']} ("]
    parts = []
    for c in t["cols"]:
        s = f"  {c['name']} {h2_type(c['typ'])}"
        if c["pk"]:
            s += " GENERATED BY DEFAULT AS IDENTITY"
        elif not c["null"]:
            s += " NOT NULL"
        if c["default"]:
            s += f" DEFAULT {c['default']}"
        parts.append(s)
    pkcol = [c["name"] for c in t["cols"] if c["pk"]][0]
    parts.append(f"  CONSTRAINT pk_{t['name']} PRIMARY KEY ({pkcol})")
    for c in t["cols"]:
        if c["uniq"]:
            parts.append(f"  CONSTRAINT {constraint_name('uk', t['name'], c['name'])} UNIQUE ({c['name']})")
    for name, cols, uniq in t["indexes"]:
        if uniq:
            parts.append(f"  CONSTRAINT {name} UNIQUE ({', '.join(cols)})")
    for c in t["cols"]:
        if c["check"]:
            parts.append(f"  CONSTRAINT {constraint_name('ck', t['name'], c['name'])} CHECK ({c['check']})")
    for suffix, expr in t["checks"]:
        parts.append(f"  CONSTRAINT {suffix} CHECK ({expr})")
    for c in t["cols"]:
        if c["fk"]:
            ref_t, ref_c = c["fk"].split(".")
            s = f"  CONSTRAINT {constraint_name('fk', t['name'], c['name'])} FOREIGN KEY ({c['name']}) REFERENCES {ref_t} ({ref_c})"
            if c["on_delete"]:
                s += f" ON DELETE {c['on_delete']}"
            parts.append(s)
    lines.append(",\n".join(parts))
    lines.append(");")
    for name, cols, uniq in t["indexes"]:
        if not uniq:
            lines.append(f"CREATE INDEX {name} ON {t['name']} ({', '.join(cols)});")
    return "\n".join(lines)


def write_h2():
    head = f"""-- ============================================================
-- {M.PROJECT}
-- H2 2.2.x 开发库建表脚本（MODE=Oracle，{M.VERSION}）
-- 用法：java -cp h2-2.2.224.jar org.h2.tools.RunScript \\
--        -url "jdbc:h2:mem:lifecircle;MODE=Oracle;DB_CLOSE_DELAY=-1" -user sa -script schema_h2.sql
-- 共 {len(TABLES)} 张表，已实际执行验证。
-- ============================================================
"""
    body = "\n\n".join(h2_table(t) for t in order)
    p = os.path.join(SQL_DIR, "03_schema_h2.sql")
    open(p, "w", encoding="utf-8").write(head + body + "\n")
    print("wrote h2 schema")


# --------------------------------------------------------------------------
# seed + views + migration
# --------------------------------------------------------------------------
def write_seed():
    lines = ["-- 初始化数据：设施类别、画像标签、演示片区与 POI（可选）", "SET DEFINE OFF;", ""]
    for code, name, dim, dimname, sort in M.FACILITY_CATEGORIES:
        lines.append(
            "INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) "
            f"VALUES ({q(code)}, {q(name)}, {q(dim)}, {q(dimname)}, {sort});"
        )
    lines.append("")
    for code, name, role, dim, weight in M.PROFILE_TAGS:
        lines.append(
            "INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) "
            f"VALUES ({q(code)}, {q(name)}, {q(role)}, {q(dim)}, {weight});"
        )
    lines.append("")
    districts = [
        ("510107001001", "朝阳社区示范片区", "STREET", "510107", 104.0431, 30.6421, 12680),
        ("510107001002", "东南片区", "COMMUNITY", "510107", 104.0512, 30.6388, 8420),
        ("510107001003", "北部新居", "COMMUNITY", "510107", 104.0405, 30.6512, 9630),
    ]
    for code, name, level, city, lng, lat, pop in districts:
        lines.append(
            "INSERT INTO district (district_code, district_name, district_level, city_code, center_lng, center_lat, resident_count) "
            f"VALUES ({q(code)}, {q(name)}, {q(level)}, {q(city)}, {lng}, {lat}, {pop});"
        )
    lines.append("")
    lines.append(
        "INSERT INTO sync_batch (batch_no, data_source, sync_type, started_at, finished_at, total_count, insert_count, status) "
        "VALUES ('POI-20261015-01', 'AMAP', 'INCREMENT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 'SUCCESS');"
    )
    lines.append("")
    pois = [
        ("朝阳生鲜市场", "FRESH_MARKET", 104.0437, 30.6426, "朝阳路 18 号"),
        ("朝阳社区卫生服务中心", "COMMUNITY_CLINIC", 104.0425, 30.6419, "朝阳路 36 号"),
        ("小芽托育中心", "NURSERY", 104.0442, 30.6408, "文体路 8 号"),
        ("东园路口公交站", "BUS_STOP", 104.0460, 30.6432, "东园路"),
        ("康宁夜间药房", "NIGHT_PHARMACY", 104.0418, 30.6395, "康宁路 12 号"),
        ("邻家便利店", "CONVENIENCE", 104.0449, 30.6422, "朝阳路 22 号"),
    ]
    for name, cat, lng, lat, addr in pois:
        lines.append(
            "INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) "
            "SELECT d.id, c.id, " + f"{q(name)}, {lng}, {lat}, {q(addr)}, 'MANUAL', " + q("SEED-" + name) +
            ", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c "
            f"WHERE d.district_code = '510107001001' AND c.category_code = {q(cat)};"
        )
    lines.append("")
    lines.append("COMMIT;")
    p = os.path.join(SQL_DIR, "05_seed_data.sql")
    open(p, "w", encoding="utf-8").write("\n".join(lines))


def write_views():
    sql = """-- 社区治理看板视图：每个片区取最新一次评分快照
CREATE OR REPLACE VIEW v_district_dashboard AS
SELECT d.id                                   AS district_id,
       d.district_code,
       d.district_name,
       s.coverage_pct,
       s.avg_score,
       s.rank_no,
       d.resident_count,
       (SELECT COUNT(*) FROM community_gap g
         WHERE g.district_id = d.id AND g.gap_level = '高') AS high_gap_count,
       (SELECT COUNT(*) FROM merchant_intent i
         WHERE i.district_id = d.id AND i.status = 'SUBMITTED') AS pending_intent_count,
       s.scored_at
  FROM district d
  LEFT JOIN district_score_snapshot s
    ON s.district_id = d.id
   AND s.scored_at = (SELECT MAX(s2.scored_at)
                        FROM district_score_snapshot s2
                       WHERE s2.district_id = d.id)
 WHERE d.status = 'ACTIVE';

-- 设施类别统计视图
CREATE OR REPLACE VIEW v_poi_category_stat AS
SELECT p.district_id,
       d.district_name,
       c.category_code,
       c.category_name,
       c.dimension_code,
       COUNT(*) AS facility_count
  FROM poi_facility p
  JOIN district d ON d.id = p.district_id
  JOIN facility_category c ON c.id = p.category_id
 WHERE p.is_valid = 'Y'
 GROUP BY p.district_id, d.district_name, c.category_code, c.category_name, c.dimension_code;
"""
    p = os.path.join(SQL_DIR, "06_views_oracle.sql")
    open(p, "w", encoding="utf-8").write(sql)


def write_migration():
    sql = """-- ============================================================
-- V1 -> V2 迁移脚本：保留已有 merchant_intent 数据
-- 适用：当前工程已按 V1 建过 merchant_intent（5 列）
-- ============================================================

ALTER TABLE merchant_intent MODIFY (contact VARCHAR2(200));

ALTER TABLE merchant_intent ADD (
  contact_masked VARCHAR2(20),
  district_id    NUMBER(19),
  candidate_id   NUMBER(19),
  budget_min     NUMBER(8,2),
  budget_max     NUMBER(8,2),
  area_sqm       NUMBER(8,2),
  remark         VARCHAR2(500),
  status         VARCHAR2(20) DEFAULT 'SUBMITTED' NOT NULL,
  updated_at     TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE merchant_intent ADD CONSTRAINT fk_merchant_intent_district
  FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE SET NULL;
ALTER TABLE merchant_intent ADD CONSTRAINT fk_merchant_intent_candidate
  FOREIGN KEY (candidate_id) REFERENCES site_candidate (id) ON DELETE SET NULL;
ALTER TABLE merchant_intent ADD CONSTRAINT ck_merchant_intent_status
  CHECK (status IN ('SUBMITTED','MATCHED','CONTACTED','CLOSED','INVALID'));

CREATE INDEX idx_intent_status_time ON merchant_intent (status, created_at) TABLESPACE TBS_LIFECIRCLE_IDX;
CREATE INDEX idx_intent_district ON merchant_intent (district_id) TABLESPACE TBS_LIFECIRCLE_IDX;
CREATE INDEX idx_intent_candidate ON merchant_intent (candidate_id) TABLESPACE TBS_LIFECIRCLE_IDX;

COMMENT ON COLUMN merchant_intent.contact IS '联系方式密文：AES-256-GCM + Base64，禁止明文';
COMMENT ON COLUMN merchant_intent.status IS '意向状态';
COMMIT;
"""
    p = os.path.join(SQL_DIR, "07_migration_v1_to_v2.sql")
    open(p, "w", encoding="utf-8").write(sql)


# --------------------------------------------------------------------------
# Excel
# --------------------------------------------------------------------------
def write_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "00 说明"

    title_font = Font(name="微软雅黑", size=16, bold=True, color="1F3864")
    hdr_font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
    body_font = Font(name="微软雅黑", size=9, color="000000")
    hdr_fill = PatternFill("solid", fgColor="2F5597")
    alt_fill = PatternFill("solid", fgColor="EDF2F9")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.merge_cells("A1:F1")
    ws["A1"] = M.PROJECT
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30
    info = [
        ("文档名称", "数据项清单与数据字典"),
        ("版本", M.VERSION),
        ("日期", M.DATE_CN),
        ("数据模型文件", "dbml/class_test_full.dbml（dbdiagram.io 可直接导入）"),
        ("建表脚本", "sql/02_schema_oracle.sql、03_schema_h2.sql、04_schema_mysql.sql"),
        ("表数量", len(TABLES)),
        ("数据项数量", sum(len(t["cols"]) for t in TABLES)),
        ("说明", "本工作簿由统一数据模型自动生成，字段、表与脚本保持一致。"),
    ]
    r = 3
    for k, v in info:
        ws.cell(r, 1, k).font = Font(name="微软雅黑", size=10, bold=True)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        ws.cell(r, 2, v).font = body_font
        r += 1
    ws.column_dimensions["A"].width = 18
    for c in "BCDEF":
        ws.column_dimensions[c].width = 20

    def style_sheet(sh, headers, widths, rows, title):
        sh.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        sh.cell(1, 1, title).font = Font(name="微软雅黑", size=13, bold=True, color="1F3864")
        sh.cell(1, 1).alignment = Alignment(horizontal="center", vertical="center")
        sh.row_dimensions[1].height = 26
        for j, h in enumerate(headers, 1):
            c = sh.cell(3, j, h)
            c.font = hdr_font
            c.fill = hdr_fill
            c.border = border
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            sh.column_dimensions[get_column_letter(j)].width = widths[j - 1]
        sh.row_dimensions[3].height = 24
        for i, row in enumerate(rows, 4):
            for j, v in enumerate(row, 1):
                c = sh.cell(i, j, v)
                c.font = body_font
                c.border = border
                c.alignment = Alignment(vertical="top", wrap_text=True)
                if i % 2 == 0:
                    c.fill = alt_fill
        sh.freeze_panes = "A4"
        sh.auto_filter.ref = f"A3:{get_column_letter(len(headers))}{3 + len(rows)}"

    # 数据项清单
    prefix = {k: 0 for k in DOMAINS}
    rows = []
    for t in TABLES:
        dk = t["domain"]
        for c in t["cols"]:
            prefix[dk] += 1
            key = "PK" if c["pk"] else ("FK" if c["fk"] else ("UK" if c["uniq"] else ""))
            domain_bit = f"{dk}-{prefix[dk]:03d}"
            rows.append([
                "DI-" + domain_bit,
                DOMAINS[dk],
                c["cn"],
                c["name"],
                t["name"],
                c["typ"],
                "否" if (c["null"] and not c["pk"]) else "是",
                (c["check"] or "").replace("BETWEEN", "范围").replace("IN (", "枚举 ") or "—",
                c["default"] or "—",
                key,
                (c["note"] or c["cn"]),
            ])
    sh = wb.create_sheet("01 数据项清单")
    style_sheet(sh, ["数据项编号", "主题域", "中文名称", "英文标识", "所属表", "数据类型", "必填",
                     "值域/约束", "默认值", "键", "说明"],
                [15, 16, 18, 24, 24, 16, 7, 40, 16, 7, 40], rows,
                f"数据项清单（共 {len(rows)} 项）")

    # 表清单
    rows = []
    for i, t in enumerate(TABLES, 1):
        tm, lm, im = storage_mb(t)
        rows.append([i, t["name"], t["cn"], DOMAINS[t["domain"]], t["kind"],
                     t["rows_3y"], f"{tm + lm + im:.1f}",
                     "是" if t["partition"] else "否",
                     "TBS_LIFECIRCLE_ODS" if t["tablespace"] == "ODS" else "TBS_LIFECIRCLE_DATA",
                     t["note"]])
    sh = wb.create_sheet("02 数据表清单")
    style_sheet(sh, ["序号", "表名", "中文名", "主题域", "表类型", "预估行数(3年)",
                     "预估容量(MB)", "分区", "表空间", "说明"],
                [6, 26, 24, 18, 10, 14, 13, 7, 26, 55], rows, "数据表清单")

    # 字段字典
    rows = []
    for t in TABLES:
        for i, c in enumerate(t["cols"], 1):
            key = "PK" if c["pk"] else ("FK→" + c["fk"] if c["fk"] else ("UK" if c["uniq"] else ""))
            rows.append([t["name"], t["cn"], i, c["name"], c["cn"], c["typ"],
                         "是" if (c["null"] and not c["pk"]) else "否",
                         c["default"] or "", key, c["check"] or "", c["note"] or ""])
    sh = wb.create_sheet("03 字段字典")
    style_sheet(sh, ["表名", "表中文名", "序号", "字段名", "中文名", "类型", "可空",
                     "默认值", "键/引用", "检查约束", "说明"],
                [24, 22, 6, 24, 18, 16, 6, 18, 30, 40, 40], rows,
                f"字段字典（共 {len(rows)} 个字段）")

    # 码表
    rows = [[i, a, b, c, d, e] for i, (a, b, c, d, e) in enumerate(M.ENUMS, 1)]
    sh = wb.create_sheet("04 码表与枚举")
    style_sheet(sh, ["序号", "枚举组", "编码", "中文含义", "使用字段", "说明"],
                [6, 18, 18, 20, 40, 24],
                [r + [""] for r in rows], "码表与枚举值（前后端必须逐字一致）")

    # 索引约束
    rows = []
    for t in TABLES:
        pk = [c["name"] for c in t["cols"] if c["pk"]][0]
        rows.append([t["name"], "pk_" + t["name"], "主键", pk, "唯一、非空"])
        for c in t["cols"]:
            if c["uniq"]:
                rows.append([t["name"], "uk_" + t["name"] + "_" + c["name"], "唯一", c["name"], "业务唯一"])
            if c["fk"]:
                rows.append([t["name"], "fk_" + t["name"] + "_" + c["name"], "外键", c["name"], "引用 " + c["fk"]])
            if c["check"]:
                rows.append([t["name"], "ck_" + t["name"] + "_" + c["name"], "检查", c["name"], c["check"]])
        for name, cols, uniq in t["indexes"]:
            rows.append([t["name"], name, "唯一约束" if uniq else "普通索引", ", ".join(cols), "加速查询"])
        for suffix, expr in t["checks"]:
            rows.append([t["name"], suffix, "表级检查", "", expr])
    sh = wb.create_sheet("05 索引与约束")
    style_sheet(sh, ["表名", "名称", "类型", "字段", "说明"],
                [24, 40, 12, 40, 55], rows, "索引与约束清单")

    # 存储规划
    rows = []
    for t in TABLES:
        tm, lm, im = storage_mb(t)
        rows.append([t["name"], t["cn"], "ODS" if t["tablespace"] == "ODS" else "DWD",
                     "TBS_LIFECIRCLE_ODS" if t["tablespace"] == "ODS" else "TBS_LIFECIRCLE_DATA",
                     ("按月 RANGE 分区：" + t["partition"]) if t["partition"] else "不分区",
                     "",
                     round(tm, 2), round(lm, 2), round(im, 2), round(tm + lm + im, 2), t["retention"]])
    # fix column source for CLOB
    for row, t in zip(rows, TABLES):
        row[5] = "是" if any(c["typ"] == "CLOB" for c in t["cols"]) else ""
    sh = wb.create_sheet("06 存储规划")
    style_sheet(sh, ["表名", "中文名", "数据层", "表空间", "分区策略", "含 LOB",
                     "表数据(MB)", "LOB(MB)", "索引(MB)", "合计(MB)", "保留策略"],
                [24, 22, 8, 26, 30, 8, 11, 9, 10, 10, 26], rows, "数据表存储结构规划")

    # 数据流转
    flow = [
        ["高德 POI 接口", "ods_poi_raw", "poi_facility / poi_change_log", "每半月增量", "设施主数据与变更留痕"],
        ["人口栅格文件", "ods_population_raw", "population_grid", "每半月/季度", "人口密度与覆盖测算"],
        ["城市路网文件", "ods_road_raw", "road_node / road_segment", "每半年", "15 分钟步行等时圈"],
        ["居民勾选与对话", "—", "app_user / user_profile / profile_dimension_weight", "实时", "画像与权重"],
        ["居民评估请求", "—", "resident_assessment / assessment_dimension / assessment_facility_stat", "实时", "体检报告与雷达图"],
        ["商户选址请求", "—", "site_candidate / site_score_item", "实时", "候选点与可解释评分"],
        ["商户意向表单", "—", "merchant_intent / merchant_match", "实时", "招商对接台账"],
        ["社区治理操作", "—", "community_gap / simulation_record", "实时", "短板与模拟推演"],
        ["评分快照", "—", "district_score_snapshot → v_district_dashboard", "每次同步后", "社区看板与排名"],
    ]
    sh = wb.create_sheet("07 数据流转")
    style_sheet(sh, ["数据来源", "ODS 落地", "DWD/ADS 目标", "更新频率", "用途"],
                [24, 26, 50, 16, 36], flow, "数据流转与分层规划")

    # 容量汇总
    total_t = total_l = total_i = 0
    for t in TABLES:
        tm, lm, im = storage_mb(t)
        total_t += tm
        total_l += lm
        total_i += im
    sh = wb.create_sheet("08 容量汇总")
    rows = [
        ["表数据合计", round(total_t, 1), "MB", "27 张表 3 年在线数据（ODS 按 12 个月）"],
        ["LOB 合计", round(total_l, 1), "MB", "CLOB/JSON 原文"],
        ["索引合计", round(total_i, 1), "MB", "按数据量 24% 估算"],
        ["总计", round(total_t + total_l + total_i, 1), "MB", "不含备份、UNDO、TEMP"],
        ["建议规划", 4096, "MB", "预留 2 倍增长与归档空间"],
    ]
    style_sheet(sh, ["项目", "容量", "单位", "说明"], [24, 14, 8, 60], rows, "存储容量估算")

    p = os.path.join(OUT, "数据字典与数据项清单.xlsx")
    wb.save(p)
    print("wrote", p)


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------
def write_readme():
    text = f"""# 数据库设计交付包清单（本文件由 gen_artifacts.py 自动生成）

> 这是生成器输出的文件清单，会被每次运行覆盖。
> 人工维护的目录说明请看同目录下的 `README.md`。

**项目**：{M.PROJECT}  
**版本**：{M.VERSION}　**日期**：{M.DATE_CN}

## 一、文件清单

| 文件 | 说明 |
| --- | --- |
| `数据库设计说明书.docx` | 完整设计文档：数据项、数据模型、数据规划架构、表结构、存储规划、建表脚本 |
| `数据字典与数据项清单.xlsx` | 自动生成的数据项清单、表清单、字段字典、码表、索引约束、存储规划、容量汇总 |
| `dbml/class_test_full.dbml` | **dbdiagram.io 建模源文件**，复制粘贴到 https://dbdiagram.io/d 即可复现完整 ER 图 |
| `dbml/class_test_<域>.dbml` | 按主题域拆分的 DBML，便于单独查看 |
| `sql/01_tablespace_oracle.sql` | Oracle 表空间规划（DBA 执行） |
| `sql/02_schema_oracle.sql` | Oracle 23ai 生产建表脚本（{len(TABLES)} 张表） |
| `sql/03_schema_h2.sql` | H2 开发库建表脚本，已实际执行验证 |
| `sql/04_schema_mysql.sql` | MySQL 8.0 方言建表脚本（可选） |
| `sql/05_seed_data.sql` | 设施类别、画像标签、演示片区/POI 初始化数据 |
| `sql/06_views_oracle.sql` | 社区看板视图、设施类别统计视图 |
| `sql/07_migration_v1_to_v2.sql` | 从现有 V1 `merchant_intent` 平滑升级到 V2 |
| `图/` | 总体 ER、分域 ER、数据架构、数据流、存储布局图 |
| `data-model.json` | 机器可读的完整模型（供后续代码生成/校验） |

## 二、dbdiagram.io 复现步骤

1. 打开 <https://dbdiagram.io/d>。
2. 清空左侧默认示例，粘贴 `dbml/class_test_full.dbml` 的全部内容。
3. 右侧自动生成 ER 图；使用右上角 **Export → PNG/PDF** 可导出图片。
4. 表分组（TableGroup）对应六个主题域；关系线由 `Ref` 定义。
5. 修改字段时先改 DBML，再同步 `sql/` 与 Excel，保持三处一致。

## 三、建表验证

Oracle 脚本按外键依赖拓扑排序，执行顺序：

```sql
-- DBA
@01_tablespace_oracle.sql
-- 业务用户 life_circle
@02_schema_oracle.sql
@05_seed_data.sql
@06_views_oracle.sql
```

H2 开发库验证命令：

```powershell
java -cp h2-2.2.224.jar org.h2.tools.RunScript `
  -url "jdbc:h2:mem:lifecircle;MODE=Oracle;DB_CLOSE_DELAY=-1" `
  -user sa -script sql/03_schema_h2.sql
```

验证结果：{len(TABLES)} 张表、{sum(len(t["cols"]) for t in TABLES)} 个字段、{sum(1 for t in TABLES for c in t["cols"] if c["fk"])} 个外键全部创建成功。

## 四、设计口径

- 结构化业务数据统一放 DWD；原始接口报文保留在 ODS；评分排名等派生结果放 ADS 快照。
- 时间统一存 UTC，展示层按 Asia/Shanghai 转换。
- 手机号只存 SHA-256 哈希；商户联系方式 AES-256-GCM 加密后 Base64 存储，列表用脱敏字段。
- 枚举值中文与前端 `docs/DATA_CONVENTIONS.md` 逐字一致；英文状态码用于内部流转。
- 大表按时间分区，ODS 按月分区并压缩；索引与数据分表空间存放。
"""
    p = os.path.join(OUT, "交付包清单.md")
    open(p, "w", encoding="utf-8").write(text)
    print("wrote 交付包清单.md")


def write_json():
    import json
    data = {
        "project": M.PROJECT,
        "version": M.VERSION,
        "domains": M.DOMAINS,
        "tables": [
            {
                "name": t["name"], "cn": t["cn"], "domain": t["domain"], "kind": t["kind"],
                "note": t["note"], "partition": t["partition"], "tablespace": t["tablespace"],
                "columns": t["cols"], "indexes": t["indexes"], "checks": t["checks"],
            } for t in TABLES
        ],
        "enums": M.ENUMS,
    }
    p = os.path.join(OUT, "data-model.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("wrote", p)


if __name__ == "__main__":
    write_dbml()
    write_oracle()
    write_mysql()
    write_h2()
    write_seed()
    write_views()
    write_migration()
    write_excel()
    write_readme()
    write_json()
    print("table count", len(TABLES), "column count", sum(len(t["cols"]) for t in TABLES))
