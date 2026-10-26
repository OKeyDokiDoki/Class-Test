-- 初始化数据：设施类别、画像标签、演示片区与 POI（可选）
SET DEFINE OFF;

INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('FRESH_MARKET', '菜市场', 'FRESH', '生鲜购物', 10);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('FRESH_SUPER', '生鲜超市', 'FRESH', '生鲜购物', 20);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('CONVENIENCE', '便利店', 'FRESH', '生鲜购物', 30);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('COMMUNITY_CLINIC', '社区卫生服务中心', 'MEDICAL', '医疗健康', 10);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('PHARMACY', '药店', 'MEDICAL', '医疗健康', 20);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('CLINIC', '社区诊所', 'MEDICAL', '医疗健康', 30);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('KINDERGARTEN', '幼儿园', 'EDU', '亲子教育', 10);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('NURSERY', '托育机构', 'EDU', '亲子教育', 20);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('PRIMARY_SCHOOL', '小学', 'EDU', '亲子教育', 30);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('BUS_STOP', '公交站', 'TRAFFIC', '交通通勤', 10);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('METRO_STATION', '地铁站', 'TRAFFIC', '交通通勤', 20);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('NIGHT_PHARMACY', '夜间药店', 'NIGHT', '夜间服务', 10);
INSERT INTO facility_category (category_code, category_name, dimension_code, dimension_name, sort_no) VALUES ('NIGHT_STORE', '24 小时便利店', 'NIGHT', '夜间服务', 20);

INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('FRESH_FOOD', '生鲜买菜', 'RESIDENT', 'FRESH', 20);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('NIGHT_MEDICAL', '夜间就医', 'RESIDENT', 'NIGHT', 20);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('PARENTING', '亲子托育', 'RESIDENT', 'EDU', 20);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('COMMUTE', '通勤便利', 'RESIDENT', 'TRAFFIC', 20);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('ELDER_CARE', '老人就医', 'RESIDENT', 'MEDICAL', 20);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('LOW_RISK', '稳健投资', 'MERCHANT', 'COMPETITION', 30);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('HIGH_TRAFFIC', '高人流', 'MERCHANT', 'POPULATION', 35);
INSERT INTO profile_tag (tag_code, tag_name, role_scope, dimension_code, default_weight) VALUES ('LOW_RENT', '低租金', 'MERCHANT', 'RENT', 35);

INSERT INTO district (district_code, district_name, district_level, city_code, center_lng, center_lat, resident_count) VALUES ('510107001001', '朝阳社区示范片区', 'STREET', '510107', 104.0431, 30.6421, 12680);
INSERT INTO district (district_code, district_name, district_level, city_code, center_lng, center_lat, resident_count) VALUES ('510107001002', '东南片区', 'COMMUNITY', '510107', 104.0512, 30.6388, 8420);
INSERT INTO district (district_code, district_name, district_level, city_code, center_lng, center_lat, resident_count) VALUES ('510107001003', '北部新居', 'COMMUNITY', '510107', 104.0405, 30.6512, 9630);

INSERT INTO sync_batch (batch_no, data_source, sync_type, started_at, finished_at, total_count, insert_count, status) VALUES ('POI-20261015-01', 'AMAP', 'INCREMENT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 'SUCCESS');

INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) SELECT d.id, c.id, '朝阳生鲜市场', 104.0437, 30.6426, '朝阳路 18 号', 'MANUAL', 'SEED-朝阳生鲜市场', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c WHERE d.district_code = '510107001001' AND c.category_code = 'FRESH_MARKET';
INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) SELECT d.id, c.id, '朝阳社区卫生服务中心', 104.0425, 30.6419, '朝阳路 36 号', 'MANUAL', 'SEED-朝阳社区卫生服务中心', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c WHERE d.district_code = '510107001001' AND c.category_code = 'COMMUNITY_CLINIC';
INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) SELECT d.id, c.id, '小芽托育中心', 104.0442, 30.6408, '文体路 8 号', 'MANUAL', 'SEED-小芽托育中心', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c WHERE d.district_code = '510107001001' AND c.category_code = 'NURSERY';
INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) SELECT d.id, c.id, '东园路口公交站', 104.046, 30.6432, '东园路', 'MANUAL', 'SEED-东园路口公交站', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c WHERE d.district_code = '510107001001' AND c.category_code = 'BUS_STOP';
INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) SELECT d.id, c.id, '康宁夜间药房', 104.0418, 30.6395, '康宁路 12 号', 'MANUAL', 'SEED-康宁夜间药房', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c WHERE d.district_code = '510107001001' AND c.category_code = 'NIGHT_PHARMACY';
INSERT INTO poi_facility (district_id, category_id, poi_name, lng, lat, address, source, source_poi_id, first_seen_at, last_seen_at) SELECT d.id, c.id, '邻家便利店', 104.0449, 30.6422, '朝阳路 22 号', 'MANUAL', 'SEED-邻家便利店', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM district d, facility_category c WHERE d.district_code = '510107001001' AND c.category_code = 'CONVENIENCE';

COMMIT;