-- 新增两种丹邱大米商品及其溯源码
USE danqiu_rice;
SET NAMES utf8mb4;

INSERT INTO trace_code
  (code, plot_id, season_id, batch_name, product_grade, quality_report_url, status)
SELECT 'DANQIU-XM-20260922', 1, 4, '丹邱村香米 2026年批次', 'SPECIAL', NULL, 'ACTIVE'
WHERE NOT EXISTS (SELECT 1 FROM trace_code WHERE code = 'DANQIU-XM-20260922');

INSERT INTO trace_code
  (code, plot_id, season_id, batch_name, product_grade, quality_report_url, status)
SELECT 'DANQIU-YM-20260922', 2, 4, '丹邱村胚芽米 2026年批次', 'FIRST', NULL, 'ACTIVE'
WHERE NOT EXISTS (SELECT 1 FROM trace_code WHERE code = 'DANQIU-YM-20260922');

INSERT INTO product (trace_code_id, product_name, specification, price, stock, status)
SELECT t.id, '丹邱香米 5kg 装', '5kg 装', 78.00, 200, 'ON_SALE'
FROM trace_code t
WHERE t.code = 'DANQIU-XM-20260922'
  AND NOT EXISTS (SELECT 1 FROM product WHERE product_name = '丹邱香米 5kg 装');

INSERT INTO product (trace_code_id, product_name, specification, price, stock, status)
SELECT t.id, '丹邱胚芽米 5kg 装', '5kg 装', 88.00, 180, 'ON_SALE'
FROM trace_code t
WHERE t.code = 'DANQIU-YM-20260922'
  AND NOT EXISTS (SELECT 1 FROM product WHERE product_name = '丹邱胚芽米 5kg 装');
