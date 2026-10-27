# -*- coding: utf-8 -*-
"""Single source of truth for the life-circle database design.

All generated artefacts (DBML, Oracle/MySQL/H2 DDL, data dictionary, ER
diagrams and the Word specification) are derived from TABLES below.
"""

from collections import OrderedDict

PROJECT = "城市15分钟便民生活圈与小微开店智能助手"
VERSION = "V2.0"
DATE_CN = "2026年10月"

DOMAINS = OrderedDict([
    ("USR", "用户与画像"),
    ("SIT", "空间与设施"),
    ("RES", "居民生活圈评估"),
    ("MER", "商户选址与招商"),
    ("COM", "社区治理"),
    ("OPS", "数据运营与同步"),
])

DOMAIN_COLORS = {
    "USR": ("E8F0FB", "2F5597"),
    "SIT": ("EAF4EA", "548235"),
    "RES": ("FFF2E5", "C55A11"),
    "MER": ("F3EAF7", "7030A0"),
    "COM": ("E6F4F5", "1F6F78"),
    "OPS": ("F2F2F2", "7F7F7F"),
}

# kind: 主数据 / 业务 / 明细 / 字典 / 快照 / 日志 / ODS
TABLES = []


def col(name, cn, typ, null=True, pk=False, fk=None, uniq=False,
        default=None, check=None, note="", on_delete=None, kind=""):
    return dict(name=name, cn=cn, typ=typ, null=null, pk=pk, fk=fk,
                uniq=uniq, default=default, check=check, note=note,
                on_delete=on_delete, kind=kind)


def table(name, cn, domain, kind, note, cols, indexes=(), checks=(),
          partition=None, tablespace="DATA", rows_3y=0, row_bytes=0,
          lob_bytes=0, retention="长期"):
    TABLES.append(dict(name=name, cn=cn, domain=domain, kind=kind, note=note,
                       cols=cols, indexes=list(indexes), checks=list(checks),
                       partition=partition, tablespace=tablespace,
                       rows_3y=rows_3y, row_bytes=row_bytes, lob_bytes=lob_bytes,
                       retention=retention))


# --------------------------------------------------------------------------
# USR 用户与画像
# --------------------------------------------------------------------------
table(
    "app_user", "用户账号表", "USR", "主数据",
    "三类使用者的统一账号，只保存脱敏业务编号与手机号哈希，不落库明文手机号。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True, note="自增主键"),
        col("user_code", "用户业务编号", "VARCHAR(64)", null=False, uniq=True,
            note="脱敏编号，居民 R、商户 M、社区 C 前缀", check=None),
        col("role_code", "角色编码", "VARCHAR(20)", null=False,
            default="'RESIDENT'", check="role_code IN ('RESIDENT','MERCHANT','COMMUNITY','ADMIN')",
            note="RESIDENT 居民 / MERCHANT 商户 / COMMUNITY 社区 / ADMIN 管理员"),
        col("nickname", "昵称", "VARCHAR(50)", note="展示名称，可为空"),
        col("phone_hash", "手机号哈希", "VARCHAR(64)", uniq=True,
            note="SHA-256 加盐哈希，用于登录匹配，不可逆"),
        col("status", "账号状态", "VARCHAR(20)", null=False, default="'ACTIVE'",
            check="status IN ('ACTIVE','DISABLED','DELETED')", note="ACTIVE/DISABLED/DELETED"),
        col("last_login_at", "最近登录时间", "TIMESTAMP", note="UTC 时间"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_app_user_role_status", ["role_code", "status"], False)],
    rows_3y=52100, row_bytes=260,
)

table(
    "user_profile", "用户画像表", "USR", "业务",
    "一次画像生成的版本化结果，保留历史版本，is_current 标记当前生效画像。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("user_id", "用户", "BIGINT", null=False, fk="app_user.id",
            on_delete="CASCADE", note="所属用户"),
        col("profile_type", "画像类型", "VARCHAR(20)", null=False,
            check="profile_type IN ('RESIDENT','MERCHANT')", note="居民画像或商户画像"),
        col("profile_label", "画像标签", "VARCHAR(50)", null=False,
            note="如“青年夜班画像”“稳健型商户画像”"),
        col("source", "生成方式", "VARCHAR(20)", null=False, default="'FORM'",
            check="source IN ('FORM','CHAT','IMPORT')", note="表单/多轮对话/导入"),
        col("confidence", "画像置信度", "DECIMAL(5,2)",
            check="confidence BETWEEN 0 AND 100", note="0-100，表示标签可信程度"),
        col("version_no", "版本号", "INT", null=False, default="1", note="从 1 递增"),
        col("is_current", "是否当前版本", "CHAR(1)", null=False, default="'Y'",
            check="is_current IN ('Y','N')", note="Y/N，同一用户仅一条 Y"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("uk_user_profile_ver", ["user_id", "version_no"], True),
             ("idx_user_profile_cur", ["user_id", "is_current"], False)],
    rows_3y=62500, row_bytes=180,
)

table(
    "profile_tag", "画像标签字典表", "USR", "字典",
    "可配置的关注点标签库，按角色与评分维度归类，供画像生成和权重计算使用。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("tag_code", "标签编码", "VARCHAR(40)", null=False, uniq=True,
            note="如 NIGHT_MEDICAL、FRESH_FOOD"),
        col("tag_name", "标签名称", "VARCHAR(50)", null=False, note="如“夜间就医”"),
        col("role_scope", "适用角色", "VARCHAR(20)", null=False, default="'ALL'",
            check="role_scope IN ('RESIDENT','MERCHANT','ALL')", note="适用角色范围"),
        col("dimension_code", "评分维度编码", "VARCHAR(30)", null=False,
            note="关联 FACILITY_DIMENSION 编码"),
        col("default_weight", "默认权重", "DECIMAL(5,2)", null=False, default="20",
            check="default_weight BETWEEN 0 AND 100", note="0-100 百分比"),
        col("status", "状态", "VARCHAR(20)", null=False, default="'ACTIVE'",
            check="status IN ('ACTIVE','INACTIVE')"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_profile_tag_dim", ["dimension_code", "role_scope"], False)],
    rows_3y=40, row_bytes=200,
)

table(
    "user_profile_tag", "用户画像标签明细表", "USR", "明细",
    "画像与标签的多对多关联，记录用户勾选/对话提取出的标签及个性化权重。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("profile_id", "画像", "BIGINT", null=False, fk="user_profile.id",
            on_delete="CASCADE"),
        col("tag_id", "标签", "BIGINT", null=False, fk="profile_tag.id",
            on_delete="RESTRICT"),
        col("weight", "个性化权重", "DECIMAL(5,2)", null=False, default="20",
            check="weight BETWEEN 0 AND 100", note="0-100 百分比，参与加权评分"),
        col("selected_at", "选取时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("uk_profile_tag", ["profile_id", "tag_id"], True)],
    rows_3y=312500, row_bytes=60,
)

table(
    "profile_dimension_weight", "画像维度权重表", "USR", "明细",
    "画像对五个评分维度的最终权重，居民评估时按该表动态加权，权重之和应为 100。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("profile_id", "画像", "BIGINT", null=False, fk="user_profile.id",
            on_delete="CASCADE"),
        col("dimension_code", "维度编码", "VARCHAR(30)", null=False,
            note="FRESH/MEDICAL/EDU/TRAFFIC/NIGHT"),
        col("dimension_name", "维度名称", "VARCHAR(50)", null=False,
            note="生鲜购物/医疗健康/亲子教育/交通通勤/夜间服务"),
        col("weight", "维度权重", "DECIMAL(5,2)", null=False,
            check="weight BETWEEN 0 AND 100", note="0-100 百分比"),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("uk_profile_dim", ["profile_id", "dimension_code"], True)],
    rows_3y=312500, row_bytes=60,
)

# --------------------------------------------------------------------------
# SIT 空间与设施
# --------------------------------------------------------------------------
table(
    "district", "社区片区表", "SIT", "主数据",
    "街道—社区—网格三级空间主数据，是设施、评估、选址和治理的公共维度。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_code", "片区编码", "VARCHAR(40)", null=False, uniq=True,
            note="行政区划码+序号，全局唯一"),
        col("district_name", "片区名称", "VARCHAR(100)", null=False),
        col("parent_id", "上级片区", "BIGINT", fk="district.id", on_delete="RESTRICT",
            note="自关联，街道→社区→网格"),
        col("district_level", "层级", "VARCHAR(20)", null=False,
            check="district_level IN ('STREET','COMMUNITY','GRID')",
            note="STREET/COMMUNITY/GRID"),
        col("city_code", "城市行政区划代码", "VARCHAR(20)", null=False,
            note="GB/T 2260 六位代码"),
        col("center_lng", "中心点经度", "DECIMAL(10,6)",
            check="center_lng BETWEEN -180 AND 180", note="WGS84，单位度"),
        col("center_lat", "中心点纬度", "DECIMAL(10,6)",
            check="center_lat BETWEEN -90 AND 90", note="WGS84，单位度"),
        col("boundary_geojson", "边界 GeoJSON", "CLOB", note="片区边界，GeoJSON Polygon"),
        col("area_sqm", "面积", "DECIMAL(12,2)", note="平方米"),
        col("resident_count", "常住人口", "INT", check="resident_count >= 0", note="人"),
        col("status", "状态", "VARCHAR(20)", null=False, default="'ACTIVE'",
            check="status IN ('ACTIVE','INACTIVE')"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_district_parent", ["parent_id"], False),
             ("idx_district_city", ["city_code", "district_level"], False)],
    rows_3y=120, row_bytes=800, lob_bytes=2000,
)

table(
    "population_grid", "人口栅格表", "SIT", "业务",
    "按栅格与统计日期保存常住人口和密度，是商户选址人口指数与社区覆盖测算的输入。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_id", "所属片区", "BIGINT", null=False, fk="district.id",
            on_delete="CASCADE"),
        col("grid_code", "栅格编码", "VARCHAR(40)", null=False, note="统一栅格编码"),
        col("grid_level", "栅格精度", "VARCHAR(20)", null=False, default="'GRID_250M'",
            check="grid_level IN ('GRID_100M','GRID_250M','GRID_500M')"),
        col("center_lng", "栅格中心经度", "DECIMAL(10,6)", null=False,
            check="center_lng BETWEEN -180 AND 180"),
        col("center_lat", "栅格中心纬度", "DECIMAL(10,6)", null=False,
            check="center_lat BETWEEN -90 AND 90"),
        col("population", "常住人口", "INT", null=False, check="population >= 0", note="人"),
        col("density", "人口密度", "DECIMAL(12,2)", check="density >= 0",
            note="人/平方公里"),
        col("data_date", "统计日期", "DATE", null=False, note="人口数据口径日期"),
        col("source", "数据来源", "VARCHAR(20)", null=False, default="'GOV'",
            check="source IN ('GOV','AMAP','MANUAL')"),
        col("created_at", "入库时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("uk_pop_grid_date", ["grid_code", "data_date"], True),
             ("idx_pop_district_date", ["district_id", "data_date"], False)],
    rows_3y=2880, row_bytes=140,
)

table(
    "road_node", "路网节点表", "SIT", "主数据",
    "步行路网拓扑节点（路口、小区出入口、过街设施），用于 15 分钟步行可达计算。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("node_code", "节点编码", "VARCHAR(40)", null=False, uniq=True),
        col("district_id", "所属片区", "BIGINT", fk="district.id", on_delete="SET NULL"),
        col("lng", "经度", "DECIMAL(10,6)", null=False,
            check="lng BETWEEN -180 AND 180"),
        col("lat", "纬度", "DECIMAL(10,6)", null=False,
            check="lat BETWEEN -90 AND 90"),
        col("node_type", "节点类型", "VARCHAR(20)", null=False, default="'INTERSECTION'",
            check="node_type IN ('INTERSECTION','ENTRANCE','CROSSING')"),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_road_node_district", ["district_id"], False)],
    rows_3y=20000, row_bytes=100,
)

table(
    "road_segment", "路网步行段表", "SIT", "主数据",
    "连接两个路网节点的步行段，保存长度与步行耗时，构成 15 分钟等时圈的图结构。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("segment_code", "路段编码", "VARCHAR(50)", null=False, uniq=True),
        col("district_id", "所属片区", "BIGINT", fk="district.id", on_delete="SET NULL"),
        col("from_node_id", "起点节点", "BIGINT", null=False, fk="road_node.id",
            on_delete="RESTRICT"),
        col("to_node_id", "终点节点", "BIGINT", null=False, fk="road_node.id",
            on_delete="RESTRICT"),
        col("road_name", "道路名称", "VARCHAR(100)"),
        col("road_level", "道路等级", "VARCHAR(20)", null=False, default="'BRANCH'",
            check="road_level IN ('MAIN','BRANCH','ALLEY')"),
        col("length_m", "路段长度", "DECIMAL(10,2)", null=False, check="length_m > 0",
            note="米"),
        col("walk_time_s", "步行耗时", "INT", null=False, check="walk_time_s > 0",
            note="秒，按 1.2 m/s 及过街等待估算"),
        col("is_walkable", "是否可步行", "CHAR(1)", null=False, default="'Y'",
            check="is_walkable IN ('Y','N')"),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_road_seg_from", ["from_node_id"], False),
             ("idx_road_seg_to", ["to_node_id"], False),
             ("idx_road_seg_district", ["district_id"], False)],
    rows_3y=30000, row_bytes=180,
)

table(
    "facility_category", "设施类别字典表", "SIT", "字典",
    "POI 类别与五维评分的映射字典，统一高德分类与业务维度，避免代码硬编码。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("category_code", "类别编码", "VARCHAR(40)", null=False, uniq=True,
            note="如 FRESH_MARKET、CLINIC"),
        col("category_name", "类别名称", "VARCHAR(50)", null=False, note="如“社区诊所”"),
        col("dimension_code", "评分维度编码", "VARCHAR(30)", null=False,
            note="FRESH/MEDICAL/EDU/TRAFFIC/NIGHT"),
        col("dimension_name", "评分维度名称", "VARCHAR(50)", null=False),
        col("icon", "图标标识", "VARCHAR(100)", note="前端图标名"),
        col("sort_no", "排序号", "INT", null=False, default="0"),
        col("status", "状态", "VARCHAR(20)", null=False, default="'ACTIVE'",
            check="status IN ('ACTIVE','INACTIVE')"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_fac_category_dim", ["dimension_code", "sort_no"], False)],
    rows_3y=30, row_bytes=220,
)

table(
    "poi_facility", "设施网点 POI 表", "SIT", "业务",
    "社区周边生鲜、医疗、教育、交通、夜间服务等设施网点，是评估与选址的主数据。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_id", "所属片区", "BIGINT", null=False, fk="district.id",
            on_delete="RESTRICT"),
        col("category_id", "设施类别", "BIGINT", null=False,
            fk="facility_category.id", on_delete="RESTRICT"),
        col("poi_name", "设施名称", "VARCHAR(200)", null=False),
        col("lng", "经度", "DECIMAL(10,6)", null=False,
            check="lng BETWEEN -180 AND 180"),
        col("lat", "纬度", "DECIMAL(10,6)", null=False,
            check="lat BETWEEN -90 AND 90"),
        col("address", "详细地址", "VARCHAR(255)"),
        col("business_status", "营业状态", "VARCHAR(20)", null=False, default="'OPEN'",
            check="business_status IN ('OPEN','CLOSED','MOVED','UNKNOWN')"),
        col("source", "数据来源", "VARCHAR(20)", null=False,
            check="source IN ('AMAP','GOV','MANUAL')"),
        col("source_poi_id", "来源 POI 编号", "VARCHAR(100)", null=False,
            note="高德 POI ID 或政务数据主键，用于增量去重"),
        col("telephone", "公开电话", "VARCHAR(50)", note="仅公共设施公开电话，不含个人信息"),
        col("first_seen_at", "首次发现时间", "TIMESTAMP", null=False),
        col("last_seen_at", "最近发现时间", "TIMESTAMP", null=False),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("is_valid", "是否有效", "CHAR(1)", null=False, default="'Y'",
            check="is_valid IN ('Y','N')"),
    ],
    indexes=[("uk_poi_source", ["source", "source_poi_id"], True),
             ("idx_poi_district_cat", ["district_id", "category_id"], False),
             ("idx_poi_category", ["category_id", "is_valid"], False),
             ("idx_poi_name", ["poi_name"], False)],
    rows_3y=8000, row_bytes=420,
)

table(
    "poi_change_log", "POI 变更日志表", "OPS", "日志",
    "记录新增、变更、关停和清洗无效的 POI 差异，支持增量追溯与数据质量审计。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("poi_id", "设施", "BIGINT", fk="poi_facility.id", on_delete="SET NULL"),
        col("batch_id", "同步批次", "BIGINT", null=False, fk="sync_batch.id",
            on_delete="RESTRICT"),
        col("change_type", "变更类型", "VARCHAR(20)", null=False,
            check="change_type IN ('INSERT','UPDATE','CLOSE','INVALID')"),
        col("change_summary", "变更摘要", "VARCHAR(500)",
            note="如“地址变更”“营业状态 OPEN→CLOSED”"),
        col("before_json", "变更前数据", "CLOB", note="JSON 快照，便于回滚"),
        col("after_json", "变更后数据", "CLOB", note="JSON 快照"),
        col("changed_at", "变更时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_poi_log_poi", ["poi_id", "changed_at"], False),
             ("idx_poi_log_batch", ["batch_id"], False)],
    partition="changed_at", tablespace="ODS", rows_3y=96000, row_bytes=500,
    lob_bytes=800,
)

# --------------------------------------------------------------------------
# RES 居民生活圈评估
# --------------------------------------------------------------------------
table(
    "resident_assessment", "居民生活圈评估表", "RES", "业务",
    "一次居民生活圈体检的汇总结果，保存评分、画像、步行半径和诊断结论。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("resident_code", "居民编号", "VARCHAR(64)", null=False,
            note="脱敏居民编号，未登录用户也可评估"),
        col("user_id", "用户", "BIGINT", fk="app_user.id", on_delete="SET NULL"),
        col("district_id", "目标片区", "BIGINT", null=False, fk="district.id",
            on_delete="RESTRICT"),
        col("profile_id", "画像版本", "BIGINT", fk="user_profile.id",
            on_delete="SET NULL", note="个性化权重来源"),
        col("batch_id", "数据批次", "BIGINT", fk="sync_batch.id", on_delete="SET NULL",
            note="评估使用的 POI/人口数据版本"),
        col("radius_m", "步行半径", "INT", null=False, default="1080",
            check="radius_m BETWEEN 100 AND 3000", note="米，15 分钟按 1.2 m/s 约 1080 m"),
        col("total_score", "综合评分", "INT", null=False,
            check="total_score BETWEEN 0 AND 100", note="0-100"),
        col("profile_label", "画像标签", "VARCHAR(50)", note="冗余画像标签，便于列表展示"),
        col("insight", "诊断建议", "VARCHAR(1000)", note="Agent 生成的优缺点诊断"),
        col("assessed_at", "评估时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_assess_district_time", ["district_id", "assessed_at"], False),
             ("idx_assess_user", ["user_id", "assessed_at"], False),
             ("idx_assess_batch", ["batch_id"], False)],
    partition="assessed_at", rows_3y=300000, row_bytes=360,
)

table(
    "assessment_dimension", "评估维度得分表", "RES", "明细",
    "五维评分的分项结果，保存得分、权重和设施计数，支撑雷达图与可解释性。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("assessment_id", "评估记录", "BIGINT", null=False,
            fk="resident_assessment.id", on_delete="CASCADE"),
        col("dimension_code", "维度编码", "VARCHAR(30)", null=False),
        col("dimension_name", "维度名称", "VARCHAR(50)", null=False),
        col("dimension_score", "维度得分", "INT", null=False,
            check="dimension_score BETWEEN 0 AND 100"),
        col("weight", "维度权重", "DECIMAL(5,2)", null=False,
            check="weight BETWEEN 0 AND 100", note="来自画像，百分比"),
        col("facility_count", "设施数量", "INT", null=False, default="0",
            check="facility_count >= 0"),
    ],
    indexes=[("uk_assess_dim", ["assessment_id", "dimension_code"], True)],
    rows_3y=1500000, row_bytes=120,
)

table(
    "assessment_facility_stat", "评估设施盘点表", "RES", "明细",
    "一次评估中各设施类别的数量、最近距离与状态，用于设施清单和短板定位。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("assessment_id", "评估记录", "BIGINT", null=False,
            fk="resident_assessment.id", on_delete="CASCADE"),
        col("category_id", "设施类别", "BIGINT", null=False,
            fk="facility_category.id", on_delete="RESTRICT"),
        col("facility_count", "设施数量", "INT", null=False, default="0",
            check="facility_count >= 0"),
        col("nearest_distance_m", "最近距离", "DECIMAL(10,2)",
            check="nearest_distance_m >= 0", note="米"),
        col("status", "设施状态", "VARCHAR(20)",
            note="充足/基本满足/待改善，与前端枚举逐字一致"),
    ],
    indexes=[("uk_assess_category", ["assessment_id", "category_id"], True)],
    rows_3y=3000000, row_bytes=100,
)

table(
    "district_score_snapshot", "片区评分快照表", "RES", "快照",
    "每次数据同步后按片区重算的便民评分与排名，供社区热力图、排名和趋势查询。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_id", "片区", "BIGINT", null=False, fk="district.id",
            on_delete="CASCADE"),
        col("batch_id", "数据批次", "BIGINT", fk="sync_batch.id", on_delete="SET NULL"),
        col("coverage_pct", "覆盖率", "INT", null=False,
            check="coverage_pct BETWEEN 0 AND 100", note="%，15 分钟覆盖人口占比"),
        col("avg_score", "平均评分", "DECIMAL(5,2)", null=False,
            check="avg_score BETWEEN 0 AND 100"),
        col("rank_no", "辖区排名", "INT", check="rank_no > 0"),
        col("resident_count", "覆盖人口", "INT", check="resident_count >= 0"),
        col("scored_at", "计算时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("uk_district_batch", ["district_id", "batch_id"], True),
             ("idx_district_score_time", ["scored_at"], False)],
    rows_3y=864, row_bytes=120,
)

# --------------------------------------------------------------------------
# MER 商户选址与招商
# --------------------------------------------------------------------------
table(
    "site_candidate", "商户选址候选点表", "MER", "业务",
    "Agent 依据人口栅格与同业态竞争 POI 推演出的候选点位，含评分与关键指标。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_id", "所属片区", "BIGINT", null=False, fk="district.id",
            on_delete="RESTRICT"),
        col("batch_id", "数据批次", "BIGINT", fk="sync_batch.id", on_delete="SET NULL"),
        col("candidate_name", "候选点名称", "VARCHAR(100)", null=False,
            note="如“东园路口”"),
        col("business_type", "经营业态", "VARCHAR(100)",
            note="早餐、便利店、托育、药店等"),
        col("lng", "经度", "DECIMAL(10,6)", check="lng BETWEEN -180 AND 180"),
        col("lat", "纬度", "DECIMAL(10,6)", check="lat BETWEEN -90 AND 90"),
        col("population_index", "人口指数", "DECIMAL(10,2)",
            check="population_index >= 0", note="候选项半径内人口/密度综合指数"),
        col("competitor_count", "同业态竞争数", "INT", check="competitor_count >= 0",
            note="候选点 15 分钟范围内同业态 POI 数"),
        col("demand_level", "需求强度", "VARCHAR(10)", note="高/中高/中/低"),
        col("competition_level", "竞争度", "VARCHAR(10)", note="低/中/高"),
        col("rent_min", "租金下限", "DECIMAL(8,2)", check="rent_min >= 0",
            note="万元/年"),
        col("rent_max", "租金上限", "DECIMAL(8,2)", check="rent_max >= 0",
            note="万元/年"),
        col("site_score", "选址评分", "INT", check="site_score BETWEEN 0 AND 100"),
        col("created_at", "生成时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_site_district_type", ["district_id", "business_type", "site_score"], False),
             ("idx_site_batch", ["batch_id"], False)],
    checks=[("ck_site_rent", "rent_min IS NULL OR rent_max IS NULL OR rent_min <= rent_max")],
    rows_3y=6000, row_bytes=420,
)

table(
    "site_score_item", "选址评分明细表", "MER", "明细",
    "候选点各评分项的分值、权重与理由，保证选址推荐可解释、可复核。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("candidate_id", "候选点", "BIGINT", null=False,
            fk="site_candidate.id", on_delete="CASCADE"),
        col("score_item", "评分项", "VARCHAR(50)", null=False,
            note="人口密度/竞争饱和度/租金/交通/设施缺口"),
        col("item_score", "得分", "DECIMAL(5,2)", null=False,
            check="item_score BETWEEN 0 AND 100"),
        col("weight", "权重", "DECIMAL(5,2)", null=False,
            check="weight BETWEEN 0 AND 100"),
        col("reason", "评分理由", "VARCHAR(255)", note="给商户看的解释文本"),
    ],
    indexes=[("uk_site_score_item", ["candidate_id", "score_item"], True)],
    rows_3y=48000, row_bytes=220,
)

table(
    "merchant_intent", "商户开店意向表", "MER", "业务",
    "商户提交的开店意向，保留原有字段并扩展片区、候选点、预算和状态，兼容现有接口。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("merchant_name", "商户名称", "VARCHAR(100)", null=False),
        col("business_type", "经营业态", "VARCHAR(100)", null=False),
        col("contact", "联系方式密文", "VARCHAR(200)", null=False,
            note="AES-256-GCM 加密后 Base64，禁止明文落库；接口层解密"),
        col("contact_masked", "联系方式脱敏", "VARCHAR(20)",
            note="如 138****8000，列表展示用"),
        col("district_id", "意向片区", "BIGINT", fk="district.id", on_delete="SET NULL"),
        col("candidate_id", "意向候选点", "BIGINT", fk="site_candidate.id",
            on_delete="SET NULL"),
        col("budget_min", "预算下限", "DECIMAL(8,2)", check="budget_min >= 0",
            note="万元"),
        col("budget_max", "预算上限", "DECIMAL(8,2)", check="budget_max >= 0",
            note="万元"),
        col("area_sqm", "经营面积", "DECIMAL(8,2)", check="area_sqm > 0",
            note="平方米"),
        col("remark", "经营说明", "VARCHAR(500)"),
        col("status", "意向状态", "VARCHAR(20)", null=False, default="'SUBMITTED'",
            check="status IN ('SUBMITTED','MATCHED','CONTACTED','CLOSED','INVALID')"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("updated_at", "更新时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_intent_status_time", ["status", "created_at"], False),
             ("idx_intent_district", ["district_id"], False),
             ("idx_intent_candidate", ["candidate_id"], False)],
    checks=[("ck_intent_budget", "budget_min IS NULL OR budget_max IS NULL OR budget_min <= budget_max")],
    rows_3y=6000, row_bytes=520,
)

table(
    "merchant_match", "招商匹配表", "MER", "业务",
    "社区短板与商户意向的双向匹配结果，记录匹配分、理由和对接状态。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("intent_id", "开店意向", "BIGINT", null=False, fk="merchant_intent.id",
            on_delete="CASCADE"),
        col("district_id", "片区", "BIGINT", null=False, fk="district.id",
            on_delete="RESTRICT"),
        col("gap_id", "对应短板", "BIGINT", fk="community_gap.id", on_delete="SET NULL"),
        col("fit_score", "匹配度", "INT", null=False,
            check="fit_score BETWEEN 0 AND 100"),
        col("match_reason", "匹配理由", "VARCHAR(500)"),
        col("status", "对接状态", "VARCHAR(20)", null=False, default="'PENDING'",
            check="status IN ('PENDING','ACCEPTED','REJECTED')"),
        col("matched_at", "匹配时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_match_intent", ["intent_id"], False),
             ("idx_match_gap", ["gap_id"], False),
             ("idx_match_district_score", ["district_id", "fit_score"], False)],
    rows_3y=15000, row_bytes=380,
)

# --------------------------------------------------------------------------
# COM 社区治理
# --------------------------------------------------------------------------
table(
    "community_gap", "社区短板片区表", "COM", "业务",
    "社区识别出的买菜难、就医远、托育不足等短板，含缺口等级、未覆盖人口与优先级。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_id", "片区", "BIGINT", null=False, fk="district.id",
            on_delete="CASCADE"),
        col("category_id", "设施类别", "BIGINT", null=False,
            fk="facility_category.id", on_delete="RESTRICT"),
        col("area_name", "短板区域名称", "VARCHAR(100)", null=False),
        col("issue", "短板描述", "VARCHAR(200)", null=False,
            note="如“夜间就医距离较远”"),
        col("gap_level", "缺口等级", "VARCHAR(10)", null=False,
            note="高/中/低，与前端枚举一致"),
        col("uncovered_residents", "未覆盖人口", "INT", check="uncovered_residents >= 0",
            note="人"),
        col("priority_no", "改造优先级", "INT", check="priority_no > 0",
            note="1 为最高"),
        col("batch_id", "数据批次", "BIGINT", fk="sync_batch.id", on_delete="SET NULL"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_gap_district_level", ["district_id", "gap_level"], False),
             ("idx_gap_category", ["category_id"], False),
             ("idx_gap_batch", ["batch_id"], False)],
    rows_3y=1500, row_bytes=320,
)

table(
    "simulation_record", "网点增设模拟记录表", "COM", "业务",
    "社区在地图上模拟新增便民网点后的覆盖率、受益人口和前后对比，支撑改造决策。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("district_id", "片区", "BIGINT", null=False, fk="district.id",
            on_delete="CASCADE"),
        col("category_id", "设施类别", "BIGINT", null=False,
            fk="facility_category.id", on_delete="RESTRICT"),
        col("business_type", "模拟业态", "VARCHAR(100)"),
        col("lng", "模拟点经度", "DECIMAL(10,6)", check="lng BETWEEN -180 AND 180"),
        col("lat", "模拟点纬度", "DECIMAL(10,6)", check="lat BETWEEN -90 AND 90"),
        col("before_coverage", "模拟前覆盖率", "INT", null=False,
            check="before_coverage BETWEEN 0 AND 100", note="%"),
        col("after_coverage", "模拟后覆盖率", "INT", null=False,
            check="after_coverage BETWEEN 0 AND 100", note="%"),
        col("benefited_residents", "受益人口", "INT", null=False,
            check="benefited_residents >= 0"),
        col("operator", "操作人", "VARCHAR(50)", note="社区工作人员编号"),
        col("simulated_at", "模拟时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_sim_district_time", ["district_id", "simulated_at"], False)],
    rows_3y=6000, row_bytes=280,
)

# --------------------------------------------------------------------------
# OPS 数据运营与同步
# --------------------------------------------------------------------------
table(
    "sync_batch", "数据同步批次表", "OPS", "业务",
    "每半月一次 POI/人口/路网增量同步的批次台账，记录数量、状态与错误信息。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("batch_no", "批次号", "VARCHAR(40)", null=False, uniq=True,
            note="如 POI-20261015-01"),
        col("data_source", "数据来源", "VARCHAR(20)", null=False,
            check="data_source IN ('AMAP','GOV','MANUAL')"),
        col("sync_type", "同步类型", "VARCHAR(20)", null=False,
            check="sync_type IN ('FULL','INCREMENT')"),
        col("started_at", "开始时间", "TIMESTAMP", null=False),
        col("finished_at", "结束时间", "TIMESTAMP"),
        col("total_count", "处理总数", "INT", null=False, default="0",
            check="total_count >= 0"),
        col("insert_count", "新增数", "INT", null=False, default="0"),
        col("update_count", "变更数", "INT", null=False, default="0"),
        col("close_count", "关停数", "INT", null=False, default="0"),
        col("invalid_count", "无效数", "INT", null=False, default="0"),
        col("status", "批次状态", "VARCHAR(20)", null=False, default="'RUNNING'",
            check="status IN ('RUNNING','SUCCESS','FAILED','PARTIAL')"),
        col("error_msg", "错误信息", "VARCHAR(1000)"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_sync_status_time", ["status", "started_at"], False)],
    rows_3y=72, row_bytes=320,
)

table(
    "data_quality_issue", "数据质量问题表", "OPS", "日志",
    "同步过程中的重复、坐标异常、类别缺失等质量问题及处理状态，支撑数据治理闭环。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("batch_id", "同步批次", "BIGINT", null=False, fk="sync_batch.id",
            on_delete="CASCADE"),
        col("poi_id", "设施", "BIGINT", fk="poi_facility.id", on_delete="SET NULL"),
        col("rule_code", "校验规则编码", "VARCHAR(40)", null=False,
            note="如 DUP_POI、COORD_OUT_OF_RANGE"),
        col("issue_desc", "问题描述", "VARCHAR(500)", null=False),
        col("severity", "严重程度", "VARCHAR(20)", null=False,
            check="severity IN ('HIGH','MEDIUM','LOW')"),
        col("is_handled", "是否已处理", "CHAR(1)", null=False, default="'N'",
            check="is_handled IN ('Y','N')"),
        col("handled_at", "处理时间", "TIMESTAMP"),
        col("created_at", "创建时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
    ],
    indexes=[("idx_dq_batch_severity", ["batch_id", "severity", "is_handled"], False)],
    rows_3y=50000, row_bytes=320,
)

table(
    "ods_poi_raw", "POI 原始数据表", "OPS", "ODS",
    "高德/政务 POI 接口原始报文落地，保留原样 JSON，供清洗、重放和审计。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("batch_id", "同步批次", "BIGINT", null=False, fk="sync_batch.id",
            on_delete="CASCADE"),
        col("source", "数据来源", "VARCHAR(20)", null=False,
            check="source IN ('AMAP','GOV','MANUAL')"),
        col("source_poi_id", "来源 POI 编号", "VARCHAR(100)", null=False),
        col("poi_name", "设施名称", "VARCHAR(200)"),
        col("lng", "经度", "DECIMAL(10,6)"),
        col("lat", "纬度", "DECIMAL(10,6)"),
        col("category_raw", "原始类别", "VARCHAR(100)"),
        col("address", "原始地址", "VARCHAR(255)"),
        col("raw_json", "原始报文", "CLOB", null=False, note="接口返回 JSON 原样保存"),
        col("load_at", "入库时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("process_status", "处理状态", "VARCHAR(20)", null=False, default="'PENDING'",
            check="process_status IN ('PENDING','PROCESSED','REJECTED')"),
    ],
    indexes=[("idx_ods_poi_batch", ["batch_id", "process_status"], False),
             ("idx_ods_poi_source", ["source", "source_poi_id"], False)],
    partition="load_at", tablespace="ODS", rows_3y=192000, row_bytes=420,
    lob_bytes=1500, retention="在线 6 个月，归档 12 个月",
)

table(
    "ods_population_raw", "人口栅格原始数据表", "OPS", "ODS",
    "人口栅格文件/接口的原始统计值，按批次保留，供复算和口径追溯。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("batch_id", "同步批次", "BIGINT", null=False, fk="sync_batch.id",
            on_delete="CASCADE"),
        col("grid_code", "栅格编码", "VARCHAR(40)", null=False),
        col("population", "人口数", "INT", check="population >= 0"),
        col("density", "人口密度", "DECIMAL(12,2)", check="density >= 0"),
        col("data_date", "统计日期", "DATE"),
        col("raw_json", "原始报文", "CLOB", null=False),
        col("load_at", "入库时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("process_status", "处理状态", "VARCHAR(20)", null=False, default="'PENDING'",
            check="process_status IN ('PENDING','PROCESSED','REJECTED')"),
    ],
    indexes=[("idx_ods_pop_batch", ["batch_id", "process_status"], False)],
    partition="load_at", tablespace="ODS", rows_3y=6000, row_bytes=220,
    lob_bytes=500, retention="在线 6 个月，归档 12 个月",
)

table(
    "ods_road_raw", "路网原始数据表", "OPS", "ODS",
    "路网数据文件的原始路段记录，保留几何与属性原文，供拓扑重建。",
    [
        col("id", "主键", "BIGINT", null=False, pk=True),
        col("batch_id", "同步批次", "BIGINT", null=False, fk="sync_batch.id",
            on_delete="CASCADE"),
        col("segment_code", "路段编码", "VARCHAR(50)"),
        col("raw_json", "原始报文", "CLOB", null=False),
        col("load_at", "入库时间", "TIMESTAMP", null=False, default="CURRENT_TIMESTAMP"),
        col("process_status", "处理状态", "VARCHAR(20)", null=False, default="'PENDING'",
            check="process_status IN ('PENDING','PROCESSED','REJECTED')"),
    ],
    indexes=[("idx_ods_road_batch", ["batch_id", "process_status"], False)],
    partition="load_at", tablespace="ODS", rows_3y=60000, row_bytes=200,
    lob_bytes=800, retention="在线 6 个月，归档 12 个月",
)

# --------------------------------------------------------------------------
# Enumerations / code tables (documentation and Excel)
# --------------------------------------------------------------------------
ENUMS = [
    ("角色编码", "role_code", "RESIDENT", "居民用户", "app_user.role_code"),
    ("角色编码", "role_code", "MERCHANT", "小微商户", "app_user.role_code"),
    ("角色编码", "role_code", "COMMUNITY", "社区管理员", "app_user.role_code"),
    ("角色编码", "role_code", "ADMIN", "系统管理员", "app_user.role_code"),
    ("账号状态", "user_status", "ACTIVE", "正常", "app_user.status"),
    ("账号状态", "user_status", "DISABLED", "已停用", "app_user.status"),
    ("账号状态", "user_status", "DELETED", "已注销", "app_user.status"),
    ("画像类型", "profile_type", "RESIDENT", "居民画像", "user_profile.profile_type"),
    ("画像类型", "profile_type", "MERCHANT", "商户画像", "user_profile.profile_type"),
    ("画像来源", "profile_source", "FORM", "标签勾选表单", "user_profile.source"),
    ("画像来源", "profile_source", "CHAT", "多轮对话提取", "user_profile.source"),
    ("画像来源", "profile_source", "IMPORT", "批量导入", "user_profile.source"),
    ("片区层级", "district_level", "STREET", "街道", "district.district_level"),
    ("片区层级", "district_level", "COMMUNITY", "社区", "district.district_level"),
    ("片区层级", "district_level", "GRID", "网格", "district.district_level"),
    ("栅格精度", "grid_level", "GRID_100M", "100 米栅格", "population_grid.grid_level"),
    ("栅格精度", "grid_level", "GRID_250M", "250 米栅格", "population_grid.grid_level"),
    ("栅格精度", "grid_level", "GRID_500M", "500 米栅格", "population_grid.grid_level"),
    ("道路等级", "road_level", "MAIN", "主干路", "road_segment.road_level"),
    ("道路等级", "road_level", "BRANCH", "支路", "road_segment.road_level"),
    ("道路等级", "road_level", "ALLEY", "街巷", "road_segment.road_level"),
    ("POI 营业状态", "business_status", "OPEN", "营业", "poi_facility.business_status"),
    ("POI 营业状态", "business_status", "CLOSED", "关停", "poi_facility.business_status"),
    ("POI 营业状态", "business_status", "MOVED", "迁址", "poi_facility.business_status"),
    ("POI 营业状态", "business_status", "UNKNOWN", "未知", "poi_facility.business_status"),
    ("数据来源", "data_source", "AMAP", "高德地图开放平台", "poi_facility.source 等"),
    ("数据来源", "data_source", "GOV", "政务开放数据", "poi_facility.source 等"),
    ("数据来源", "data_source", "MANUAL", "人工录入", "poi_facility.source 等"),
    ("变更类型", "change_type", "INSERT", "新增", "poi_change_log.change_type"),
    ("变更类型", "change_type", "UPDATE", "变更", "poi_change_log.change_type"),
    ("变更类型", "change_type", "CLOSE", "关停", "poi_change_log.change_type"),
    ("变更类型", "change_type", "INVALID", "清洗无效", "poi_change_log.change_type"),
    ("设施状态", "facility_status_cn", "充足", "设施数量充足", "assessment_facility_stat.status"),
    ("设施状态", "facility_status_cn", "基本满足", "基本满足需求", "assessment_facility_stat.status"),
    ("设施状态", "facility_status_cn", "待改善", "供给不足待改善", "assessment_facility_stat.status"),
    ("需求强度", "demand_level_cn", "高", "需求高", "site_candidate.demand_level"),
    ("需求强度", "demand_level_cn", "中高", "需求中高", "site_candidate.demand_level"),
    ("需求强度", "demand_level_cn", "中", "需求中等", "site_candidate.demand_level"),
    ("需求强度", "demand_level_cn", "低", "需求低", "site_candidate.demand_level"),
    ("竞争度", "competition_level_cn", "低", "竞争低", "site_candidate.competition_level"),
    ("竞争度", "competition_level_cn", "中", "竞争中", "site_candidate.competition_level"),
    ("竞争度", "competition_level_cn", "高", "竞争高", "site_candidate.competition_level"),
    ("缺口等级", "gap_level_cn", "高", "高缺口", "community_gap.gap_level"),
    ("缺口等级", "gap_level_cn", "中", "中缺口", "community_gap.gap_level"),
    ("缺口等级", "gap_level_cn", "低", "低缺口", "community_gap.gap_level"),
    ("意向状态", "intent_status", "SUBMITTED", "已提交", "merchant_intent.status"),
    ("意向状态", "intent_status", "MATCHED", "已匹配", "merchant_intent.status"),
    ("意向状态", "intent_status", "CONTACTED", "已对接", "merchant_intent.status"),
    ("意向状态", "intent_status", "CLOSED", "已关闭", "merchant_intent.status"),
    ("意向状态", "intent_status", "INVALID", "无效", "merchant_intent.status"),
    ("匹配状态", "match_status", "PENDING", "待对接", "merchant_match.status"),
    ("匹配状态", "match_status", "ACCEPTED", "已接受", "merchant_match.status"),
    ("匹配状态", "match_status", "REJECTED", "已拒绝", "merchant_match.status"),
    ("同步类型", "sync_type", "FULL", "全量", "sync_batch.sync_type"),
    ("同步类型", "sync_type", "INCREMENT", "增量", "sync_batch.sync_type"),
    ("批次状态", "batch_status", "RUNNING", "执行中", "sync_batch.status"),
    ("批次状态", "batch_status", "SUCCESS", "成功", "sync_batch.status"),
    ("批次状态", "batch_status", "FAILED", "失败", "sync_batch.status"),
    ("批次状态", "batch_status", "PARTIAL", "部分成功", "sync_batch.status"),
    ("质量严重度", "severity", "HIGH", "高", "data_quality_issue.severity"),
    ("质量严重度", "severity", "MEDIUM", "中", "data_quality_issue.severity"),
    ("质量严重度", "severity", "LOW", "低", "data_quality_issue.severity"),
]

# Facility dictionary seed
FACILITY_CATEGORIES = [
    ("FRESH_MARKET", "菜市场", "FRESH", "生鲜购物", 10),
    ("FRESH_SUPER", "生鲜超市", "FRESH", "生鲜购物", 20),
    ("CONVENIENCE", "便利店", "FRESH", "生鲜购物", 30),
    ("COMMUNITY_CLINIC", "社区卫生服务中心", "MEDICAL", "医疗健康", 10),
    ("PHARMACY", "药店", "MEDICAL", "医疗健康", 20),
    ("CLINIC", "社区诊所", "MEDICAL", "医疗健康", 30),
    ("KINDERGARTEN", "幼儿园", "EDU", "亲子教育", 10),
    ("NURSERY", "托育机构", "EDU", "亲子教育", 20),
    ("PRIMARY_SCHOOL", "小学", "EDU", "亲子教育", 30),
    ("BUS_STOP", "公交站", "TRAFFIC", "交通通勤", 10),
    ("METRO_STATION", "地铁站", "TRAFFIC", "交通通勤", 20),
    ("NIGHT_PHARMACY", "夜间药店", "NIGHT", "夜间服务", 10),
    ("NIGHT_STORE", "24 小时便利店", "NIGHT", "夜间服务", 20),
]

PROFILE_TAGS = [
    ("FRESH_FOOD", "生鲜买菜", "RESIDENT", "FRESH", 20),
    ("NIGHT_MEDICAL", "夜间就医", "RESIDENT", "NIGHT", 20),
    ("PARENTING", "亲子托育", "RESIDENT", "EDU", 20),
    ("COMMUTE", "通勤便利", "RESIDENT", "TRAFFIC", 20),
    ("ELDER_CARE", "老人就医", "RESIDENT", "MEDICAL", 20),
    ("LOW_RISK", "稳健投资", "MERCHANT", "COMPETITION", 30),
    ("HIGH_TRAFFIC", "高人流", "MERCHANT", "POPULATION", 35),
    ("LOW_RENT", "低租金", "MERCHANT", "RENT", 35),
]

TABLE_BY_NAME = OrderedDict((t["name"], t) for t in TABLES)
