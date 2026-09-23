-- 004 特色农险产品矩阵与自动定损基础字段
USE danqiu_rice;
SET NAMES utf8mb4;

ALTER TABLE insurance_product
  ADD COLUMN product_code VARCHAR(32) NULL AFTER id,
  ADD COLUMN product_type ENUM('COST','INCOME','PRICE_INDEX','WEATHER_INDEX','QUALITY_DOWNGRADE') NOT NULL DEFAULT 'COST' AFTER product_code,
  ADD COLUMN trigger_config JSON NULL AFTER government_subsidy_rate,
  ADD COLUMN description VARCHAR(500) NULL AFTER trigger_config;

UPDATE insurance_product
SET product_code = CONCAT('COST-', LPAD(id, 3, '0')),
    product_type = 'COST',
    description = '政策性基础保障，按受灾比例人工定损'
WHERE product_code IS NULL;

ALTER TABLE insurance_product MODIFY product_code VARCHAR(32) NOT NULL;
ALTER TABLE insurance_product ADD UNIQUE KEY uk_insurance_product_code (product_code);

ALTER TABLE insurance_claim
  ADD COLUMN assessment_mode ENUM('MANUAL','WEATHER_INDEX','PRICE_INDEX','QUALITY_INDEX','INCOME_INDEX') NOT NULL DEFAULT 'MANUAL' AFTER claim_amount,
  ADD COLUMN assessment_json JSON NULL AFTER assessment_mode;

INSERT INTO insurance_product
  (product_code, product_type, product_name, insured_amount_per_mu, premium_rate, government_subsidy_rate, trigger_config, description)
SELECT 'INCOME-001', 'INCOME', '丝苗米收入保险', 2000, 0.055, 0.30, '{"target_income_per_mu":3600}', '收入低于目标收入时按差额辅助核算'
WHERE NOT EXISTS (SELECT 1 FROM insurance_product WHERE product_code = 'INCOME-001');
INSERT INTO insurance_product
  (product_code, product_type, product_name, insured_amount_per_mu, premium_rate, government_subsidy_rate, trigger_config, description)
SELECT 'PRICE-001', 'PRICE_INDEX', '稻谷价格指数保险', 1200, 0.05, 0.50, '{"trigger_price":2.40,"base_price":3.00}', '区域收购价格低于约定指数时触发'
WHERE NOT EXISTS (SELECT 1 FROM insurance_product WHERE product_code = 'PRICE-001');
INSERT INTO insurance_product
  (product_code, product_type, product_name, insured_amount_per_mu, premium_rate, government_subsidy_rate, trigger_config, description)
SELECT 'WEATHER-001', 'WEATHER_INDEX', '台风暴雨气象指数保险', 800, 0.045, 0.40, '{"wind_speed_kmh":80,"rainfall_mm":120}', '风速或过程雨量达到阈值时自动生成定损草案'
WHERE NOT EXISTS (SELECT 1 FROM insurance_product WHERE product_code = 'WEATHER-001');
INSERT INTO insurance_product
  (product_code, product_type, product_name, insured_amount_per_mu, premium_rate, government_subsidy_rate, trigger_config, description)
SELECT 'QUALITY-001', 'QUALITY_DOWNGRADE', '米质降级保险', 600, 0.0467, 0.50, '{"max_grade_drop":2}', '灾后质量等级下降时按检测结果辅助核算'
WHERE NOT EXISTS (SELECT 1 FROM insurance_product WHERE product_code = 'QUALITY-001');
