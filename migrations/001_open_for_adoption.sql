-- 001 认养开放标记(系统管理后台-认养管理)
-- 有溯源码的地块默认开放认养,运营可在后台调整
USE danqiu_rice;

ALTER TABLE farm_plot
  ADD COLUMN open_for_adoption TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否开放消费者认养' AFTER status;

UPDATE farm_plot p
SET p.open_for_adoption = 1
WHERE EXISTS (SELECT 1 FROM trace_code t WHERE t.plot_id = p.id AND t.status = 'ACTIVE');
