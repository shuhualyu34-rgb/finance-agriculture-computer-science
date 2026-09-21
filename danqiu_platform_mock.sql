-- 丹邱丝苗米普惠产融服务平台 Mock 演示数据
-- 使用前先执行 danqiu_platform_schema.sql
USE danqiu_rice;

INSERT INTO sys_user (id, username, real_name, phone) VALUES
(1,'farmer_chen','陈伟','13800000001'),
(2,'farmer_huang','黄秀兰','13800000002'),
(3,'farmer_li','李梅','13800000003'),
(4,'consumer_demo','演示消费者','13900000001'),
(5,'operator_demo','品牌运营员','13700000001'),
(6,'gov_demo','朱村街监管员','13600000001'),
(7,'bank_demo','合作银行专员','13500000001'),
(8,'insurance_demo','保险公司专员','13400000001'),
(9,'admin_demo','平台管理员','13300000001');

INSERT INTO sys_user_role (user_id, role_id)
SELECT u.id, r.id FROM sys_user u JOIN sys_role r ON
  (u.id IN (1,2,3) AND r.role_code='FARMER') OR
  (u.id=4 AND r.role_code='CONSUMER') OR
  (u.id=5 AND r.role_code='OPERATOR') OR
  (u.id=6 AND r.role_code='GOVERNMENT') OR
  (u.id=7 AND r.role_code='BANK') OR
  (u.id=8 AND r.role_code='INSURANCE') OR
  (u.id=9 AND r.role_code='ADMIN');

INSERT INTO farmer_profile (id, user_id, village, address, certification_status, certification_at) VALUES
(1,1,'丹邱村','丹邱村东片 3 号地块附近','CERTIFIED','2026-09-10 10:00:00'),
(2,2,'丹邱村','丹邱村北片 8 号地块附近','PENDING',NULL),
(3,3,'丹邱村','丹邱村西片 6 号地块附近','CERTIFIED','2026-08-22 15:30:00');

INSERT INTO production_season (id, season_code, season_name, sowing_date, harvest_date, status) VALUES
(1,'DQ-2026-LATE','2026 年晚造丝苗米','2026-06-18','2026-09-16','HARVESTED'),
(2,'DQ-2026-EARLY','2026 年早造丝苗米','2026-02-20','2026-06-28','CLOSED');

INSERT INTO farm_plot (id, plot_code, farmer_id, plot_name, village, area_mu, variety, longitude, latitude, satellite_image_url) VALUES
(1,'DQ-PLOT-003',1,'丹邱村 3 号地块','丹邱村',18.60,'增科新选丝苗1号',113.6971000,23.2874000,'mock/satellite-plot-003.jpg'),
(2,'DQ-PLOT-008',2,'丹邱村 8 号地块','丹邱村',12.20,'增科新选丝苗1号',113.7012000,23.2911000,'mock/satellite-plot-008.jpg'),
(3,'DQ-PLOT-006',3,'丹邱村 6 号地块','丹邱村',13.00,'增科新选丝苗1号',113.6946000,23.2842000,'mock/satellite-plot-006.jpg');

INSERT INTO farm_record (id, plot_id, season_id, record_type, record_date, description, material_name, material_amount, output_jin, submitted_by, status) VALUES
(1,1,1,'SOWING','2026-06-18','完成晚造播种，使用认证品种。',NULL,NULL,NULL,1,'VERIFIED'),
(2,1,1,'FERTILIZING','2026-07-10','按标准完成第一次追肥。','有机复合肥',42,NULL,1,'VERIFIED'),
(3,1,1,'IRRIGATION','2026-08-04','完成关键农时灌溉。',NULL,NULL,NULL,1,'VERIFIED'),
(4,1,1,'HARVEST','2026-09-16','完成收割，产量稳定。',NULL,NULL,9300,1,'VERIFIED'),
(5,2,1,'SOWING','2026-06-21','已上传播种记录。',NULL,NULL,NULL,2,'SUBMITTED'),
(6,3,1,'HARVEST','2026-09-14','完成收割记录。',NULL,NULL,6550,3,'VERIFIED');

INSERT INTO standard_version (id, version_no, title, status, published_at) VALUES
(1,'DQ-SM-2026-V1','丹邱丝苗米全链条生产与品牌使用标准 V1.0','PUBLISHED','2026-03-01 09:00:00');

INSERT INTO standard_clause (id, standard_id, stage, clause_code, clause_name, requirement) VALUES
(1,1,'PLANTING','PL-001','品种要求','使用增科新选丝苗1号等备案品种'),
(2,1,'PLANTING','PL-002','投入品管理','肥料以有机肥为主，农药使用限定清单'),
(3,1,'QUALITY','QU-001','米质检测','碎米率不高于 5%，垩白度不高于 3%'),
(4,1,'PACKAGING','PK-001','包装溯源','统一规格包装，每包附一批一码溯源码');

INSERT INTO farmer_certification (id, farmer_id, plot_id, standard_id, status, reviewer_id, review_note, reviewed_at) VALUES
(1,1,1,1,'APPROVED',5,'资料齐全，农事记录完整。','2026-09-10 10:00:00'),
(2,2,2,1,'RECTIFYING',5,'缺少施肥记录，需补充。',NULL),
(3,3,3,1,'APPROVED',5,'已通过现场核验。','2026-08-22 15:30:00');

INSERT INTO certification_check (certification_id, clause_id, result, note) VALUES
(1,1,'PASS','品种照片与采购记录一致'),(1,2,'PASS','农事记录未发现违规投入品'),
(1,3,'PASS','检测报告已上传'),(1,4,'PASS','溯源码已绑定');

INSERT INTO field_inspection (plot_id, inspector_id, inspection_date, result, difference_note, rectification_required) VALUES
(1,6,'2026-09-12','PASS','现场面积与农户申报一致，生产记录可核验。',FALSE),
(3,6,'2026-09-09','WARNING','产量记录存在小幅差异，已要求补充说明。',TRUE);

INSERT INTO insurance_policy (id, policy_no, farmer_id, plot_id, product_id, insured_area_mu, insured_amount, total_premium, farmer_premium, status) VALUES
(1,'POL-DQ-2026-0001',1,1,1,18.60,27900,1395,279,'ACTIVE'),
(2,'POL-DQ-2026-0002',3,3,1,13.00,19500,975,195,'ACTIVE');

INSERT INTO insurance_claim (id, claim_no, policy_id, disaster_note, disaster_rate, claim_amount, entered_by, reviewed_by, status, reviewed_at) VALUES
(1,'CLM-2026-008',1,'台风强降雨造成部分倒伏。',0.30,8370,9,8,'APPROVED','2026-09-18 16:40:00'),
(2,'CLM-2026-007',2,'连续降雨影响局部产量。',0.15,2925,9,NULL,'UNDER_REVIEW',NULL);

INSERT INTO loan_application (id, application_no, farmer_id, plot_id, area_mu, suggested_amount, risk_level, bank_result) VALUES
(1,'LOAN-DQ-2026-0001',1,1,18.60,14880,'LOW','APPROVED'),
(2,'LOAN-DQ-2026-0002',2,2,12.20,9760,'MEDIUM','PENDING');

INSERT INTO trace_code (id, code, plot_id, season_id, batch_name, product_grade, quality_report_url) VALUES
(1,'DQ2026SM000001',1,1,'丹邱村 3 号地块晚造批次','SPECIAL','mock/quality-DQ2026SM000001.pdf'),
(2,'DQ2026SM000002',3,1,'丹邱村 6 号地块晚造批次','FIRST','mock/quality-DQ2026SM000002.pdf');

INSERT INTO product (id, trace_code_id, product_name, specification, price, stock) VALUES
(1,1,'丹邱丝苗米 特级','5kg',89,320),
(2,1,'丹邱丝苗米 特级','10kg',168,120),
(3,2,'丹邱丝苗米 一级','5kg',69,260);

INSERT INTO adoption_order (id, order_no, consumer_user_id, plot_id, fee, status) VALUES
(1,'ADOPT-DQ-2026-0001',4,1,199,'ACTIVE');

INSERT INTO sales_order (id, order_no, consumer_user_id, total_amount, source, status, address_snapshot, paid_at, shipped_at) VALUES
(1,'ORD-DQ-2026-0001',4,178,'PLATFORM','SHIPPED','{"name":"演示消费者","phone":"13900000001","address":"广州市天河区演示地址"}','2026-09-18 11:20:00','2026-09-18 16:30:00'),
(2,'ORD-DQ-2026-0002',4,89,'PLATFORM','PAID','{"name":"演示消费者","phone":"13900000001","address":"广州市天河区演示地址"}','2026-09-19 09:15:00',NULL);

INSERT INTO sales_order_item (order_id, product_id, plot_id, quantity, unit_price, amount) VALUES
(1,1,1,2,89,178),(2,1,1,1,89,89);

INSERT INTO shipment (order_id, carrier, tracking_no, shipped_at) VALUES
(1,'顺丰速运','SF202609180001','2026-09-18 16:30:00');

INSERT INTO farmer_dividend (order_id, farmer_id, plot_id, base_amount, dividend_rate, dividend_amount, status) VALUES
(1,1,1,178,0.15,26.70,'SETTLED'),
(2,1,1,89,0.15,13.35,'PENDING_SETTLEMENT');

INSERT INTO regulatory_report (report_type, report_period, content_json, status, confirmed_by, confirmed_at) VALUES
('MONTHLY','2026-08','{"certifiedFarmers":116,"complianceRate":92.8,"missingRecords":21,"insurancePolicies":88,"loanApplications":14,"salesAmount":724000}','ARCHIVED',6,'2026-09-01 10:00:00'),
('WEEKLY','2026-W38','{"certifiedFarmers":128,"complianceRate":94.6,"missingRecords":17,"rectificationEvents":6}','DRAFT',NULL,NULL);
