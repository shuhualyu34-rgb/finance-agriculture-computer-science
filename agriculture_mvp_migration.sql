USE `Agriculture`;

-- 初期闭环增量迁移
-- 目标：主体 → 批次 → 主标准 → 品控检测 → 品牌授权 → 溯源查询
-- 说明：所有新增字段均保持可空，便于试点阶段继续调整，不引入复杂拆分表。

ALTER TABLE product_batch
    ADD COLUMN batch_code VARCHAR(64) NULL COMMENT '对外展示的批次编号' AFTER batch_id,
    ADD COLUMN standard_id BIGINT UNSIGNED NULL COMMENT '试点阶段绑定的主标准版本' AFTER category,
    ADD COLUMN trace_code VARCHAR(64) NULL COMMENT '试点阶段一批一码溯源码' AFTER standard_execution_status,
    ADD UNIQUE KEY uk_batch_code (batch_code),
    ADD UNIQUE KEY uk_batch_trace_code (trace_code),
    ADD KEY idx_batch_standard (standard_id),
    ADD CONSTRAINT fk_batch_standard FOREIGN KEY (standard_id)
        REFERENCES standard_clause (standard_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE inspection_report
    ADD COLUMN report_file_url VARCHAR(500) NULL COMMENT '检测报告文件地址' AFTER inspection_result;

