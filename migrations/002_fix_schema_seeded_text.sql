-- 002 修复 schema 初始化数据的双重编码乱码
-- 根因:danqiu_platform_schema.sql 缺 SET NAMES utf8mb4(已补),旧卷按 latin1 解释了中文
USE danqiu_rice;
SET NAMES utf8mb4;

UPDATE sys_role SET role_name = CASE role_code
  WHEN 'FARMER' THEN '农户'
  WHEN 'CONSUMER' THEN '消费者'
  WHEN 'BANK' THEN '合作银行'
  WHEN 'INSURANCE' THEN '保险公司'
  WHEN 'OPERATOR' THEN '品牌运营方'
  WHEN 'GOVERNMENT' THEN '政府监管'
  WHEN 'ADMIN' THEN '平台管理员'
  ELSE role_name END;

UPDATE insurance_product
SET product_name = '丹邱丝苗米种植保险'
WHERE product_name LIKE 'ä%' OR product_name <> CONVERT(CONVERT(product_name USING latin1) USING utf8mb4);
