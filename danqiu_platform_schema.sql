-- 丹邱丝苗米普惠产融服务平台数据库设计
-- MySQL 8.0 / Mock 数据与正式后端共用
-- 说明：不删除、不修改原有 agriculture_ddl.sql

CREATE DATABASE IF NOT EXISTS danqiu_rice DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE danqiu_rice;

-- 1. 用户与角色
CREATE TABLE sys_user (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NULL,
  real_name VARCHAR(64) NOT NULL,
  phone VARCHAR(32) NULL UNIQUE,
  status ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT '平台用户';

CREATE TABLE sys_role (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_code VARCHAR(32) NOT NULL UNIQUE,
  role_name VARCHAR(64) NOT NULL
) ENGINE=InnoDB COMMENT '平台角色';

CREATE TABLE sys_user_role (
  user_id BIGINT UNSIGNED NOT NULL,
  role_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_sur_user FOREIGN KEY (user_id) REFERENCES sys_user(id),
  CONSTRAINT fk_sur_role FOREIGN KEY (role_id) REFERENCES sys_role(id)
) ENGINE=InnoDB COMMENT '用户角色关系';

-- 2. 农户、地块与生产档案
CREATE TABLE farmer_profile (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL UNIQUE,
  village VARCHAR(128) NOT NULL DEFAULT '丹邱村',
  address VARCHAR(255) NULL,
  id_card_masked VARCHAR(32) NULL COMMENT '仅保存脱敏身份证号',
  certification_status ENUM('PENDING','CERTIFIED','REJECTED','SUSPENDED') NOT NULL DEFAULT 'PENDING',
  certification_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_farmer_user FOREIGN KEY (user_id) REFERENCES sys_user(id)
) ENGINE=InnoDB COMMENT '农户档案';

CREATE TABLE farm_plot (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plot_code VARCHAR(64) NOT NULL UNIQUE,
  farmer_id BIGINT UNSIGNED NOT NULL,
  plot_name VARCHAR(128) NOT NULL,
  village VARCHAR(128) NOT NULL DEFAULT '丹邱村',
  area_mu DECIMAL(10,2) NOT NULL,
  variety VARCHAR(128) NOT NULL DEFAULT '增科新选丝苗1号',
  longitude DECIMAL(10,7) NULL,
  latitude DECIMAL(10,7) NULL,
  boundary_json JSON NULL COMMENT '地块边界，前端地图展示用',
  satellite_image_url VARCHAR(500) NULL COMMENT '静态卫星图地址',
  status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_plot_farmer FOREIGN KEY (farmer_id) REFERENCES farmer_profile(id),
  CONSTRAINT chk_plot_area CHECK (area_mu > 0)
) ENGINE=InnoDB COMMENT '农田地块';

CREATE TABLE production_season (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  season_code VARCHAR(32) NOT NULL UNIQUE,
  season_name VARCHAR(64) NOT NULL,
  sowing_date DATE NULL,
  harvest_date DATE NULL,
  status ENUM('PLANNED','IN_PROGRESS','HARVESTED','CLOSED') NOT NULL DEFAULT 'PLANNED'
) ENGINE=InnoDB COMMENT '种植季';

CREATE TABLE farm_record (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plot_id BIGINT UNSIGNED NOT NULL,
  season_id BIGINT UNSIGNED NOT NULL,
  record_type ENUM('SOWING','FERTILIZING','PESTICIDE','IRRIGATION','HARVEST','QUALITY_TEST') NOT NULL,
  record_date DATE NOT NULL,
  description TEXT NULL,
  material_name VARCHAR(128) NULL,
  material_amount DECIMAL(10,2) NULL,
  output_jin DECIMAL(10,2) NULL,
  submitted_by BIGINT UNSIGNED NOT NULL,
  status ENUM('SUBMITTED','VERIFIED','NEEDS_CORRECTION') NOT NULL DEFAULT 'SUBMITTED',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_record_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id),
  CONSTRAINT fk_record_season FOREIGN KEY (season_id) REFERENCES production_season(id),
  CONSTRAINT fk_record_user FOREIGN KEY (submitted_by) REFERENCES sys_user(id),
  KEY idx_record_plot_date (plot_id, record_date),
  KEY idx_record_type (record_type)
) ENGINE=InnoDB COMMENT '农事记录';

CREATE TABLE record_attachment (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  record_id BIGINT UNSIGNED NOT NULL,
  file_url VARCHAR(500) NOT NULL,
  file_type VARCHAR(32) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_attachment_record FOREIGN KEY (record_id) REFERENCES farm_record(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT '农事记录照片或检测报告';

-- 3. 标准、认证与监管
CREATE TABLE standard_version (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  version_no VARCHAR(32) NOT NULL UNIQUE,
  title VARCHAR(200) NOT NULL,
  status ENUM('DRAFT','PUBLISHED','RETIRED') NOT NULL DEFAULT 'DRAFT',
  published_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT '丹邱丝苗米标准版本';

CREATE TABLE standard_clause (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  standard_id BIGINT UNSIGNED NOT NULL,
  stage ENUM('PLANTING','PROCESSING','QUALITY','GRADING','PACKAGING','DISTRIBUTION') NOT NULL,
  clause_code VARCHAR(64) NOT NULL,
  clause_name VARCHAR(128) NOT NULL,
  requirement TEXT NOT NULL,
  check_rule_json JSON NULL,
  UNIQUE KEY uk_clause_code (standard_id, clause_code),
  CONSTRAINT fk_clause_standard FOREIGN KEY (standard_id) REFERENCES standard_version(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT '全链条标准条款';

CREATE TABLE farmer_certification (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  farmer_id BIGINT UNSIGNED NOT NULL,
  plot_id BIGINT UNSIGNED NOT NULL,
  standard_id BIGINT UNSIGNED NOT NULL,
  status ENUM('PENDING','APPROVED','REJECTED','RECTIFYING') NOT NULL DEFAULT 'PENDING',
  reviewer_id BIGINT UNSIGNED NULL,
  review_note VARCHAR(500) NULL,
  submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at DATETIME NULL,
  CONSTRAINT fk_cert_farmer FOREIGN KEY (farmer_id) REFERENCES farmer_profile(id),
  CONSTRAINT fk_cert_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id),
  CONSTRAINT fk_cert_standard FOREIGN KEY (standard_id) REFERENCES standard_version(id),
  CONSTRAINT fk_cert_reviewer FOREIGN KEY (reviewer_id) REFERENCES sys_user(id)
) ENGINE=InnoDB COMMENT '农户地块品牌认证';

CREATE TABLE certification_check (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  certification_id BIGINT UNSIGNED NOT NULL,
  clause_id BIGINT UNSIGNED NOT NULL,
  result ENUM('PASS','FAIL','PENDING') NOT NULL DEFAULT 'PENDING',
  note VARCHAR(500) NULL,
  CONSTRAINT fk_check_cert FOREIGN KEY (certification_id) REFERENCES farmer_certification(id) ON DELETE CASCADE,
  CONSTRAINT fk_check_clause FOREIGN KEY (clause_id) REFERENCES standard_clause(id)
) ENGINE=InnoDB COMMENT '认证逐项检查结果';

CREATE TABLE field_inspection (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plot_id BIGINT UNSIGNED NOT NULL,
  inspector_id BIGINT UNSIGNED NOT NULL,
  inspection_date DATE NOT NULL,
  result ENUM('PASS','WARNING','FAIL') NOT NULL,
  difference_note TEXT NULL,
  rectification_required BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_inspection_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id),
  CONSTRAINT fk_inspection_user FOREIGN KEY (inspector_id) REFERENCES sys_user(id)
) ENGINE=InnoDB COMMENT '政府实地核验记录';

CREATE TABLE regulatory_report (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  report_type ENUM('WEEKLY','MONTHLY','QUARTERLY') NOT NULL,
  report_period VARCHAR(32) NOT NULL,
  content_json JSON NOT NULL,
  status ENUM('DRAFT','CONFIRMED','ARCHIVED') NOT NULL DEFAULT 'DRAFT',
  confirmed_by BIGINT UNSIGNED NULL,
  confirmed_at DATETIME NULL,
  export_file_url VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_report_period (report_type, report_period),
  CONSTRAINT fk_reg_report_user FOREIGN KEY (confirmed_by) REFERENCES sys_user(id)
) ENGINE=InnoDB COMMENT '政府周期监管报表';

-- 4. 保险与贷款
CREATE TABLE insurance_product (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_name VARCHAR(128) NOT NULL,
  insured_amount_per_mu DECIMAL(10,2) NOT NULL DEFAULT 1500,
  premium_rate DECIMAL(6,4) NOT NULL DEFAULT 0.0500,
  government_subsidy_rate DECIMAL(6,4) NOT NULL DEFAULT 0.8000,
  status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE'
) ENGINE=InnoDB COMMENT '农业保险产品';

CREATE TABLE insurance_policy (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  policy_no VARCHAR(64) NOT NULL UNIQUE,
  farmer_id BIGINT UNSIGNED NOT NULL,
  plot_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  insured_area_mu DECIMAL(10,2) NOT NULL,
  insured_amount DECIMAL(12,2) NOT NULL,
  total_premium DECIMAL(12,2) NOT NULL,
  farmer_premium DECIMAL(12,2) NOT NULL,
  status ENUM('APPLIED','ACTIVE','EXPIRED','CANCELLED') NOT NULL DEFAULT 'APPLIED',
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_policy_farmer FOREIGN KEY (farmer_id) REFERENCES farmer_profile(id),
  CONSTRAINT fk_policy_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id),
  CONSTRAINT fk_policy_product FOREIGN KEY (product_id) REFERENCES insurance_product(id)
) ENGINE=InnoDB COMMENT '农户保单';

CREATE TABLE insurance_claim (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  claim_no VARCHAR(64) NOT NULL UNIQUE,
  policy_id BIGINT UNSIGNED NOT NULL,
  disaster_note TEXT NULL,
  disaster_rate DECIMAL(6,4) NOT NULL,
  claim_amount DECIMAL(12,2) NOT NULL,
  entered_by BIGINT UNSIGNED NOT NULL COMMENT '管理员手动录入受灾比例',
  reviewed_by BIGINT UNSIGNED NULL,
  status ENUM('SUBMITTED','UNDER_REVIEW','APPROVED','REJECTED','PAID') NOT NULL DEFAULT 'SUBMITTED',
  reviewed_at DATETIME NULL,
  CONSTRAINT fk_claim_policy FOREIGN KEY (policy_id) REFERENCES insurance_policy(id),
  CONSTRAINT fk_claim_entered FOREIGN KEY (entered_by) REFERENCES sys_user(id),
  CONSTRAINT fk_claim_reviewer FOREIGN KEY (reviewed_by) REFERENCES sys_user(id),
  CONSTRAINT chk_disaster_rate CHECK (disaster_rate >= 0 AND disaster_rate <= 1)
) ENGINE=InnoDB COMMENT '保险理赔';

CREATE TABLE loan_application (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  application_no VARCHAR(64) NOT NULL UNIQUE,
  farmer_id BIGINT UNSIGNED NOT NULL,
  plot_id BIGINT UNSIGNED NOT NULL,
  area_mu DECIMAL(10,2) NOT NULL,
  suggested_amount DECIMAL(12,2) NOT NULL,
  risk_level ENUM('LOW','MEDIUM','HIGH') NOT NULL,
  bank_result ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
  bank_note VARCHAR(500) NULL,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at DATETIME NULL,
  CONSTRAINT fk_loan_farmer FOREIGN KEY (farmer_id) REFERENCES farmer_profile(id),
  CONSTRAINT fk_loan_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id)
) ENGINE=InnoDB COMMENT '贷款申请与授信建议';

-- 5. 溯源、商城、认养与分红
CREATE TABLE trace_code (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(96) NOT NULL UNIQUE,
  plot_id BIGINT UNSIGNED NOT NULL,
  season_id BIGINT UNSIGNED NOT NULL,
  batch_name VARCHAR(128) NOT NULL,
  product_grade ENUM('SPECIAL','FIRST','SECOND') NOT NULL,
  quality_report_url VARCHAR(500) NULL,
  status ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_trace_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id),
  CONSTRAINT fk_trace_season FOREIGN KEY (season_id) REFERENCES production_season(id)
) ENGINE=InnoDB COMMENT '一批一码溯源码';

CREATE TABLE product (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  trace_code_id BIGINT UNSIGNED NOT NULL,
  product_name VARCHAR(128) NOT NULL,
  specification VARCHAR(64) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  status ENUM('ON_SALE','OFF_SALE') NOT NULL DEFAULT 'ON_SALE',
  CONSTRAINT fk_product_trace FOREIGN KEY (trace_code_id) REFERENCES trace_code(id),
  CONSTRAINT chk_product_price CHECK (price >= 0)
) ENGINE=InnoDB COMMENT '平台销售商品';

CREATE TABLE adoption_order (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_no VARCHAR(64) NOT NULL UNIQUE,
  consumer_user_id BIGINT UNSIGNED NOT NULL,
  plot_id BIGINT UNSIGNED NOT NULL,
  fee DECIMAL(10,2) NOT NULL,
  status ENUM('PAID','ACTIVE','COMPLETED','REFUNDED') NOT NULL DEFAULT 'PAID',
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_adoption_user FOREIGN KEY (consumer_user_id) REFERENCES sys_user(id),
  CONSTRAINT fk_adoption_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id)
) ENGINE=InnoDB COMMENT '消费者认养订单';

CREATE TABLE sales_order (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_no VARCHAR(64) NOT NULL UNIQUE,
  consumer_user_id BIGINT UNSIGNED NULL,
  total_amount DECIMAL(12,2) NOT NULL,
  source ENUM('PLATFORM','OTHER') NOT NULL DEFAULT 'PLATFORM',
  status ENUM('PENDING_PAYMENT','PAID','SHIPPED','COMPLETED','CANCELLED','REFUNDED') NOT NULL DEFAULT 'PENDING_PAYMENT',
  address_snapshot JSON NULL,
  paid_at DATETIME NULL,
  shipped_at DATETIME NULL,
  completed_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_sales_user FOREIGN KEY (consumer_user_id) REFERENCES sys_user(id)
) ENGINE=InnoDB COMMENT '平台商城订单';

CREATE TABLE sales_order_item (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  plot_id BIGINT UNSIGNED NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES sales_order(id) ON DELETE CASCADE,
  CONSTRAINT fk_item_product FOREIGN KEY (product_id) REFERENCES product(id),
  CONSTRAINT fk_item_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id)
) ENGINE=InnoDB COMMENT '商城订单明细';

CREATE TABLE shipment (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id BIGINT UNSIGNED NOT NULL UNIQUE,
  carrier VARCHAR(64) NULL,
  tracking_no VARCHAR(128) NULL,
  shipped_at DATETIME NULL,
  CONSTRAINT fk_shipment_order FOREIGN KEY (order_id) REFERENCES sales_order(id)
) ENGINE=InnoDB COMMENT '订单物流';

CREATE TABLE farmer_dividend (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id BIGINT UNSIGNED NOT NULL,
  farmer_id BIGINT UNSIGNED NOT NULL,
  plot_id BIGINT UNSIGNED NOT NULL,
  base_amount DECIMAL(12,2) NOT NULL COMMENT '参与分红的订单金额或新增利润基数',
  dividend_rate DECIMAL(6,4) NOT NULL,
  dividend_amount DECIMAL(12,2) NOT NULL,
  status ENUM('CALCULATED','PENDING_SETTLEMENT','SETTLED') NOT NULL DEFAULT 'CALCULATED',
  settled_at DATETIME NULL,
  CONSTRAINT fk_dividend_order FOREIGN KEY (order_id) REFERENCES sales_order(id),
  CONSTRAINT fk_dividend_farmer FOREIGN KEY (farmer_id) REFERENCES farmer_profile(id),
  CONSTRAINT fk_dividend_plot FOREIGN KEY (plot_id) REFERENCES farm_plot(id)
) ENGINE=InnoDB COMMENT '平台销售分红';

-- 6. 初始化角色和业务默认参数
INSERT INTO sys_role (role_code, role_name) VALUES
('FARMER','农户'),('CONSUMER','消费者'),('BANK','合作银行'),
('INSURANCE','保险公司'),('OPERATOR','品牌运营方'),('GOVERNMENT','政府监管'),('ADMIN','平台管理员')
ON DUPLICATE KEY UPDATE role_name=VALUES(role_name);

INSERT INTO insurance_product (product_name, insured_amount_per_mu, premium_rate, government_subsidy_rate)
VALUES ('丹邱丝苗米种植保险', 1500, 0.05, 0.80);

-- 常用查询示例
-- 贷款建议：面积 × 800 元/亩
-- 保险保额：面积 × 1500 元/亩
-- 总保费：保额 × 5%，农户自缴：总保费 × 20%
-- 理赔金额：保额 × disaster_rate
-- 溯源入口：SELECT ... FROM trace_code JOIN farm_plot ... WHERE code = ?
