-- ============================================================
-- 城市15分钟便民生活圈与小微开店智能助手
-- MySQL 8.0 建表脚本（V2.0，可选方言）
-- 说明：项目生产库以 Oracle 为主；本脚本用于教学/本地 MySQL 验证。
-- 字符集 utf8mb4；共 27 张表。
-- ============================================================
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE app_user (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键；自增主键',
  user_code VARCHAR(64) NOT NULL COMMENT '用户业务编号；脱敏编号，居民 R、商户 M、社区 C 前缀',
  role_code VARCHAR(20) NOT NULL DEFAULT 'RESIDENT' COMMENT '角色编码；RESIDENT 居民 / MERCHANT 商户 / COMMUNITY 社区 / ADMIN 管理员',
  nickname VARCHAR(50) COMMENT '昵称；展示名称，可为空',
  phone_hash VARCHAR(64) COMMENT '手机号哈希；SHA-256 加盐哈希，用于登录匹配，不可逆',
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '账号状态；ACTIVE/DISABLED/DELETED',
  last_login_at DATETIME(6) COMMENT '最近登录时间；UTC 时间',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_app_user_user_code (user_code),
  UNIQUE KEY uk_app_user_phone_hash (phone_hash),
  KEY idx_app_user_role_status (role_code, status),
  CONSTRAINT ck_app_user_role_code CHECK (role_code IN ('RESIDENT','MERCHANT','COMMUNITY','ADMIN')),
  CONSTRAINT ck_app_user_status CHECK (status IN ('ACTIVE','DISABLED','DELETED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户账号表：三类使用者的统一账号，只保存脱敏业务编号与手机号哈希，不落库明文手机号。';

CREATE TABLE user_profile (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  user_id BIGINT NOT NULL COMMENT '用户；所属用户',
  profile_type VARCHAR(20) NOT NULL COMMENT '画像类型；居民画像或商户画像',
  profile_label VARCHAR(50) NOT NULL COMMENT '画像标签；如“青年夜班画像”“稳健型商户画像”',
  source VARCHAR(20) NOT NULL DEFAULT 'FORM' COMMENT '生成方式；表单/多轮对话/导入',
  confidence DECIMAL(5,2) COMMENT '画像置信度；0-100，表示标签可信程度',
  version_no INT NOT NULL DEFAULT 1 COMMENT '版本号；从 1 递增',
  is_current CHAR(1) NOT NULL DEFAULT 'Y' COMMENT '是否当前版本；Y/N，同一用户仅一条 Y',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_profile_ver (user_id, version_no),
  KEY idx_user_profile_cur (user_id, is_current),
  CONSTRAINT ck_user_profile_profile_type CHECK (profile_type IN ('RESIDENT','MERCHANT')),
  CONSTRAINT ck_user_profile_source CHECK (source IN ('FORM','CHAT','IMPORT')),
  CONSTRAINT ck_user_profile_confidence CHECK (confidence BETWEEN 0 AND 100),
  CONSTRAINT ck_user_profile_is_current CHECK (is_current IN ('Y','N')),
  CONSTRAINT fk_user_profile_user_id FOREIGN KEY (user_id) REFERENCES app_user (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户画像表：一次画像生成的版本化结果，保留历史版本，is_current 标记当前生效画像。';

CREATE TABLE profile_tag (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  tag_code VARCHAR(40) NOT NULL COMMENT '标签编码；如 NIGHT_MEDICAL、FRESH_FOOD',
  tag_name VARCHAR(50) NOT NULL COMMENT '标签名称；如“夜间就医”',
  role_scope VARCHAR(20) NOT NULL DEFAULT 'ALL' COMMENT '适用角色；适用角色范围',
  dimension_code VARCHAR(30) NOT NULL COMMENT '评分维度编码；关联 FACILITY_DIMENSION 编码',
  default_weight DECIMAL(5,2) NOT NULL DEFAULT 20 COMMENT '默认权重；0-100 百分比',
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_profile_tag_tag_code (tag_code),
  KEY idx_profile_tag_dim (dimension_code, role_scope),
  CONSTRAINT ck_profile_tag_role_scope CHECK (role_scope IN ('RESIDENT','MERCHANT','ALL')),
  CONSTRAINT ck_profile_tag_default_weight CHECK (default_weight BETWEEN 0 AND 100),
  CONSTRAINT ck_profile_tag_status CHECK (status IN ('ACTIVE','INACTIVE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='画像标签字典表：可配置的关注点标签库，按角色与评分维度归类，供画像生成和权重计算使用。';

CREATE TABLE user_profile_tag (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  profile_id BIGINT NOT NULL COMMENT '画像',
  tag_id BIGINT NOT NULL COMMENT '标签',
  weight DECIMAL(5,2) NOT NULL DEFAULT 20 COMMENT '个性化权重；0-100 百分比，参与加权评分',
  selected_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '选取时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_profile_tag (profile_id, tag_id),
  CONSTRAINT ck_user_profile_tag_weight CHECK (weight BETWEEN 0 AND 100),
  CONSTRAINT fk_user_profile_tag_profile_id FOREIGN KEY (profile_id) REFERENCES user_profile (id) ON DELETE CASCADE,
  CONSTRAINT fk_user_profile_tag_tag_id FOREIGN KEY (tag_id) REFERENCES profile_tag (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户画像标签明细表：画像与标签的多对多关联，记录用户勾选/对话提取出的标签及个性化权重。';

CREATE TABLE profile_dimension_weight (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  profile_id BIGINT NOT NULL COMMENT '画像',
  dimension_code VARCHAR(30) NOT NULL COMMENT '维度编码；FRESH/MEDICAL/EDU/TRAFFIC/NIGHT',
  dimension_name VARCHAR(50) NOT NULL COMMENT '维度名称；生鲜购物/医疗健康/亲子教育/交通通勤/夜间服务',
  weight DECIMAL(5,2) NOT NULL COMMENT '维度权重；0-100 百分比',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_profile_dim (profile_id, dimension_code),
  CONSTRAINT ck_profile_dimension_weight_weight CHECK (weight BETWEEN 0 AND 100),
  CONSTRAINT fk_profile_dimension_weight_profile_id FOREIGN KEY (profile_id) REFERENCES user_profile (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='画像维度权重表：画像对五个评分维度的最终权重，居民评估时按该表动态加权，权重之和应为 100。';

CREATE TABLE district (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_code VARCHAR(40) NOT NULL COMMENT '片区编码；行政区划码+序号，全局唯一',
  district_name VARCHAR(100) NOT NULL COMMENT '片区名称',
  parent_id BIGINT COMMENT '上级片区；自关联，街道→社区→网格',
  district_level VARCHAR(20) NOT NULL COMMENT '层级；STREET/COMMUNITY/GRID',
  city_code VARCHAR(20) NOT NULL COMMENT '城市行政区划代码；GB/T 2260 六位代码',
  center_lng DECIMAL(10,6) COMMENT '中心点经度；WGS84，单位度',
  center_lat DECIMAL(10,6) COMMENT '中心点纬度；WGS84，单位度',
  boundary_geojson LONGTEXT COMMENT '边界 GeoJSON；片区边界，GeoJSON Polygon',
  area_sqm DECIMAL(12,2) COMMENT '面积；平方米',
  resident_count INT COMMENT '常住人口；人',
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_district_district_code (district_code),
  KEY idx_district_parent (parent_id),
  KEY idx_district_city (city_code, district_level),
  CONSTRAINT ck_district_district_level CHECK (district_level IN ('STREET','COMMUNITY','GRID')),
  CONSTRAINT ck_district_center_lng CHECK (center_lng BETWEEN -180 AND 180),
  CONSTRAINT ck_district_center_lat CHECK (center_lat BETWEEN -90 AND 90),
  CONSTRAINT ck_district_resident_count CHECK (resident_count >= 0),
  CONSTRAINT ck_district_status CHECK (status IN ('ACTIVE','INACTIVE')),
  CONSTRAINT fk_district_parent_id FOREIGN KEY (parent_id) REFERENCES district (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='社区片区表：街道—社区—网格三级空间主数据，是设施、评估、选址和治理的公共维度。';

CREATE TABLE population_grid (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_id BIGINT NOT NULL COMMENT '所属片区',
  grid_code VARCHAR(40) NOT NULL COMMENT '栅格编码；统一栅格编码',
  grid_level VARCHAR(20) NOT NULL DEFAULT 'GRID_250M' COMMENT '栅格精度',
  center_lng DECIMAL(10,6) NOT NULL COMMENT '栅格中心经度',
  center_lat DECIMAL(10,6) NOT NULL COMMENT '栅格中心纬度',
  population INT NOT NULL COMMENT '常住人口；人',
  density DECIMAL(12,2) COMMENT '人口密度；人/平方公里',
  data_date DATE NOT NULL COMMENT '统计日期；人口数据口径日期',
  source VARCHAR(20) NOT NULL DEFAULT 'GOV' COMMENT '数据来源',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '入库时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_pop_grid_date (grid_code, data_date),
  KEY idx_pop_district_date (district_id, data_date),
  CONSTRAINT ck_population_grid_grid_level CHECK (grid_level IN ('GRID_100M','GRID_250M','GRID_500M')),
  CONSTRAINT ck_population_grid_center_lng CHECK (center_lng BETWEEN -180 AND 180),
  CONSTRAINT ck_population_grid_center_lat CHECK (center_lat BETWEEN -90 AND 90),
  CONSTRAINT ck_population_grid_population CHECK (population >= 0),
  CONSTRAINT ck_population_grid_density CHECK (density >= 0),
  CONSTRAINT ck_population_grid_source CHECK (source IN ('GOV','AMAP','MANUAL')),
  CONSTRAINT fk_population_grid_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='人口栅格表：按栅格与统计日期保存常住人口和密度，是商户选址人口指数与社区覆盖测算的输入。';

CREATE TABLE road_node (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  node_code VARCHAR(40) NOT NULL COMMENT '节点编码',
  district_id BIGINT COMMENT '所属片区',
  lng DECIMAL(10,6) NOT NULL COMMENT '经度',
  lat DECIMAL(10,6) NOT NULL COMMENT '纬度',
  node_type VARCHAR(20) NOT NULL DEFAULT 'INTERSECTION' COMMENT '节点类型',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_road_node_node_code (node_code),
  KEY idx_road_node_district (district_id),
  CONSTRAINT ck_road_node_lng CHECK (lng BETWEEN -180 AND 180),
  CONSTRAINT ck_road_node_lat CHECK (lat BETWEEN -90 AND 90),
  CONSTRAINT ck_road_node_node_type CHECK (node_type IN ('INTERSECTION','ENTRANCE','CROSSING')),
  CONSTRAINT fk_road_node_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='路网节点表：步行路网拓扑节点（路口、小区出入口、过街设施），用于 15 分钟步行可达计算。';

CREATE TABLE road_segment (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  segment_code VARCHAR(50) NOT NULL COMMENT '路段编码',
  district_id BIGINT COMMENT '所属片区',
  from_node_id BIGINT NOT NULL COMMENT '起点节点',
  to_node_id BIGINT NOT NULL COMMENT '终点节点',
  road_name VARCHAR(100) COMMENT '道路名称',
  road_level VARCHAR(20) NOT NULL DEFAULT 'BRANCH' COMMENT '道路等级',
  length_m DECIMAL(10,2) NOT NULL COMMENT '路段长度；米',
  walk_time_s INT NOT NULL COMMENT '步行耗时；秒，按 1.2 m/s 及过街等待估算',
  is_walkable CHAR(1) NOT NULL DEFAULT 'Y' COMMENT '是否可步行',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_road_segment_segment_code (segment_code),
  KEY idx_road_seg_from (from_node_id),
  KEY idx_road_seg_to (to_node_id),
  KEY idx_road_seg_district (district_id),
  CONSTRAINT ck_road_segment_road_level CHECK (road_level IN ('MAIN','BRANCH','ALLEY')),
  CONSTRAINT ck_road_segment_length_m CHECK (length_m > 0),
  CONSTRAINT ck_road_segment_walk_time_s CHECK (walk_time_s > 0),
  CONSTRAINT ck_road_segment_is_walkable CHECK (is_walkable IN ('Y','N')),
  CONSTRAINT fk_road_segment_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE SET NULL,
  CONSTRAINT fk_road_segment_from_node_id FOREIGN KEY (from_node_id) REFERENCES road_node (id) ON DELETE RESTRICT,
  CONSTRAINT fk_road_segment_to_node_id FOREIGN KEY (to_node_id) REFERENCES road_node (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='路网步行段表：连接两个路网节点的步行段，保存长度与步行耗时，构成 15 分钟等时圈的图结构。';

CREATE TABLE facility_category (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  category_code VARCHAR(40) NOT NULL COMMENT '类别编码；如 FRESH_MARKET、CLINIC',
  category_name VARCHAR(50) NOT NULL COMMENT '类别名称；如“社区诊所”',
  dimension_code VARCHAR(30) NOT NULL COMMENT '评分维度编码；FRESH/MEDICAL/EDU/TRAFFIC/NIGHT',
  dimension_name VARCHAR(50) NOT NULL COMMENT '评分维度名称',
  icon VARCHAR(100) COMMENT '图标标识；前端图标名',
  sort_no INT NOT NULL DEFAULT 0 COMMENT '排序号',
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_facility_category_category_code (category_code),
  KEY idx_fac_category_dim (dimension_code, sort_no),
  CONSTRAINT ck_facility_category_status CHECK (status IN ('ACTIVE','INACTIVE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='设施类别字典表：POI 类别与五维评分的映射字典，统一高德分类与业务维度，避免代码硬编码。';

CREATE TABLE poi_facility (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_id BIGINT NOT NULL COMMENT '所属片区',
  category_id BIGINT NOT NULL COMMENT '设施类别',
  poi_name VARCHAR(200) NOT NULL COMMENT '设施名称',
  lng DECIMAL(10,6) NOT NULL COMMENT '经度',
  lat DECIMAL(10,6) NOT NULL COMMENT '纬度',
  address VARCHAR(255) COMMENT '详细地址',
  business_status VARCHAR(20) NOT NULL DEFAULT 'OPEN' COMMENT '营业状态',
  source VARCHAR(20) NOT NULL COMMENT '数据来源',
  source_poi_id VARCHAR(100) NOT NULL COMMENT '来源 POI 编号；高德 POI ID 或政务数据主键，用于增量去重',
  telephone VARCHAR(50) COMMENT '公开电话；仅公共设施公开电话，不含个人信息',
  first_seen_at DATETIME(6) NOT NULL COMMENT '首次发现时间',
  last_seen_at DATETIME(6) NOT NULL COMMENT '最近发现时间',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  is_valid CHAR(1) NOT NULL DEFAULT 'Y' COMMENT '是否有效',
  PRIMARY KEY (id),
  UNIQUE KEY uk_poi_source (source, source_poi_id),
  KEY idx_poi_district_cat (district_id, category_id),
  KEY idx_poi_category (category_id, is_valid),
  KEY idx_poi_name (poi_name),
  CONSTRAINT ck_poi_facility_lng CHECK (lng BETWEEN -180 AND 180),
  CONSTRAINT ck_poi_facility_lat CHECK (lat BETWEEN -90 AND 90),
  CONSTRAINT ck_poi_facility_business_status CHECK (business_status IN ('OPEN','CLOSED','MOVED','UNKNOWN')),
  CONSTRAINT ck_poi_facility_source CHECK (source IN ('AMAP','GOV','MANUAL')),
  CONSTRAINT ck_poi_facility_is_valid CHECK (is_valid IN ('Y','N')),
  CONSTRAINT fk_poi_facility_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE RESTRICT,
  CONSTRAINT fk_poi_facility_category_id FOREIGN KEY (category_id) REFERENCES facility_category (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='设施网点 POI 表：社区周边生鲜、医疗、教育、交通、夜间服务等设施网点，是评估与选址的主数据。';

CREATE TABLE sync_batch (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  batch_no VARCHAR(40) NOT NULL COMMENT '批次号；如 POI-20261015-01',
  data_source VARCHAR(20) NOT NULL COMMENT '数据来源',
  sync_type VARCHAR(20) NOT NULL COMMENT '同步类型',
  started_at DATETIME(6) NOT NULL COMMENT '开始时间',
  finished_at DATETIME(6) COMMENT '结束时间',
  total_count INT NOT NULL DEFAULT 0 COMMENT '处理总数',
  insert_count INT NOT NULL DEFAULT 0 COMMENT '新增数',
  update_count INT NOT NULL DEFAULT 0 COMMENT '变更数',
  close_count INT NOT NULL DEFAULT 0 COMMENT '关停数',
  invalid_count INT NOT NULL DEFAULT 0 COMMENT '无效数',
  status VARCHAR(20) NOT NULL DEFAULT 'RUNNING' COMMENT '批次状态',
  error_msg VARCHAR(1000) COMMENT '错误信息',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_sync_batch_batch_no (batch_no),
  KEY idx_sync_status_time (status, started_at),
  CONSTRAINT ck_sync_batch_data_source CHECK (data_source IN ('AMAP','GOV','MANUAL')),
  CONSTRAINT ck_sync_batch_sync_type CHECK (sync_type IN ('FULL','INCREMENT')),
  CONSTRAINT ck_sync_batch_total_count CHECK (total_count >= 0),
  CONSTRAINT ck_sync_batch_status CHECK (status IN ('RUNNING','SUCCESS','FAILED','PARTIAL'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据同步批次表：每半月一次 POI/人口/路网增量同步的批次台账，记录数量、状态与错误信息。';

CREATE TABLE poi_change_log (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  poi_id BIGINT COMMENT '设施',
  batch_id BIGINT NOT NULL COMMENT '同步批次',
  change_type VARCHAR(20) NOT NULL COMMENT '变更类型',
  change_summary VARCHAR(500) COMMENT '变更摘要；如“地址变更”“营业状态 OPEN→CLOSED”',
  before_json LONGTEXT COMMENT '变更前数据；JSON 快照，便于回滚',
  after_json LONGTEXT COMMENT '变更后数据；JSON 快照',
  changed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '变更时间',
  PRIMARY KEY (id),
  KEY idx_poi_log_poi (poi_id, changed_at),
  KEY idx_poi_log_batch (batch_id),
  CONSTRAINT ck_poi_change_log_change_type CHECK (change_type IN ('INSERT','UPDATE','CLOSE','INVALID')),
  CONSTRAINT fk_poi_change_log_poi_id FOREIGN KEY (poi_id) REFERENCES poi_facility (id) ON DELETE SET NULL,
  CONSTRAINT fk_poi_change_log_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='POI 变更日志表：记录新增、变更、关停和清洗无效的 POI 差异，支持增量追溯与数据质量审计。';

CREATE TABLE resident_assessment (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  resident_code VARCHAR(64) NOT NULL COMMENT '居民编号；脱敏居民编号，未登录用户也可评估',
  user_id BIGINT COMMENT '用户',
  district_id BIGINT NOT NULL COMMENT '目标片区',
  profile_id BIGINT COMMENT '画像版本；个性化权重来源',
  batch_id BIGINT COMMENT '数据批次；评估使用的 POI/人口数据版本',
  radius_m INT NOT NULL DEFAULT 1080 COMMENT '步行半径；米，15 分钟按 1.2 m/s 约 1080 m',
  total_score INT NOT NULL COMMENT '综合评分；0-100',
  profile_label VARCHAR(50) COMMENT '画像标签；冗余画像标签，便于列表展示',
  insight VARCHAR(1000) COMMENT '诊断建议；Agent 生成的优缺点诊断',
  assessed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '评估时间',
  PRIMARY KEY (id),
  KEY idx_assess_district_time (district_id, assessed_at),
  KEY idx_assess_user (user_id, assessed_at),
  KEY idx_assess_batch (batch_id),
  CONSTRAINT ck_resident_assessment_radius_m CHECK (radius_m BETWEEN 100 AND 3000),
  CONSTRAINT ck_resident_assessment_total_score CHECK (total_score BETWEEN 0 AND 100),
  CONSTRAINT fk_resident_assessment_user_id FOREIGN KEY (user_id) REFERENCES app_user (id) ON DELETE SET NULL,
  CONSTRAINT fk_resident_assessment_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE RESTRICT,
  CONSTRAINT fk_resident_assessment_profile_id FOREIGN KEY (profile_id) REFERENCES user_profile (id) ON DELETE SET NULL,
  CONSTRAINT fk_resident_assessment_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='居民生活圈评估表：一次居民生活圈体检的汇总结果，保存评分、画像、步行半径和诊断结论。';

CREATE TABLE assessment_dimension (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  assessment_id BIGINT NOT NULL COMMENT '评估记录',
  dimension_code VARCHAR(30) NOT NULL COMMENT '维度编码',
  dimension_name VARCHAR(50) NOT NULL COMMENT '维度名称',
  dimension_score INT NOT NULL COMMENT '维度得分',
  weight DECIMAL(5,2) NOT NULL COMMENT '维度权重；来自画像，百分比',
  facility_count INT NOT NULL DEFAULT 0 COMMENT '设施数量',
  PRIMARY KEY (id),
  UNIQUE KEY uk_assess_dim (assessment_id, dimension_code),
  CONSTRAINT ck_assessment_dimension_dimension_score CHECK (dimension_score BETWEEN 0 AND 100),
  CONSTRAINT ck_assessment_dimension_weight CHECK (weight BETWEEN 0 AND 100),
  CONSTRAINT ck_assessment_dimension_facility_count CHECK (facility_count >= 0),
  CONSTRAINT fk_assessment_dimension_assessment_id FOREIGN KEY (assessment_id) REFERENCES resident_assessment (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='评估维度得分表：五维评分的分项结果，保存得分、权重和设施计数，支撑雷达图与可解释性。';

CREATE TABLE assessment_facility_stat (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  assessment_id BIGINT NOT NULL COMMENT '评估记录',
  category_id BIGINT NOT NULL COMMENT '设施类别',
  facility_count INT NOT NULL DEFAULT 0 COMMENT '设施数量',
  nearest_distance_m DECIMAL(10,2) COMMENT '最近距离；米',
  status VARCHAR(20) COMMENT '设施状态；充足/基本满足/待改善，与前端枚举逐字一致',
  PRIMARY KEY (id),
  UNIQUE KEY uk_assess_category (assessment_id, category_id),
  CONSTRAINT ck_assessment_facility_stat_facility_count CHECK (facility_count >= 0),
  CONSTRAINT ck_assessment_facility_stat_nearest_distance_m CHECK (nearest_distance_m >= 0),
  CONSTRAINT fk_assessment_facility_stat_assessment_id FOREIGN KEY (assessment_id) REFERENCES resident_assessment (id) ON DELETE CASCADE,
  CONSTRAINT fk_assessment_facility_stat_category_id FOREIGN KEY (category_id) REFERENCES facility_category (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='评估设施盘点表：一次评估中各设施类别的数量、最近距离与状态，用于设施清单和短板定位。';

CREATE TABLE district_score_snapshot (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_id BIGINT NOT NULL COMMENT '片区',
  batch_id BIGINT COMMENT '数据批次',
  coverage_pct INT NOT NULL COMMENT '覆盖率；%，15 分钟覆盖人口占比',
  avg_score DECIMAL(5,2) NOT NULL COMMENT '平均评分',
  rank_no INT COMMENT '辖区排名',
  resident_count INT COMMENT '覆盖人口',
  scored_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '计算时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_district_batch (district_id, batch_id),
  KEY idx_district_score_time (scored_at),
  CONSTRAINT ck_district_score_snapshot_coverage_pct CHECK (coverage_pct BETWEEN 0 AND 100),
  CONSTRAINT ck_district_score_snapshot_avg_score CHECK (avg_score BETWEEN 0 AND 100),
  CONSTRAINT ck_district_score_snapshot_rank_no CHECK (rank_no > 0),
  CONSTRAINT ck_district_score_snapshot_resident_count CHECK (resident_count >= 0),
  CONSTRAINT fk_district_score_snapshot_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE CASCADE,
  CONSTRAINT fk_district_score_snapshot_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='片区评分快照表：每次数据同步后按片区重算的便民评分与排名，供社区热力图、排名和趋势查询。';

CREATE TABLE site_candidate (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_id BIGINT NOT NULL COMMENT '所属片区',
  batch_id BIGINT COMMENT '数据批次',
  candidate_name VARCHAR(100) NOT NULL COMMENT '候选点名称；如“东园路口”',
  business_type VARCHAR(100) COMMENT '经营业态；早餐、便利店、托育、药店等',
  lng DECIMAL(10,6) COMMENT '经度',
  lat DECIMAL(10,6) COMMENT '纬度',
  population_index DECIMAL(10,2) COMMENT '人口指数；候选项半径内人口/密度综合指数',
  competitor_count INT COMMENT '同业态竞争数；候选点 15 分钟范围内同业态 POI 数',
  demand_level VARCHAR(10) COMMENT '需求强度；高/中高/中/低',
  competition_level VARCHAR(10) COMMENT '竞争度；低/中/高',
  rent_min DECIMAL(8,2) COMMENT '租金下限；万元/年',
  rent_max DECIMAL(8,2) COMMENT '租金上限；万元/年',
  site_score INT COMMENT '选址评分',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '生成时间',
  PRIMARY KEY (id),
  KEY idx_site_district_type (district_id, business_type, site_score),
  KEY idx_site_batch (batch_id),
  CONSTRAINT ck_site_candidate_lng CHECK (lng BETWEEN -180 AND 180),
  CONSTRAINT ck_site_candidate_lat CHECK (lat BETWEEN -90 AND 90),
  CONSTRAINT ck_site_candidate_population_index CHECK (population_index >= 0),
  CONSTRAINT ck_site_candidate_competitor_count CHECK (competitor_count >= 0),
  CONSTRAINT ck_site_candidate_rent_min CHECK (rent_min >= 0),
  CONSTRAINT ck_site_candidate_rent_max CHECK (rent_max >= 0),
  CONSTRAINT ck_site_candidate_site_score CHECK (site_score BETWEEN 0 AND 100),
  CONSTRAINT ck_site_rent CHECK (rent_min IS NULL OR rent_max IS NULL OR rent_min <= rent_max),
  CONSTRAINT fk_site_candidate_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE RESTRICT,
  CONSTRAINT fk_site_candidate_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商户选址候选点表：Agent 依据人口栅格与同业态竞争 POI 推演出的候选点位，含评分与关键指标。';

CREATE TABLE site_score_item (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  candidate_id BIGINT NOT NULL COMMENT '候选点',
  score_item VARCHAR(50) NOT NULL COMMENT '评分项；人口密度/竞争饱和度/租金/交通/设施缺口',
  item_score DECIMAL(5,2) NOT NULL COMMENT '得分',
  weight DECIMAL(5,2) NOT NULL COMMENT '权重',
  reason VARCHAR(255) COMMENT '评分理由；给商户看的解释文本',
  PRIMARY KEY (id),
  UNIQUE KEY uk_site_score_item (candidate_id, score_item),
  CONSTRAINT ck_site_score_item_item_score CHECK (item_score BETWEEN 0 AND 100),
  CONSTRAINT ck_site_score_item_weight CHECK (weight BETWEEN 0 AND 100),
  CONSTRAINT fk_site_score_item_candidate_id FOREIGN KEY (candidate_id) REFERENCES site_candidate (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='选址评分明细表：候选点各评分项的分值、权重与理由，保证选址推荐可解释、可复核。';

CREATE TABLE merchant_intent (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  merchant_name VARCHAR(100) NOT NULL COMMENT '商户名称',
  business_type VARCHAR(100) NOT NULL COMMENT '经营业态',
  contact VARCHAR(200) NOT NULL COMMENT '联系方式密文；AES-256-GCM 加密后 Base64，禁止明文落库；接口层解密',
  contact_masked VARCHAR(20) COMMENT '联系方式脱敏；如 138****8000，列表展示用',
  district_id BIGINT COMMENT '意向片区',
  candidate_id BIGINT COMMENT '意向候选点',
  budget_min DECIMAL(8,2) COMMENT '预算下限；万元',
  budget_max DECIMAL(8,2) COMMENT '预算上限；万元',
  area_sqm DECIMAL(8,2) COMMENT '经营面积；平方米',
  remark VARCHAR(500) COMMENT '经营说明',
  status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED' COMMENT '意向状态',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_intent_status_time (status, created_at),
  KEY idx_intent_district (district_id),
  KEY idx_intent_candidate (candidate_id),
  CONSTRAINT ck_merchant_intent_budget_min CHECK (budget_min >= 0),
  CONSTRAINT ck_merchant_intent_budget_max CHECK (budget_max >= 0),
  CONSTRAINT ck_merchant_intent_area_sqm CHECK (area_sqm > 0),
  CONSTRAINT ck_merchant_intent_status CHECK (status IN ('SUBMITTED','MATCHED','CONTACTED','CLOSED','INVALID')),
  CONSTRAINT ck_intent_budget CHECK (budget_min IS NULL OR budget_max IS NULL OR budget_min <= budget_max),
  CONSTRAINT fk_merchant_intent_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE SET NULL,
  CONSTRAINT fk_merchant_intent_candidate_id FOREIGN KEY (candidate_id) REFERENCES site_candidate (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商户开店意向表：商户提交的开店意向，保留原有字段并扩展片区、候选点、预算和状态，兼容现有接口。';

CREATE TABLE community_gap (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_id BIGINT NOT NULL COMMENT '片区',
  category_id BIGINT NOT NULL COMMENT '设施类别',
  area_name VARCHAR(100) NOT NULL COMMENT '短板区域名称',
  issue VARCHAR(200) NOT NULL COMMENT '短板描述；如“夜间就医距离较远”',
  gap_level VARCHAR(10) NOT NULL COMMENT '缺口等级；高/中/低，与前端枚举一致',
  uncovered_residents INT COMMENT '未覆盖人口；人',
  priority_no INT COMMENT '改造优先级；1 为最高',
  batch_id BIGINT COMMENT '数据批次',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_gap_district_level (district_id, gap_level),
  KEY idx_gap_category (category_id),
  KEY idx_gap_batch (batch_id),
  CONSTRAINT ck_community_gap_uncovered_residents CHECK (uncovered_residents >= 0),
  CONSTRAINT ck_community_gap_priority_no CHECK (priority_no > 0),
  CONSTRAINT fk_community_gap_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE CASCADE,
  CONSTRAINT fk_community_gap_category_id FOREIGN KEY (category_id) REFERENCES facility_category (id) ON DELETE RESTRICT,
  CONSTRAINT fk_community_gap_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='社区短板片区表：社区识别出的买菜难、就医远、托育不足等短板，含缺口等级、未覆盖人口与优先级。';

CREATE TABLE merchant_match (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  intent_id BIGINT NOT NULL COMMENT '开店意向',
  district_id BIGINT NOT NULL COMMENT '片区',
  gap_id BIGINT COMMENT '对应短板',
  fit_score INT NOT NULL COMMENT '匹配度',
  match_reason VARCHAR(500) COMMENT '匹配理由',
  status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '对接状态',
  matched_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '匹配时间',
  PRIMARY KEY (id),
  KEY idx_match_intent (intent_id),
  KEY idx_match_gap (gap_id),
  KEY idx_match_district_score (district_id, fit_score),
  CONSTRAINT ck_merchant_match_fit_score CHECK (fit_score BETWEEN 0 AND 100),
  CONSTRAINT ck_merchant_match_status CHECK (status IN ('PENDING','ACCEPTED','REJECTED')),
  CONSTRAINT fk_merchant_match_intent_id FOREIGN KEY (intent_id) REFERENCES merchant_intent (id) ON DELETE CASCADE,
  CONSTRAINT fk_merchant_match_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE RESTRICT,
  CONSTRAINT fk_merchant_match_gap_id FOREIGN KEY (gap_id) REFERENCES community_gap (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='招商匹配表：社区短板与商户意向的双向匹配结果，记录匹配分、理由和对接状态。';

CREATE TABLE simulation_record (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  district_id BIGINT NOT NULL COMMENT '片区',
  category_id BIGINT NOT NULL COMMENT '设施类别',
  business_type VARCHAR(100) COMMENT '模拟业态',
  lng DECIMAL(10,6) COMMENT '模拟点经度',
  lat DECIMAL(10,6) COMMENT '模拟点纬度',
  before_coverage INT NOT NULL COMMENT '模拟前覆盖率；%',
  after_coverage INT NOT NULL COMMENT '模拟后覆盖率；%',
  benefited_residents INT NOT NULL COMMENT '受益人口',
  operator VARCHAR(50) COMMENT '操作人；社区工作人员编号',
  simulated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '模拟时间',
  PRIMARY KEY (id),
  KEY idx_sim_district_time (district_id, simulated_at),
  CONSTRAINT ck_simulation_record_lng CHECK (lng BETWEEN -180 AND 180),
  CONSTRAINT ck_simulation_record_lat CHECK (lat BETWEEN -90 AND 90),
  CONSTRAINT ck_simulation_record_before_coverage CHECK (before_coverage BETWEEN 0 AND 100),
  CONSTRAINT ck_simulation_record_after_coverage CHECK (after_coverage BETWEEN 0 AND 100),
  CONSTRAINT ck_simulation_record_benefited_residents CHECK (benefited_residents >= 0),
  CONSTRAINT fk_simulation_record_district_id FOREIGN KEY (district_id) REFERENCES district (id) ON DELETE CASCADE,
  CONSTRAINT fk_simulation_record_category_id FOREIGN KEY (category_id) REFERENCES facility_category (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='网点增设模拟记录表：社区在地图上模拟新增便民网点后的覆盖率、受益人口和前后对比，支撑改造决策。';

CREATE TABLE data_quality_issue (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  batch_id BIGINT NOT NULL COMMENT '同步批次',
  poi_id BIGINT COMMENT '设施',
  rule_code VARCHAR(40) NOT NULL COMMENT '校验规则编码；如 DUP_POI、COORD_OUT_OF_RANGE',
  issue_desc VARCHAR(500) NOT NULL COMMENT '问题描述',
  severity VARCHAR(20) NOT NULL COMMENT '严重程度',
  is_handled CHAR(1) NOT NULL DEFAULT 'N' COMMENT '是否已处理',
  handled_at DATETIME(6) COMMENT '处理时间',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_dq_batch_severity (batch_id, severity, is_handled),
  CONSTRAINT ck_data_quality_issue_severity CHECK (severity IN ('HIGH','MEDIUM','LOW')),
  CONSTRAINT ck_data_quality_issue_is_handled CHECK (is_handled IN ('Y','N')),
  CONSTRAINT fk_data_quality_issue_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE CASCADE,
  CONSTRAINT fk_data_quality_issue_poi_id FOREIGN KEY (poi_id) REFERENCES poi_facility (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据质量问题表：同步过程中的重复、坐标异常、类别缺失等质量问题及处理状态，支撑数据治理闭环。';

CREATE TABLE ods_poi_raw (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  batch_id BIGINT NOT NULL COMMENT '同步批次',
  source VARCHAR(20) NOT NULL COMMENT '数据来源',
  source_poi_id VARCHAR(100) NOT NULL COMMENT '来源 POI 编号',
  poi_name VARCHAR(200) COMMENT '设施名称',
  lng DECIMAL(10,6) COMMENT '经度',
  lat DECIMAL(10,6) COMMENT '纬度',
  category_raw VARCHAR(100) COMMENT '原始类别',
  address VARCHAR(255) COMMENT '原始地址',
  raw_json LONGTEXT NOT NULL COMMENT '原始报文；接口返回 JSON 原样保存',
  load_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '入库时间',
  process_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '处理状态',
  PRIMARY KEY (id),
  KEY idx_ods_poi_batch (batch_id, process_status),
  KEY idx_ods_poi_source (source, source_poi_id),
  CONSTRAINT ck_ods_poi_raw_source CHECK (source IN ('AMAP','GOV','MANUAL')),
  CONSTRAINT ck_ods_poi_raw_process_status CHECK (process_status IN ('PENDING','PROCESSED','REJECTED')),
  CONSTRAINT fk_ods_poi_raw_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='POI 原始数据表：高德/政务 POI 接口原始报文落地，保留原样 JSON，供清洗、重放和审计。';

CREATE TABLE ods_population_raw (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  batch_id BIGINT NOT NULL COMMENT '同步批次',
  grid_code VARCHAR(40) NOT NULL COMMENT '栅格编码',
  population INT COMMENT '人口数',
  density DECIMAL(12,2) COMMENT '人口密度',
  data_date DATE COMMENT '统计日期',
  raw_json LONGTEXT NOT NULL COMMENT '原始报文',
  load_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '入库时间',
  process_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '处理状态',
  PRIMARY KEY (id),
  KEY idx_ods_pop_batch (batch_id, process_status),
  CONSTRAINT ck_ods_population_raw_population CHECK (population >= 0),
  CONSTRAINT ck_ods_population_raw_density CHECK (density >= 0),
  CONSTRAINT ck_ods_population_raw_process_status CHECK (process_status IN ('PENDING','PROCESSED','REJECTED')),
  CONSTRAINT fk_ods_population_raw_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='人口栅格原始数据表：人口栅格文件/接口的原始统计值，按批次保留，供复算和口径追溯。';

CREATE TABLE ods_road_raw (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  batch_id BIGINT NOT NULL COMMENT '同步批次',
  segment_code VARCHAR(50) COMMENT '路段编码',
  raw_json LONGTEXT NOT NULL COMMENT '原始报文',
  load_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '入库时间',
  process_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '处理状态',
  PRIMARY KEY (id),
  KEY idx_ods_road_batch (batch_id, process_status),
  CONSTRAINT ck_ods_road_raw_process_status CHECK (process_status IN ('PENDING','PROCESSED','REJECTED')),
  CONSTRAINT fk_ods_road_raw_batch_id FOREIGN KEY (batch_id) REFERENCES sync_batch (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='路网原始数据表：路网数据文件的原始路段记录，保留几何与属性原文，供拓扑重建。';

SET FOREIGN_KEY_CHECKS = 1;
