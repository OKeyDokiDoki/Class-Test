# -*- coding: utf-8 -*-
"""从 db_model.py 生成 PlantUML 源文件，并渲染数据库设计相关的 PNG 图。

所属链路
    db_model.py  --本脚本-->  docs/database/puml/*.puml  +  docs/database/图/*.png

产出
    puml/  11 个 PlantUML 源文件（总体 ER、六个分域 ER、数据架构、数据流转、存储布局、建模流程）
    图/    与 puml 对应的 PNG，供 Word 说明书和评审使用

渲染方式
    默认调用 PlantUML 官方在线服务（需要能访问互联网）。
    离线时脚本会保留 .puml 源文件，可自行用本地 plantuml.jar 渲染：
        java -jar plantuml.jar -tpng puml/01_总体ER图.puml

依赖
    pip install Pillow        # 仅图片后处理需要

运行
    cd tools/db-toolchain
    python gen_diagrams.py
"""
import io
import os
import sys
import time
import urllib.request
import zlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import db_model as M

# --- 路径约定 ---------------------------------------------------------------
# 本文件位于 <repo>/tools/db-toolchain/，向上两级就是仓库根目录。
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.environ.get("DB_DESIGN_OUT") or os.path.join(REPO, "docs", "database")
OUT = os.path.join(OUT, "图")
PUML = os.path.join(os.path.dirname(OUT), "puml")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PUML, exist_ok=True)

TABLES = M.TABLES
BY = M.TABLE_BY_NAME
DOMAINS = M.DOMAINS
COLORS = M.DOMAIN_COLORS

KEY_FIELDS = {
    "app_user": ["user_code", "role_code", "status"],
    "user_profile": ["user_id", "profile_type", "profile_label", "version_no", "is_current"],
    "profile_tag": ["tag_code", "tag_name", "dimension_code", "default_weight"],
    "user_profile_tag": ["profile_id", "tag_id", "weight"],
    "profile_dimension_weight": ["profile_id", "dimension_code", "weight"],
    "district": ["district_code", "district_name", "parent_id", "district_level", "resident_count"],
    "population_grid": ["district_id", "grid_code", "data_date", "population", "density"],
    "road_node": ["node_code", "district_id", "lng", "lat"],
    "road_segment": ["segment_code", "from_node_id", "to_node_id", "length_m", "walk_time_s"],
    "facility_category": ["category_code", "category_name", "dimension_code"],
    "poi_facility": ["district_id", "category_id", "poi_name", "lng", "lat", "business_status"],
    "poi_change_log": ["poi_id", "batch_id", "change_type", "changed_at"],
    "resident_assessment": ["resident_code", "district_id", "profile_id", "total_score", "radius_m", "assessed_at"],
    "assessment_dimension": ["assessment_id", "dimension_code", "dimension_score", "weight"],
    "assessment_facility_stat": ["assessment_id", "category_id", "facility_count", "nearest_distance_m", "status"],
    "district_score_snapshot": ["district_id", "batch_id", "coverage_pct", "avg_score", "rank_no", "scored_at"],
    "site_candidate": ["district_id", "candidate_name", "business_type", "population_index", "competitor_count", "site_score"],
    "site_score_item": ["candidate_id", "score_item", "item_score", "weight"],
    "merchant_intent": ["merchant_name", "business_type", "district_id", "candidate_id", "status"],
    "merchant_match": ["intent_id", "district_id", "gap_id", "fit_score", "status"],
    "community_gap": ["district_id", "category_id", "area_name", "issue", "gap_level", "priority_no"],
    "simulation_record": ["district_id", "category_id", "before_coverage", "after_coverage", "benefited_residents"],
    "sync_batch": ["batch_no", "data_source", "sync_type", "status", "started_at"],
    "data_quality_issue": ["batch_id", "rule_code", "severity", "is_handled"],
    "ods_poi_raw": ["batch_id", "source", "source_poi_id", "poi_name", "process_status"],
    "ods_population_raw": ["batch_id", "grid_code", "population", "data_date"],
    "ods_road_raw": ["batch_id", "segment_code", "process_status"],
}

DOMAIN_SUBSETS = {
    "USR": ["app_user", "user_profile", "profile_tag", "user_profile_tag", "profile_dimension_weight"],
    "SIT": ["district", "population_grid", "road_node", "road_segment", "facility_category", "poi_facility"],
    "RES": ["resident_assessment", "assessment_dimension", "assessment_facility_stat", "district_score_snapshot"],
    "MER": ["site_candidate", "site_score_item", "merchant_intent", "merchant_match"],
    "COM": ["community_gap", "simulation_record"],
    "OPS": ["sync_batch", "poi_change_log", "data_quality_issue", "ods_poi_raw", "ods_population_raw", "ods_road_raw"],
}


def puml_header(extra=""):
    return (
        "@startuml\n"
        "skinparam backgroundColor #FFFFFF\n"
        "skinparam shadowing false\n"
        "skinparam defaultFontName \"Microsoft YaHei\"\n"
        "skinparam defaultFontSize 13\n"
        "skinparam dpi 140\n"
        "skinparam nodesep 26\n"
        "skinparam ranksep 40\n"
        "skinparam ArrowColor #7F7F7F\n"
        "skinparam ArrowThickness 1.2\n"
        "hide circle\n"
        "hide empty methods\n"
        "hide empty fields\n"
        + extra
    )


def entity_line(t, fields, stub=False):
    color = "#F2F2F2" if stub else "#" + COLORS[t["domain"]][0]
    cn = "（外部）" if stub else ""
    name = f'{t["name"]}\\n{t["cn"]}{cn}'
    lines = [f'entity "{name}" as {t["name"]} {color} {{']
    if stub:
        lines.append("  *id : BIGINT <<PK>>")
    else:
        pk = [c for c in t["cols"] if c["pk"]]
        for c in pk:
            lines.append(f"  *{c['name']} : {c['typ']} <<PK>>")
        lines.append("  --")
        for c in t["cols"]:
            if c["pk"]:
                continue
            if c["name"] not in fields:
                continue
            tag = " <<FK>>" if c["fk"] else ""
            lines.append(f"  {c['name']} : {c['typ']}{tag}")
    lines.append("}")
    return "\n".join(lines)


def domain_puml(dk):
    names = DOMAIN_SUBSETS[dk]
    subset = [BY[n] for n in names]
    ext = []
    for t in subset:
        for c in t["cols"]:
            if c["fk"]:
                rn = c["fk"].split(".")[0]
                if rn not in names and rn not in [x["name"] for x in ext]:
                    ext.append(BY[rn])
    lines = [puml_header("skinparam linetype polyline\n")]
    lines.append(f'package "{dk} · {DOMAINS[dk]}" {{')
    for t in subset:
        lines.append(entity_line(t, KEY_FIELDS[t["name"]]))
    lines.append("}")
    for t in ext:
        lines.append(entity_line(t, [], stub=True))
    for t in subset:
        for c in t["cols"]:
            if not c["fk"]:
                continue
            rn, rc = c["fk"].split(".")
            if rn == t["name"]:
                continue
            label = c["cn"]
            lines.append(f'{rn} ||--o{{ {t["name"]} : "{label}"')
    lines.append("@enduml")
    return "\n".join(lines)


def overview_puml():
    return r'''@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 13
skinparam dpi 150
skinparam nodesep 30
skinparam ranksep 45
skinparam ArrowColor #5B6B7F
skinparam ArrowThickness 1.4
hide stereotype

rectangle "USR · 用户与画像（5 表）\napp_user / user_profile / profile_tag\nuser_profile_tag / profile_dimension_weight" as usr #E8F0FB
rectangle "SIT · 空间与设施（6 表）\ndistrict / population_grid / road_node\nroad_segment / facility_category / poi_facility" as sit #EAF4EA
rectangle "RES · 居民生活圈评估（4 表）\nresident_assessment / assessment_dimension\nassessment_facility_stat / district_score_snapshot" as res #FFF2E5
rectangle "MER · 商户选址与招商（4 表）\nsite_candidate / site_score_item\nmerchant_intent / merchant_match" as mer #F3EAF7
rectangle "COM · 社区治理（2 表）\ncommunity_gap / simulation_record" as com #E6F4F5
rectangle "OPS · 数据运营与同步（6 表）\nsync_batch / poi_change_log / data_quality_issue\nods_poi_raw / ods_population_raw / ods_road_raw" as ops #F2F2F2

usr --> res : 画像与维度权重
sit --> res : POI / 人口 / 路网
sit --> mer : 人口指数 / 竞争 POI
sit --> com : 设施覆盖 / 短板
mer --> com : 意向匹配短板
res --> com : 评分快照
ops ..> usr : 数据批次版本
ops ..> sit : 数据批次版本
ops ..> res : 数据批次版本
ops ..> mer : 数据批次版本
ops ..> com : 数据批次版本
@enduml'''


def architecture_puml():
    return r'''@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 13
skinparam dpi 150
skinparam ArrowColor #5B6B7F
skinparam ArrowThickness 1.5
skinparam linetype ortho
hide stereotype

rectangle "**L1 数据源层**\n高德 POI 接口 · 人口栅格 · 城市路网 · 业务表单 / 画像对话" as l1 #F7F9FC
rectangle "**L2 接入与治理层**\n半月定时调度 · 增量抽取与批次管理 · 质量校验 · 元数据与权限" as l2 #EEF4FB
rectangle "**L3 ODS 原始层**（TBS_LIFECIRCLE_ODS）\nods_poi_raw · ods_population_raw · ods_road_raw（月分区 + 压缩）" as l3 #FFF8E8
rectangle "**L4 DWD 明细层**（TBS_LIFECIRCLE_DATA）\n用户画像 5 表 · 空间设施 6 表 · 居民评估 4 表\n商户招商 4 表 · 社区治理 2 表" as l4 #EAF4EA
rectangle "**L5 ADS 应用层**（快照 + 缓存）\ndistrict_score_snapshot · v_district_dashboard · 评分缓存" as l5 #F3EAF7
rectangle "**L6 服务与应用层**\n居民评估 API · 商户选址 API · 社区治理 API\nAgent 智能编排 · Vue3 工作台 / ECharts" as l6 #E6F4F5

l1 -down-> l2 : 原始数据
l2 -down-> l3 : 批次落地
l3 -down-> l4 : 清洗 / 合并
l4 -down-> l5 : 指标汇总
l5 -down-> l6 : 查询 / 写入
l4 -down-> l6 : 明细查询
@enduml'''


def flow_puml():
    return r'''@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 12
skinparam dpi 140
skinparam sequenceMessageAlign center
autonumber

actor "调度器" as job
participant "高德 / 政务接口" as src
participant "ODS 原始层" as ods
participant "质量校验" as dq
participant "DWD 明细层" as dwd
participant "ADS 快照 / 缓存" as ads
participant "社区 / 居民 / 商户工作台" as ui

job -> src : 每半月增量拉取
src --> job : 原始报文
job -> ods : 写批次与原始表
ods -> dq : 质量校验
dq -> dq : 记录质量问题
dq -> dwd : 清洗合并入仓
dwd -> dwd : 记录 POI 差异
dwd -> ads : 重算片区快照
ads -> ads : 刷新评分缓存
ui -> ads : 查询评分排名
ads --> ui : 看板数据
ui -> dwd : 评估 / 选址 / 意向
dwd --> ui : 报告 / 候选点 / 匹配
@enduml'''


def storage_puml():
    return r'''@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 13
skinparam dpi 150
skinparam ArrowColor #5B6B7F
skinparam linetype ortho
hide stereotype

rectangle "**TBS_LIFECIRCLE_DATA**\n业务数据  1G → 6G\n用户画像 5 表\n空间设施 6 表\n居民评估 4 表\n商户招商 4 表\n社区治理 2 表" as data #EAF4EA
rectangle "**TBS_LIFECIRCLE_IDX**\n索引  512M → 3G\n主键 / 唯一约束索引\n业务查询 B-tree 索引\n独立存放，便于重建" as idx #EEF4FB
rectangle "**TBS_LIFECIRCLE_LOB**\n大对象  512M → 3G\nGeoJSON 边界\nJSON 变更快照\nCLOB 原始报文" as lob #FFF8E8
rectangle "**TBS_LIFECIRCLE_ODS**\n原始层  1G → 4G\nods_poi_raw（月分区）\nods_population_raw（月分区）\nods_road_raw（月分区）\npoi_change_log（月分区）" as ods #F7F9FC

data -[hidden]right-> idx
data -[hidden]down-> lob
idx -[hidden]down-> ods

note bottom of ods
  **保护与归档**
  RMAN 每周全备 + 每日增量，归档日志保留 30 天
  ODS 分区在线 6 个月，转归档表空间 / 导出后清理
  表空间按 2 倍增长预留，监控阈值 80%
end note
@enduml'''


def dbml_flow_puml():
    return r'''@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 12
skinparam dpi 140
skinparam activityShape roundedBox

start
:业务调研与接口字段盘点;
:数据项识别与编码（DI-域-序号）;
:概念模型 / 主题域划分;
:编写 DBML（表、字段、Ref、TableGroup）;
:导入 dbdiagram.io 生成 ER 图;
if (模型评审通过？) then (否)
  :修订字段、关系与约束;
else (是)
  :导出 Oracle / MySQL / H2 DDL;
  :执行建表与约束验证;
  :同步数据字典与设计说明书;
  :纳入版本管理（Git）;
endif
stop
@enduml'''


def encode_puml(text):
    def encode6bit(b):
        if b < 10:
            return chr(48 + b)
        b -= 10
        if b < 26:
            return chr(65 + b)
        b -= 26
        if b < 26:
            return chr(97 + b)
        b -= 26
        if b == 0:
            return "-"
        if b == 1:
            return "_"
        return "?"

    def append3bytes(b1, b2, b3):
        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F
        return "".join(encode6bit(x & 0x3F) for x in (c1, c2, c3, c4))

    data = zlib.compress(text.encode("utf-8"))[2:-4]
    res = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        if len(chunk) == 3:
            res.append(append3bytes(chunk[0], chunk[1], chunk[2]))
        elif len(chunk) == 2:
            res.append(append3bytes(chunk[0], chunk[1], 0))
        else:
            res.append(append3bytes(chunk[0], 0, 0))
    return "".join(res)


def render(name, puml, fmt="png"):
    src = os.path.join(PUML, name + ".puml")
    with open(src, "w", encoding="utf-8") as f:
        f.write(puml)
    url = f"https://www.plantuml.com/plantuml/{fmt}/" + encode_puml(puml)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if data[:8] == b"\x89PNG\r\n\x1a\n" or data[:5] == b"<?xml" or data[:4] == b"<svg":
                path = os.path.join(OUT, name + "." + fmt)
                with open(path, "wb") as f:
                    f.write(data)
                print("rendered", path, len(data))
                return path
            print("bad response", name, data[:100])
        except Exception as exc:
            print("retry", name, exc)
            time.sleep(3)
    return None


if __name__ == "__main__":
    for old in ("06_社区治理与数据运营域.png", "07_数据规划架构.png",
                "08_半月数据流转.png", "09_存储结构布局.png",
                "10_dbdiagram建模流程.png"):
        p = os.path.join(OUT, old)
        if os.path.exists(p):
            os.remove(p)
    diagrams = [
        ("01_总体ER图", overview_puml()),
        ("02_用户与画像域", domain_puml("USR")),
        ("03_空间与设施域", domain_puml("SIT")),
        ("04_居民评估域", domain_puml("RES")),
        ("05_商户招商域", domain_puml("MER")),
        ("06_社区治理域", domain_puml("COM")),
        ("07_数据运营与同步域", domain_puml("OPS")),
        ("08_数据规划架构", architecture_puml()),
        ("09_半月数据流转", flow_puml()),
        ("10_存储结构布局", storage_puml()),
        ("11_dbdiagram建模流程", dbml_flow_puml()),
    ]
    for name, puml in diagrams:
        render(name, puml)
        time.sleep(1)
