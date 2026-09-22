-- 003 农户收入明细(PRD v5 §4.1 我的收入:地租、工资、品牌溢价、平台分红)
USE danqiu_rice;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS farmer_income (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  farmer_id BIGINT UNSIGNED NOT NULL COMMENT '农户档案',
  income_type ENUM('RENT','WAGE','BRAND_PREMIUM') NOT NULL COMMENT '地租/务工工资/品牌溢价(分红走 farmer_dividend)',
  amount DECIMAL(12,2) NOT NULL,
  period VARCHAR(16) NOT NULL COMMENT '年度,如 2025',
  remark VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_income_farmer FOREIGN KEY (farmer_id) REFERENCES farmer_profile(id),
  KEY idx_income_farmer_period (farmer_id, period)
) ENGINE=InnoDB COMMENT '农户收入明细';

-- 回填演示数据:每户两年地租与工资,认证农户另有品牌溢价
INSERT INTO farmer_income (farmer_id, income_type, amount, period, remark)
SELECT id, 'RENT', ROUND(300 + RAND() * 400, 2), '2025', '土地流转租金' FROM farmer_profile;

INSERT INTO farmer_income (farmer_id, income_type, amount, period, remark)
SELECT id, 'WAGE', ROUND(1200 + RAND() * 2400, 2), '2025', '基地务工工资' FROM farmer_profile;

INSERT INTO farmer_income (farmer_id, income_type, amount, period, remark)
SELECT id, 'RENT', ROUND(300 + RAND() * 400, 2), '2026', '土地流转租金' FROM farmer_profile;

INSERT INTO farmer_income (farmer_id, income_type, amount, period, remark)
SELECT id, 'WAGE', ROUND(1200 + RAND() * 2400, 2), '2026', '基地务工工资' FROM farmer_profile;

INSERT INTO farmer_income (farmer_id, income_type, amount, period, remark)
SELECT id, 'BRAND_PREMIUM', ROUND(200 + RAND() * 600, 2), '2026', '品牌溢价分成'
FROM farmer_profile WHERE certification_status = 'CERTIFIED';
