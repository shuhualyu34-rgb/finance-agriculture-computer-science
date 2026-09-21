USE `Agriculture`;

CREATE TABLE producer_subject (
    subject_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主体ID',
    subject_type ENUM('FARMER', 'COOPERATIVE', 'PROCESSOR') NOT NULL COMMENT '主体类型：农户、合作社、加工企业',
    subject_name VARCHAR(200) NOT NULL COMMENT '主体名称',
    contact_phone VARCHAR(32) NULL COMMENT '联系方式',
    contact_person VARCHAR(100) NULL COMMENT '联系人',
    settlement_status ENUM('PENDING', 'ACTIVE', 'SUSPENDED', 'EXITED') NOT NULL DEFAULT 'PENDING' COMMENT '入驻状态：待审核、已入驻、暂停、退出',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at DATETIME NULL COMMENT '删除时间，非空表示逻辑删除',
    PRIMARY KEY (subject_id),
    KEY idx_subject_type_status (subject_type, settlement_status),
    KEY idx_subject_name (subject_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生产主体表';

CREATE TABLE product_batch (
    batch_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '批次ID',
    subject_id BIGINT UNSIGNED NOT NULL COMMENT '所属主体ID',
    category VARCHAR(100) NOT NULL COMMENT '产品品类',
    planting_area DECIMAL(12,2) NULL COMMENT '种植面积，单位：亩',
    expected_listing_date DATE NOT NULL COMMENT '预计上市日期',
    standard_execution_status ENUM('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'NOT_STARTED' COMMENT '当前标准执行状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at DATETIME NULL COMMENT '删除时间，非空表示逻辑删除',
    PRIMARY KEY (batch_id),
    KEY idx_batch_subject (subject_id),
    KEY idx_batch_listing_date (expected_listing_date),
    KEY idx_batch_category_date (category, expected_listing_date),
    KEY idx_batch_standard_status (standard_execution_status),
    CONSTRAINT fk_batch_subject FOREIGN KEY (subject_id) REFERENCES producer_subject (subject_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_planting_area CHECK (planting_area IS NULL OR planting_area >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='产品批次表';

CREATE TABLE standard_clause (
    standard_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '标准ID',
    applicable_category VARCHAR(100) NOT NULL COMMENT '适用品类',
    clause_content JSON NOT NULL COMMENT '标准条款内容，JSON格式',
    inspection_thresholds JSON NULL COMMENT '检测项与阈值，JSON格式',
    published_at DATETIME NOT NULL COMMENT '发布时间',
    version_no VARCHAR(32) NOT NULL COMMENT '标准版本号',
    standard_status ENUM('DRAFT', 'PUBLISHED', 'RETIRED') NOT NULL DEFAULT 'DRAFT' COMMENT '标准状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (standard_id),
    UNIQUE KEY uk_standard_category_version (applicable_category, version_no),
    KEY idx_standard_category_status (applicable_category, standard_status),
    KEY idx_standard_published_at (published_at),
    CONSTRAINT chk_clause_content_json CHECK (JSON_VALID(clause_content)),
    CONSTRAINT chk_inspection_thresholds_json CHECK (inspection_thresholds IS NULL OR JSON_VALID(inspection_thresholds))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标准条款表';

CREATE TABLE inspection_report (
    report_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报告ID',
    batch_id BIGINT UNSIGNED NOT NULL COMMENT '产品批次ID',
    inspection_agency VARCHAR(200) NOT NULL COMMENT '检测机构名称',
    inspection_result JSON NOT NULL COMMENT '检测结果，JSON格式',
    is_qualified BOOLEAN NULL COMMENT '是否合格：1合格，0不合格，NULL待判定',
    blockchain_hash CHAR(64) NULL COMMENT '上链存证哈希，默认存储SHA-256',
    inspected_at DATETIME NULL COMMENT '检测时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (report_id),
    KEY idx_report_batch (batch_id),
    KEY idx_report_qualified (is_qualified),
    KEY idx_report_agency (inspection_agency),
    UNIQUE KEY uk_report_blockchain_hash (blockchain_hash),
    CONSTRAINT fk_report_batch FOREIGN KEY (batch_id) REFERENCES product_batch (batch_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_inspection_result_json CHECK (JSON_VALID(inspection_result)),
    CONSTRAINT chk_blockchain_hash CHECK (blockchain_hash IS NULL OR blockchain_hash REGEXP '^[0-9A-Fa-f]{64}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='检测报告表';

CREATE TABLE brand_authorization (
    authorization_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '授权ID',
    subject_id BIGINT UNSIGNED NOT NULL COMMENT '主体ID',
    authorized_category VARCHAR(100) NOT NULL COMMENT '授权品类',
    authorization_start_date DATE NOT NULL COMMENT '授权开始日期',
    authorization_end_date DATE NOT NULL COMMENT '授权结束日期',
    authorization_status ENUM('PENDING', 'ACTIVE', 'EXPIRED', 'REVOKED') NOT NULL DEFAULT 'PENDING' COMMENT '授权状态',
    performance_metrics JSON NULL COMMENT '绩效指标，JSON格式',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (authorization_id),
    KEY idx_authorization_subject (subject_id),
    KEY idx_authorization_category_status (authorized_category, authorization_status),
    KEY idx_authorization_period (authorization_start_date, authorization_end_date),
    CONSTRAINT fk_authorization_subject FOREIGN KEY (subject_id) REFERENCES producer_subject (subject_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_authorization_period CHECK (authorization_end_date >= authorization_start_date),
    CONSTRAINT chk_performance_metrics_json CHECK (performance_metrics IS NULL OR JSON_VALID(performance_metrics))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='品牌授权记录表';

CREATE TABLE channel_order (
    order_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单ID',
    batch_id BIGINT UNSIGNED NOT NULL COMMENT '产品批次ID',
    channel_party VARCHAR(200) NOT NULL COMMENT '渠道方',
    order_amount DECIMAL(18,2) NOT NULL COMMENT '订单金额',
    settlement_status ENUM('PENDING', 'PARTIAL', 'SETTLED', 'CANCELLED') NOT NULL DEFAULT 'PENDING' COMMENT '结算状态',
    order_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    settled_at DATETIME NULL COMMENT '结算时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (order_id),
    KEY idx_order_batch (batch_id),
    KEY idx_order_channel (channel_party),
    KEY idx_order_settlement_status (settlement_status),
    KEY idx_order_time (order_time),
    CONSTRAINT fk_order_batch FOREIGN KEY (batch_id) REFERENCES product_batch (batch_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_order_amount CHECK (order_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='渠道订单表';

SHOW TABLES;
