"""增量迁移执行器:应用启动时把 migrations/ 中的 SQL 补齐到数据库。

背景:docker-entrypoint-initdb.d 只在全新数据卷上执行,存量数据库永远
拿不到后续迁移(如 004 保险产品矩阵)。本模块在 API 启动时运行,对全新卷
与存量卷都保证迁移完整。

幂等策略:
- _schema_migrations 表记录已应用的迁移文件,已记录则跳过;
- 旧数据卷曾被 initdb.d 应用过但未记录的迁移,用探针(列/表是否存在)
  识别后只补登记、不重复执行;
- 002/003_add_rice_products 这类天然幂等(UPDATE / INSERT ... WHERE NOT
  EXISTS)的脚本不受探针限制,未记录时直接执行。
"""

import os
import time

import pymysql

from backend.config import DB_CONFIG

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations"
)

# 探针:迁移文件名 -> (类型, 表, 列),用于识别旧卷上已被 initdb.d 应用过的迁移
PROBES = {
    "001_open_for_adoption.sql": ("column", "farm_plot", "open_for_adoption"),
    "003_farmer_income.sql": ("table", "farmer_income", None),
    "004_insurance_product_matrix.sql": ("column", "insurance_product", "product_code"),
}


def _connect():
    return pymysql.connect(**DB_CONFIG)


def _ensure_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS _schema_migrations (
          name VARCHAR(128) PRIMARY KEY,
          applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB COMMENT '迁移执行记录'
        """
    )


def _applied(cursor) -> set[str]:
    cursor.execute("SELECT name FROM _schema_migrations")
    return {row["name"] for row in cursor.fetchall()}


def _probe_applied(cursor, marker) -> bool:
    kind, table, column = marker
    if kind == "table":
        cursor.execute(
            "SELECT COUNT(*) AS n FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table,),
        )
    else:
        cursor.execute(
            "SELECT COUNT(*) AS n FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table, column),
        )
    return cursor.fetchone()["n"] > 0


def _split_statements(sql_text: str) -> list[str]:
    """按分号切分(迁移脚本不含存储过程/触发器,无需更复杂的解析)。"""
    statements = []
    for chunk in sql_text.split(";"):
        lines = [ln for ln in chunk.splitlines() if not ln.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            statements.append(stmt)
    return statements


def run_migrations() -> list[str]:
    """执行未应用的迁移,返回动作日志。"""
    actions: list[str] = []
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            _ensure_table(cursor)
            applied = _applied(cursor)
            for name in sorted(os.listdir(MIGRATIONS_DIR)):
                if not name.endswith(".sql") or name in applied:
                    continue
                marker = PROBES.get(name)
                if marker and _probe_applied(cursor, marker):
                    # 旧数据卷:initdb.d 曾执行过但未记录,只补登记
                    cursor.execute("INSERT INTO _schema_migrations (name) VALUES (%s)", (name,))
                    actions.append(f"基线登记(旧卷已应用): {name}")
                    continue
                path = os.path.join(MIGRATIONS_DIR, name)
                with open(path, encoding="utf-8") as fh:
                    for stmt in _split_statements(fh.read()):
                        cursor.execute(stmt)
                cursor.execute("INSERT INTO _schema_migrations (name) VALUES (%s)", (name,))
                actions.append(f"已应用: {name}")
    finally:
        conn.close()
    return actions


def run_with_retry(attempts: int = 10, interval: float = 3.0) -> None:
    """供应用启动调用:等待数据库就绪并执行迁移;最终失败只告警,不阻断启动。"""
    for i in range(1, attempts + 1):
        try:
            actions = run_migrations()
            for action in actions:
                print(f"[migrate] {action}", flush=True)
            if not actions:
                print("[migrate] 数据库已是最新", flush=True)
            return
        except pymysql.MySQLError as exc:
            print(f"[migrate] 第 {i}/{attempts} 次执行失败: {exc}", flush=True)
            if i < attempts:
                time.sleep(interval)
    print(
        "[migrate] 多次重试仍未成功,服务继续启动;"
        "请检查数据库后手动执行: python -m backend.migrate",
        flush=True,
    )


if __name__ == "__main__":
    run_with_retry()
