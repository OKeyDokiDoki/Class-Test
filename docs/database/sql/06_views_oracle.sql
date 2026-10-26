-- 社区治理看板视图：每个片区取最新一次评分快照
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
