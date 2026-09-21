"""数据库访问层:查询与写入(含事务)。"""

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

import pymysql
from fastapi import HTTPException

from backend.config import DB_CONFIG


def normalize(value: Any) -> Any:
    """把 MySQL 驱动返回的类型转换为可 JSON 序列化的类型。"""
    if isinstance(value, Decimal):
        return float(value)
    return value


def _rows_to_dict(rows: list) -> list[dict[str, Any]]:
    return [{key: normalize(value) for key, value in row.items()} for row in rows]


def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """执行只读查询,返回字典列表。"""
    try:
        with pymysql.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                return _rows_to_dict(cursor.fetchall())
    except pymysql.MySQLError as exc:
        raise HTTPException(status_code=503, detail=f"数据库连接失败: {exc}") from exc


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None


@contextmanager
def transaction() -> Iterator[dict[str, Any]]:
    """写事务:yield {'conn', 'cursor'},正常退出提交,异常回滚。

    用法:
        with transaction() as tx:
            tx["cursor"].execute(sql, params)
            new_id = tx["cursor"].lastrowid
    """
    connection = pymysql.connect(**DB_CONFIG)
    try:
        connection.begin()
        with connection.cursor() as cursor:
            yield {"conn": connection, "cursor": cursor}
        connection.commit()
    except pymysql.MySQLError as exc:
        connection.rollback()
        raise HTTPException(status_code=503, detail=f"数据库写入失败: {exc}") from exc
    finally:
        connection.close()
