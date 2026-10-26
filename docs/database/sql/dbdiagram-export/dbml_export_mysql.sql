CREATE TABLE `app_user` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '自增主键',
  `user_code` varchar(64) UNIQUE NOT NULL COMMENT '脱敏编号，居民 R、商户 M、社区 C 前缀',
  `role_code` varchar(20) NOT NULL DEFAULT 'RESIDENT' COMMENT 'RESIDENT 居民 / MERCHANT 商户 / COMMUNITY 社区 / ADMIN 管理员',
  `nickname` varchar(50) COMMENT '展示名称，可为空',
  `phone_hash` varchar(64) UNIQUE COMMENT 'SHA-256 加盐哈希，用于登录匹配，不可逆',
  `status` varchar(20) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/DISABLED/DELETED',
  `last_login_at` timestamp COMMENT 'UTC 时间',
  `created_at` timestamp NOT NULL COMMENT '创建时间',
  `updated_at` timestamp NOT NULL COMMENT '更新时间'
);

CREATE TABLE `user_profile` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint NOT NULL COMMENT '所属用户',
  `profile_type` varchar(20) NOT NULL COMMENT '居民画像或商户画像',
  `profile_label` varchar(50) NOT NULL COMMENT '如“青年夜班画像”“稳健型商户画像”',
  `source` varchar(20) NOT NULL DEFAULT 'FORM' COMMENT '表单/多轮对话/导入',
  `confidence` decimal(5,2) COMMENT '0-100，表示标签可信程度',
  `version_no` int NOT NULL DEFAULT 1 COMMENT '从 1 递增',
  `is_current` char(1) NOT NULL DEFAULT 'Y' COMMENT 'Y/N，同一用户仅一条 Y',
  `created_at` timestamp NOT NULL COMMENT '创建时间'
);

CREATE TABLE `profile_tag` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `tag_code` varchar(40) UNIQUE NOT NULL COMMENT '如 NIGHT_MEDICAL、FRESH_FOOD',
  `tag_name` varchar(50) NOT NULL COMMENT '如“夜间就医”',
  `role_scope` varchar(20) NOT NULL DEFAULT 'ALL' COMMENT '适用角色范围',
  `dimension_code` varchar(30) NOT NULL COMMENT '关联 FACILITY_DIMENSION 编码',
  `default_weight` decimal(5,2) NOT NULL DEFAULT 20 COMMENT '0-100 百分比',
  `status` varchar(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  `created_at` timestamp NOT NULL COMMENT '创建时间'
);

CREATE TABLE `user_profile_tag` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `profile_id` bigint NOT NULL COMMENT '画像',
  `tag_id` bigint NOT NULL COMMENT '标签',
  `weight` decimal(5,2) NOT NULL DEFAULT 20 COMMENT '0-100 百分比，参与加权评分',
  `selected_at` timestamp NOT NULL COMMENT '选取时间'
);

CREATE TABLE `profile_dimension_weight` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `profile_id` bigint NOT NULL COMMENT '画像',
  `dimension_code` varchar(30) NOT NULL COMMENT 'FRESH/MEDICAL/EDU/TRAFFIC/NIGHT',
  `dimension_name` varchar(50) NOT NULL COMMENT '生鲜购物/医疗健康/亲子教育/交通通勤/夜间服务',
  `weight` decimal(5,2) NOT NULL COMMENT '0-100 百分比',
  `updated_at` timestamp NOT NULL COMMENT '更新时间'
);

CREATE TABLE `district` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_code` varchar(40) UNIQUE NOT NULL COMMENT '行政区划码+序号，全局唯一',
  `district_name` varchar(100) NOT NULL COMMENT '片区名称',
  `parent_id` bigint COMMENT '自关联，街道→社区→网格',
  `district_level` varchar(20) NOT NULL COMMENT 'STREET/COMMUNITY/GRID',
  `city_code` varchar(20) NOT NULL COMMENT 'GB/T 2260 六位代码',
  `center_lng` decimal(10,6) COMMENT 'WGS84，单位度',
  `center_lat` decimal(10,6) COMMENT 'WGS84，单位度',
  `boundary_geojson` text COMMENT '片区边界，GeoJSON Polygon',
  `area_sqm` decimal(12,2) COMMENT '平方米',
  `resident_count` int COMMENT '人',
  `status` varchar(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  `created_at` timestamp NOT NULL COMMENT '创建时间',
  `updated_at` timestamp NOT NULL COMMENT '更新时间'
);

CREATE TABLE `population_grid` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_id` bigint NOT NULL COMMENT '所属片区',
  `grid_code` varchar(40) NOT NULL COMMENT '统一栅格编码',
  `grid_level` varchar(20) NOT NULL DEFAULT 'GRID_250M' COMMENT '栅格精度',
  `center_lng` decimal(10,6) NOT NULL COMMENT '栅格中心经度',
  `center_lat` decimal(10,6) NOT NULL COMMENT '栅格中心纬度',
  `population` int NOT NULL COMMENT '人',
  `density` decimal(12,2) COMMENT '人/平方公里',
  `data_date` date NOT NULL COMMENT '人口数据口径日期',
  `source` varchar(20) NOT NULL DEFAULT 'GOV' COMMENT '数据来源',
  `created_at` timestamp NOT NULL COMMENT '入库时间'
);

CREATE TABLE `road_node` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `node_code` varchar(40) UNIQUE NOT NULL COMMENT '节点编码',
  `district_id` bigint COMMENT '所属片区',
  `lng` decimal(10,6) NOT NULL COMMENT '经度',
  `lat` decimal(10,6) NOT NULL COMMENT '纬度',
  `node_type` varchar(20) NOT NULL DEFAULT 'INTERSECTION' COMMENT '节点类型',
  `updated_at` timestamp NOT NULL COMMENT '更新时间'
);

CREATE TABLE `road_segment` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `segment_code` varchar(50) UNIQUE NOT NULL COMMENT '路段编码',
  `district_id` bigint COMMENT '所属片区',
  `from_node_id` bigint NOT NULL COMMENT '起点节点',
  `to_node_id` bigint NOT NULL COMMENT '终点节点',
  `road_name` varchar(100) COMMENT '道路名称',
  `road_level` varchar(20) NOT NULL DEFAULT 'BRANCH' COMMENT '道路等级',
  `length_m` decimal(10,2) NOT NULL COMMENT '米',
  `walk_time_s` int NOT NULL COMMENT '秒，按 1.2 m/s 及过街等待估算',
  `is_walkable` char(1) NOT NULL DEFAULT 'Y' COMMENT '是否可步行',
  `updated_at` timestamp NOT NULL COMMENT '更新时间'
);

CREATE TABLE `facility_category` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `category_code` varchar(40) UNIQUE NOT NULL COMMENT '如 FRESH_MARKET、CLINIC',
  `category_name` varchar(50) NOT NULL COMMENT '如“社区诊所”',
  `dimension_code` varchar(30) NOT NULL COMMENT 'FRESH/MEDICAL/EDU/TRAFFIC/NIGHT',
  `dimension_name` varchar(50) NOT NULL COMMENT '评分维度名称',
  `icon` varchar(100) COMMENT '前端图标名',
  `sort_no` int NOT NULL DEFAULT 0 COMMENT '排序号',
  `status` varchar(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  `created_at` timestamp NOT NULL COMMENT '创建时间'
);

CREATE TABLE `poi_facility` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_id` bigint NOT NULL COMMENT '所属片区',
  `category_id` bigint NOT NULL COMMENT '设施类别',
  `poi_name` varchar(200) NOT NULL COMMENT '设施名称',
  `lng` decimal(10,6) NOT NULL COMMENT '经度',
  `lat` decimal(10,6) NOT NULL COMMENT '纬度',
  `address` varchar(255) COMMENT '详细地址',
  `business_status` varchar(20) NOT NULL DEFAULT 'OPEN' COMMENT '营业状态',
  `source` varchar(20) NOT NULL COMMENT '数据来源',
  `source_poi_id` varchar(100) NOT NULL COMMENT '高德 POI ID 或政务数据主键，用于增量去重',
  `telephone` varchar(50) COMMENT '仅公共设施公开电话，不含个人信息',
  `first_seen_at` timestamp NOT NULL COMMENT '首次发现时间',
  `last_seen_at` timestamp NOT NULL COMMENT '最近发现时间',
  `updated_at` timestamp NOT NULL COMMENT '更新时间',
  `is_valid` char(1) NOT NULL DEFAULT 'Y' COMMENT '是否有效'
);

CREATE TABLE `poi_change_log` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `poi_id` bigint COMMENT '设施',
  `batch_id` bigint NOT NULL COMMENT '同步批次',
  `change_type` varchar(20) NOT NULL COMMENT '变更类型',
  `change_summary` varchar(500) COMMENT '如“地址变更”“营业状态 OPEN→CLOSED”',
  `before_json` text COMMENT 'JSON 快照，便于回滚',
  `after_json` text COMMENT 'JSON 快照',
  `changed_at` timestamp NOT NULL COMMENT '变更时间'
);

CREATE TABLE `resident_assessment` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `resident_code` varchar(64) NOT NULL COMMENT '脱敏居民编号，未登录用户也可评估',
  `user_id` bigint COMMENT '用户',
  `district_id` bigint NOT NULL COMMENT '目标片区',
  `profile_id` bigint COMMENT '个性化权重来源',
  `batch_id` bigint COMMENT '评估使用的 POI/人口数据版本',
  `radius_m` int NOT NULL DEFAULT 1080 COMMENT '米，15 分钟按 1.2 m/s 约 1080 m',
  `total_score` int NOT NULL COMMENT '0-100',
  `profile_label` varchar(50) COMMENT '冗余画像标签，便于列表展示',
  `insight` varchar(1000) COMMENT 'Agent 生成的优缺点诊断',
  `assessed_at` timestamp NOT NULL COMMENT '评估时间'
);

CREATE TABLE `assessment_dimension` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `assessment_id` bigint NOT NULL COMMENT '评估记录',
  `dimension_code` varchar(30) NOT NULL COMMENT '维度编码',
  `dimension_name` varchar(50) NOT NULL COMMENT '维度名称',
  `dimension_score` int NOT NULL COMMENT '维度得分',
  `weight` decimal(5,2) NOT NULL COMMENT '来自画像，百分比',
  `facility_count` int NOT NULL DEFAULT 0 COMMENT '设施数量'
);

CREATE TABLE `assessment_facility_stat` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `assessment_id` bigint NOT NULL COMMENT '评估记录',
  `category_id` bigint NOT NULL COMMENT '设施类别',
  `facility_count` int NOT NULL DEFAULT 0 COMMENT '设施数量',
  `nearest_distance_m` decimal(10,2) COMMENT '米',
  `status` varchar(20) COMMENT '充足/基本满足/待改善，与前端枚举逐字一致'
);

CREATE TABLE `district_score_snapshot` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_id` bigint NOT NULL COMMENT '片区',
  `batch_id` bigint COMMENT '数据批次',
  `coverage_pct` int NOT NULL COMMENT '%，15 分钟覆盖人口占比',
  `avg_score` decimal(5,2) NOT NULL COMMENT '平均评分',
  `rank_no` int COMMENT '辖区排名',
  `resident_count` int COMMENT '覆盖人口',
  `scored_at` timestamp NOT NULL COMMENT '计算时间'
);

CREATE TABLE `site_candidate` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_id` bigint NOT NULL COMMENT '所属片区',
  `batch_id` bigint COMMENT '数据批次',
  `candidate_name` varchar(100) NOT NULL COMMENT '如“东园路口”',
  `business_type` varchar(100) COMMENT '早餐、便利店、托育、药店等',
  `lng` decimal(10,6) COMMENT '经度',
  `lat` decimal(10,6) COMMENT '纬度',
  `population_index` decimal(10,2) COMMENT '候选项半径内人口/密度综合指数',
  `competitor_count` int COMMENT '候选点 15 分钟范围内同业态 POI 数',
  `demand_level` varchar(10) COMMENT '高/中高/中/低',
  `competition_level` varchar(10) COMMENT '低/中/高',
  `rent_min` decimal(8,2) COMMENT '万元/年',
  `rent_max` decimal(8,2) COMMENT '万元/年',
  `site_score` int COMMENT '选址评分',
  `created_at` timestamp NOT NULL COMMENT '生成时间'
);

CREATE TABLE `site_score_item` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `candidate_id` bigint NOT NULL COMMENT '候选点',
  `score_item` varchar(50) NOT NULL COMMENT '人口密度/竞争饱和度/租金/交通/设施缺口',
  `item_score` decimal(5,2) NOT NULL COMMENT '得分',
  `weight` decimal(5,2) NOT NULL COMMENT '权重',
  `reason` varchar(255) COMMENT '给商户看的解释文本'
);

CREATE TABLE `merchant_intent` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `merchant_name` varchar(100) NOT NULL COMMENT '商户名称',
  `business_type` varchar(100) NOT NULL COMMENT '经营业态',
  `contact` varchar(200) NOT NULL COMMENT 'AES-256-GCM 加密后 Base64，禁止明文落库；接口层解密',
  `contact_masked` varchar(20) COMMENT '如 138****8000，列表展示用',
  `district_id` bigint COMMENT '意向片区',
  `candidate_id` bigint COMMENT '意向候选点',
  `budget_min` decimal(8,2) COMMENT '万元',
  `budget_max` decimal(8,2) COMMENT '万元',
  `area_sqm` decimal(8,2) COMMENT '平方米',
  `remark` varchar(500) COMMENT '经营说明',
  `status` varchar(20) NOT NULL DEFAULT 'SUBMITTED' COMMENT '意向状态',
  `created_at` timestamp NOT NULL COMMENT '创建时间',
  `updated_at` timestamp NOT NULL COMMENT '更新时间'
);

CREATE TABLE `merchant_match` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `intent_id` bigint NOT NULL COMMENT '开店意向',
  `district_id` bigint NOT NULL COMMENT '片区',
  `gap_id` bigint COMMENT '对应短板',
  `fit_score` int NOT NULL COMMENT '匹配度',
  `match_reason` varchar(500) COMMENT '匹配理由',
  `status` varchar(20) NOT NULL DEFAULT 'PENDING' COMMENT '对接状态',
  `matched_at` timestamp NOT NULL COMMENT '匹配时间'
);

CREATE TABLE `community_gap` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_id` bigint NOT NULL COMMENT '片区',
  `category_id` bigint NOT NULL COMMENT '设施类别',
  `area_name` varchar(100) NOT NULL COMMENT '短板区域名称',
  `issue` varchar(200) NOT NULL COMMENT '如“夜间就医距离较远”',
  `gap_level` varchar(10) NOT NULL COMMENT '高/中/低，与前端枚举一致',
  `uncovered_residents` int COMMENT '人',
  `priority_no` int COMMENT '1 为最高',
  `batch_id` bigint COMMENT '数据批次',
  `created_at` timestamp NOT NULL COMMENT '创建时间'
);

CREATE TABLE `simulation_record` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `district_id` bigint NOT NULL COMMENT '片区',
  `category_id` bigint NOT NULL COMMENT '设施类别',
  `business_type` varchar(100) COMMENT '模拟业态',
  `lng` decimal(10,6) COMMENT '模拟点经度',
  `lat` decimal(10,6) COMMENT '模拟点纬度',
  `before_coverage` int NOT NULL COMMENT '%',
  `after_coverage` int NOT NULL COMMENT '%',
  `benefited_residents` int NOT NULL COMMENT '受益人口',
  `operator` varchar(50) COMMENT '社区工作人员编号',
  `simulated_at` timestamp NOT NULL COMMENT '模拟时间'
);

CREATE TABLE `sync_batch` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `batch_no` varchar(40) UNIQUE NOT NULL COMMENT '如 POI-20261015-01',
  `data_source` varchar(20) NOT NULL COMMENT '数据来源',
  `sync_type` varchar(20) NOT NULL COMMENT '同步类型',
  `started_at` timestamp NOT NULL COMMENT '开始时间',
  `finished_at` timestamp COMMENT '结束时间',
  `total_count` int NOT NULL DEFAULT 0 COMMENT '处理总数',
  `insert_count` int NOT NULL DEFAULT 0 COMMENT '新增数',
  `update_count` int NOT NULL DEFAULT 0 COMMENT '变更数',
  `close_count` int NOT NULL DEFAULT 0 COMMENT '关停数',
  `invalid_count` int NOT NULL DEFAULT 0 COMMENT '无效数',
  `status` varchar(20) NOT NULL DEFAULT 'RUNNING' COMMENT '批次状态',
  `error_msg` varchar(1000) COMMENT '错误信息',
  `created_at` timestamp NOT NULL COMMENT '创建时间'
);

CREATE TABLE `data_quality_issue` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `batch_id` bigint NOT NULL COMMENT '同步批次',
  `poi_id` bigint COMMENT '设施',
  `rule_code` varchar(40) NOT NULL COMMENT '如 DUP_POI、COORD_OUT_OF_RANGE',
  `issue_desc` varchar(500) NOT NULL COMMENT '问题描述',
  `severity` varchar(20) NOT NULL COMMENT '严重程度',
  `is_handled` char(1) NOT NULL DEFAULT 'N' COMMENT '是否已处理',
  `handled_at` timestamp COMMENT '处理时间',
  `created_at` timestamp NOT NULL COMMENT '创建时间'
);

CREATE TABLE `ods_poi_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `batch_id` bigint NOT NULL COMMENT '同步批次',
  `source` varchar(20) NOT NULL COMMENT '数据来源',
  `source_poi_id` varchar(100) NOT NULL COMMENT '来源 POI 编号',
  `poi_name` varchar(200) COMMENT '设施名称',
  `lng` decimal(10,6) COMMENT '经度',
  `lat` decimal(10,6) COMMENT '纬度',
  `category_raw` varchar(100) COMMENT '原始类别',
  `address` varchar(255) COMMENT '原始地址',
  `raw_json` text NOT NULL COMMENT '接口返回 JSON 原样保存',
  `load_at` timestamp NOT NULL COMMENT '入库时间',
  `process_status` varchar(20) NOT NULL DEFAULT 'PENDING' COMMENT '处理状态'
);

CREATE TABLE `ods_population_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `batch_id` bigint NOT NULL COMMENT '同步批次',
  `grid_code` varchar(40) NOT NULL COMMENT '栅格编码',
  `population` int COMMENT '人口数',
  `density` decimal(12,2) COMMENT '人口密度',
  `data_date` date COMMENT '统计日期',
  `raw_json` text NOT NULL COMMENT '原始报文',
  `load_at` timestamp NOT NULL COMMENT '入库时间',
  `process_status` varchar(20) NOT NULL DEFAULT 'PENDING' COMMENT '处理状态'
);

CREATE TABLE `ods_road_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `batch_id` bigint NOT NULL COMMENT '同步批次',
  `segment_code` varchar(50) COMMENT '路段编码',
  `raw_json` text NOT NULL COMMENT '原始报文',
  `load_at` timestamp NOT NULL COMMENT '入库时间',
  `process_status` varchar(20) NOT NULL DEFAULT 'PENDING' COMMENT '处理状态'
);

CREATE INDEX `idx_app_user_role_status` ON `app_user` (`role_code`, `status`);

CREATE UNIQUE INDEX `uk_user_profile_ver` ON `user_profile` (`user_id`, `version_no`);

CREATE INDEX `idx_user_profile_cur` ON `user_profile` (`user_id`, `is_current`);

CREATE INDEX `idx_profile_tag_dim` ON `profile_tag` (`dimension_code`, `role_scope`);

CREATE UNIQUE INDEX `uk_profile_tag` ON `user_profile_tag` (`profile_id`, `tag_id`);

CREATE UNIQUE INDEX `uk_profile_dim` ON `profile_dimension_weight` (`profile_id`, `dimension_code`);

CREATE INDEX `idx_district_parent` ON `district` (`parent_id`);

CREATE INDEX `idx_district_city` ON `district` (`city_code`, `district_level`);

CREATE UNIQUE INDEX `uk_pop_grid_date` ON `population_grid` (`grid_code`, `data_date`);

CREATE INDEX `idx_pop_district_date` ON `population_grid` (`district_id`, `data_date`);

CREATE INDEX `idx_road_node_district` ON `road_node` (`district_id`);

CREATE INDEX `idx_road_seg_from` ON `road_segment` (`from_node_id`);

CREATE INDEX `idx_road_seg_to` ON `road_segment` (`to_node_id`);

CREATE INDEX `idx_road_seg_district` ON `road_segment` (`district_id`);

CREATE INDEX `idx_fac_category_dim` ON `facility_category` (`dimension_code`, `sort_no`);

CREATE UNIQUE INDEX `uk_poi_source` ON `poi_facility` (`source`, `source_poi_id`);

CREATE INDEX `idx_poi_district_cat` ON `poi_facility` (`district_id`, `category_id`);

CREATE INDEX `idx_poi_category` ON `poi_facility` (`category_id`, `is_valid`);

CREATE INDEX `idx_poi_name` ON `poi_facility` (`poi_name`);

CREATE INDEX `idx_poi_log_poi` ON `poi_change_log` (`poi_id`, `changed_at`);

CREATE INDEX `idx_poi_log_batch` ON `poi_change_log` (`batch_id`);

CREATE INDEX `idx_assess_district_time` ON `resident_assessment` (`district_id`, `assessed_at`);

CREATE INDEX `idx_assess_user` ON `resident_assessment` (`user_id`, `assessed_at`);

CREATE INDEX `idx_assess_batch` ON `resident_assessment` (`batch_id`);

CREATE UNIQUE INDEX `uk_assess_dim` ON `assessment_dimension` (`assessment_id`, `dimension_code`);

CREATE UNIQUE INDEX `uk_assess_category` ON `assessment_facility_stat` (`assessment_id`, `category_id`);

CREATE UNIQUE INDEX `uk_district_batch` ON `district_score_snapshot` (`district_id`, `batch_id`);

CREATE INDEX `idx_district_score_time` ON `district_score_snapshot` (`scored_at`);

CREATE INDEX `idx_site_district_type` ON `site_candidate` (`district_id`, `business_type`, `site_score`);

CREATE INDEX `idx_site_batch` ON `site_candidate` (`batch_id`);

CREATE UNIQUE INDEX `uk_site_score_item` ON `site_score_item` (`candidate_id`, `score_item`);

CREATE INDEX `idx_intent_status_time` ON `merchant_intent` (`status`, `created_at`);

CREATE INDEX `idx_intent_district` ON `merchant_intent` (`district_id`);

CREATE INDEX `idx_intent_candidate` ON `merchant_intent` (`candidate_id`);

CREATE INDEX `idx_match_intent` ON `merchant_match` (`intent_id`);

CREATE INDEX `idx_match_gap` ON `merchant_match` (`gap_id`);

CREATE INDEX `idx_match_district_score` ON `merchant_match` (`district_id`, `fit_score`);

CREATE INDEX `idx_gap_district_level` ON `community_gap` (`district_id`, `gap_level`);

CREATE INDEX `idx_gap_category` ON `community_gap` (`category_id`);

CREATE INDEX `idx_gap_batch` ON `community_gap` (`batch_id`);

CREATE INDEX `idx_sim_district_time` ON `simulation_record` (`district_id`, `simulated_at`);

CREATE INDEX `idx_sync_status_time` ON `sync_batch` (`status`, `started_at`);

CREATE INDEX `idx_dq_batch_severity` ON `data_quality_issue` (`batch_id`, `severity`, `is_handled`);

CREATE INDEX `idx_ods_poi_batch` ON `ods_poi_raw` (`batch_id`, `process_status`);

CREATE INDEX `idx_ods_poi_source` ON `ods_poi_raw` (`source`, `source_poi_id`);

CREATE INDEX `idx_ods_pop_batch` ON `ods_population_raw` (`batch_id`, `process_status`);

CREATE INDEX `idx_ods_road_batch` ON `ods_road_raw` (`batch_id`, `process_status`);

ALTER TABLE `app_user` COMMENT = '用户账号表：三类使用者的统一账号，只保存脱敏业务编号与手机号哈希，不落库明文手机号。';

ALTER TABLE `user_profile` COMMENT = '用户画像表：一次画像生成的版本化结果，保留历史版本，is_current 标记当前生效画像。';

ALTER TABLE `profile_tag` COMMENT = '画像标签字典表：可配置的关注点标签库，按角色与评分维度归类，供画像生成和权重计算使用。';

ALTER TABLE `user_profile_tag` COMMENT = '用户画像标签明细表：画像与标签的多对多关联，记录用户勾选/对话提取出的标签及个性化权重。';

ALTER TABLE `profile_dimension_weight` COMMENT = '画像维度权重表：画像对五个评分维度的最终权重，居民评估时按该表动态加权，权重之和应为 100。';

ALTER TABLE `district` COMMENT = '社区片区表：街道—社区—网格三级空间主数据，是设施、评估、选址和治理的公共维度。';

ALTER TABLE `population_grid` COMMENT = '人口栅格表：按栅格与统计日期保存常住人口和密度，是商户选址人口指数与社区覆盖测算的输入。';

ALTER TABLE `road_node` COMMENT = '路网节点表：步行路网拓扑节点（路口、小区出入口、过街设施），用于 15 分钟步行可达计算。';

ALTER TABLE `road_segment` COMMENT = '路网步行段表：连接两个路网节点的步行段，保存长度与步行耗时，构成 15 分钟等时圈的图结构。';

ALTER TABLE `facility_category` COMMENT = '设施类别字典表：POI 类别与五维评分的映射字典，统一高德分类与业务维度，避免代码硬编码。';

ALTER TABLE `poi_facility` COMMENT = '设施网点 POI 表：社区周边生鲜、医疗、教育、交通、夜间服务等设施网点，是评估与选址的主数据。';

ALTER TABLE `poi_change_log` COMMENT = 'POI 变更日志表：记录新增、变更、关停和清洗无效的 POI 差异，支持增量追溯与数据质量审计。';

ALTER TABLE `resident_assessment` COMMENT = '居民生活圈评估表：一次居民生活圈体检的汇总结果，保存评分、画像、步行半径和诊断结论。';

ALTER TABLE `assessment_dimension` COMMENT = '评估维度得分表：五维评分的分项结果，保存得分、权重和设施计数，支撑雷达图与可解释性。';

ALTER TABLE `assessment_facility_stat` COMMENT = '评估设施盘点表：一次评估中各设施类别的数量、最近距离与状态，用于设施清单和短板定位。';

ALTER TABLE `district_score_snapshot` COMMENT = '片区评分快照表：每次数据同步后按片区重算的便民评分与排名，供社区热力图、排名和趋势查询。';

ALTER TABLE `site_candidate` COMMENT = '商户选址候选点表：Agent 依据人口栅格与同业态竞争 POI 推演出的候选点位，含评分与关键指标。';

ALTER TABLE `site_score_item` COMMENT = '选址评分明细表：候选点各评分项的分值、权重与理由，保证选址推荐可解释、可复核。';

ALTER TABLE `merchant_intent` COMMENT = '商户开店意向表：商户提交的开店意向，保留原有字段并扩展片区、候选点、预算和状态，兼容现有接口。';

ALTER TABLE `merchant_match` COMMENT = '招商匹配表：社区短板与商户意向的双向匹配结果，记录匹配分、理由和对接状态。';

ALTER TABLE `community_gap` COMMENT = '社区短板片区表：社区识别出的买菜难、就医远、托育不足等短板，含缺口等级、未覆盖人口与优先级。';

ALTER TABLE `simulation_record` COMMENT = '网点增设模拟记录表：社区在地图上模拟新增便民网点后的覆盖率、受益人口和前后对比，支撑改造决策。';

ALTER TABLE `sync_batch` COMMENT = '数据同步批次表：每半月一次 POI/人口/路网增量同步的批次台账，记录数量、状态与错误信息。';

ALTER TABLE `data_quality_issue` COMMENT = '数据质量问题表：同步过程中的重复、坐标异常、类别缺失等质量问题及处理状态，支撑数据治理闭环。';

ALTER TABLE `ods_poi_raw` COMMENT = 'POI 原始数据表：高德/政务 POI 接口原始报文落地，保留原样 JSON，供清洗、重放和审计。';

ALTER TABLE `ods_population_raw` COMMENT = '人口栅格原始数据表：人口栅格文件/接口的原始统计值，按批次保留，供复算和口径追溯。';

ALTER TABLE `ods_road_raw` COMMENT = '路网原始数据表：路网数据文件的原始路段记录，保留几何与属性原文，供拓扑重建。';

ALTER TABLE `user_profile` ADD FOREIGN KEY (`user_id`) REFERENCES `app_user` (`id`);

ALTER TABLE `user_profile_tag` ADD FOREIGN KEY (`profile_id`) REFERENCES `user_profile` (`id`);

ALTER TABLE `user_profile_tag` ADD FOREIGN KEY (`tag_id`) REFERENCES `profile_tag` (`id`);

ALTER TABLE `profile_dimension_weight` ADD FOREIGN KEY (`profile_id`) REFERENCES `user_profile` (`id`);

ALTER TABLE `district` ADD FOREIGN KEY (`parent_id`) REFERENCES `district` (`id`);

ALTER TABLE `population_grid` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `road_node` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `road_segment` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `road_segment` ADD FOREIGN KEY (`from_node_id`) REFERENCES `road_node` (`id`);

ALTER TABLE `road_segment` ADD FOREIGN KEY (`to_node_id`) REFERENCES `road_node` (`id`);

ALTER TABLE `poi_facility` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `poi_facility` ADD FOREIGN KEY (`category_id`) REFERENCES `facility_category` (`id`);

ALTER TABLE `poi_change_log` ADD FOREIGN KEY (`poi_id`) REFERENCES `poi_facility` (`id`);

ALTER TABLE `poi_change_log` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `resident_assessment` ADD FOREIGN KEY (`user_id`) REFERENCES `app_user` (`id`);

ALTER TABLE `resident_assessment` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `resident_assessment` ADD FOREIGN KEY (`profile_id`) REFERENCES `user_profile` (`id`);

ALTER TABLE `resident_assessment` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `assessment_dimension` ADD FOREIGN KEY (`assessment_id`) REFERENCES `resident_assessment` (`id`);

ALTER TABLE `assessment_facility_stat` ADD FOREIGN KEY (`assessment_id`) REFERENCES `resident_assessment` (`id`);

ALTER TABLE `assessment_facility_stat` ADD FOREIGN KEY (`category_id`) REFERENCES `facility_category` (`id`);

ALTER TABLE `district_score_snapshot` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `district_score_snapshot` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `site_candidate` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `site_candidate` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `site_score_item` ADD FOREIGN KEY (`candidate_id`) REFERENCES `site_candidate` (`id`);

ALTER TABLE `merchant_intent` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `merchant_intent` ADD FOREIGN KEY (`candidate_id`) REFERENCES `site_candidate` (`id`);

ALTER TABLE `merchant_match` ADD FOREIGN KEY (`intent_id`) REFERENCES `merchant_intent` (`id`);

ALTER TABLE `merchant_match` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `merchant_match` ADD FOREIGN KEY (`gap_id`) REFERENCES `community_gap` (`id`);

ALTER TABLE `community_gap` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `community_gap` ADD FOREIGN KEY (`category_id`) REFERENCES `facility_category` (`id`);

ALTER TABLE `community_gap` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `simulation_record` ADD FOREIGN KEY (`district_id`) REFERENCES `district` (`id`);

ALTER TABLE `simulation_record` ADD FOREIGN KEY (`category_id`) REFERENCES `facility_category` (`id`);

ALTER TABLE `data_quality_issue` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `data_quality_issue` ADD FOREIGN KEY (`poi_id`) REFERENCES `poi_facility` (`id`);

ALTER TABLE `ods_poi_raw` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `ods_population_raw` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);

ALTER TABLE `ods_road_raw` ADD FOREIGN KEY (`batch_id`) REFERENCES `sync_batch` (`id`);
