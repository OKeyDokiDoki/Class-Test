-- ============================================================
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
