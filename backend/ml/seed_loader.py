"""种子 SQL 解析器:把仓库内已提交的 INSERT 语句解析为内存表,供离线训练使用。

不依赖 MySQL/Docker,保证 `git clone` 后即可复现训练。
仅解析数据 INSERT,忽略建表语句、注释与其他语句。

用法:
    tables = load_seed_sql("danqiu_rice_seed.sql")
    farmers = tables["farmer_profile"]
"""

from __future__ import annotations

import re
from typing import Any

_INSERT_RE = re.compile(r"INSERT INTO `(\w+)`\s*\(([^)]*)\)\s*VALUES", re.IGNORECASE)


def _parse_value(token: str) -> Any:
    """把单个 SQL 字面量解析为 Python 值。"""
    token = token.strip()
    if not token:
        return None
    upper = token.upper()
    if upper == "NULL":
        return None
    if upper in ("TRUE",):
        return 1
    if upper in ("FALSE",):
        return 0
    if token.startswith("'"):
        # 去掉首尾引号,反转义 \\、\' 与 MySQL 双写引号 ''
        body = token[1:]
        if body.endswith("'"):
            body = body[:-1]
        return body.replace("''", "'").replace("\\'", "'").replace("\\\\", "\\")
    if token.startswith("b'"):
        return None
    # 数字
    try:
        if any(c in token for c in ".eE"):
            return float(token)
        return int(token)
    except ValueError:
        return token


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    """按顶层逗号切分,跳过单引号字符串。"""
    parts: list[str] = []
    buf: list[str] = []
    in_str = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "'" and not in_str:
            in_str = True
            buf.append(ch)
        elif ch == "'" and in_str:
            if i + 1 < n and text[i + 1] == "'":
                buf.append("''")
                i += 1
            else:
                in_str = False
                buf.append(ch)
        elif ch == "\\" and in_str and i + 1 < n:
            buf.append(ch)
            buf.append(text[i + 1])
            i += 1
        elif ch == sep and not in_str:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf))
    return parts


def _extract_rows(values_text: str) -> list[list[Any]]:
    """从 VALUES 文本中提取所有行元组。

    每个元组以顶层 `(` 开始、匹配的 `)` 结束;元组之间的逗号与空白跳过。
    """
    rows: list[list[Any]] = []
    in_str = False
    depth = 0
    buf: list[str] = []
    i = 0
    n = len(values_text)
    while i < n:
        ch = values_text[i]
        if ch == "'" and not in_str:
            in_str = True
            buf.append(ch)
        elif ch == "'" and in_str:
            if i + 1 < n and values_text[i + 1] == "'":
                buf.append("''")
                i += 1
            else:
                in_str = False
                buf.append(ch)
        elif ch == "\\" and in_str and i + 1 < n:
            buf.append(ch)
            buf.append(values_text[i + 1])
            i += 1
        elif ch == "(" and not in_str and depth == 0:
            depth = 1
            buf = [ch]
        elif ch == "(" and not in_str:
            depth += 1
            buf.append(ch)
        elif ch == ")" and not in_str:
            depth -= 1
            buf.append(ch)
            if depth == 0:
                inner = "".join(buf)[1:-1]
                rows.append([_parse_value(t) for t in _split_top_level(inner)])
                buf = []
        elif depth == 0:
            pass  # 元组之间的分隔符
        else:
            buf.append(ch)
        i += 1
    return rows


def load_seed_sql(path: str) -> dict[str, list[dict[str, Any]]]:
    """解析 SQL 文件,返回 {表名: [行字典,...]}。

    只处理 `INSERT INTO 表 (列...) VALUES ...;` 块;同名表多次 INSERT 时合并。
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    tables: dict[str, list[dict[str, Any]]] = {}
    for m in _INSERT_RE.finditer(text):
        table = m.group(1)
        cols = [c.strip().strip("`") for c in m.group(2).split(",")]
        start = m.end()
        # 找到该 INSERT 语句的结束分号(顶层)
        end = _statement_end(text, start)
        values_text = text[start:end]
        rows = _extract_rows(values_text)
        table_rows = tables.setdefault(table, [])
        for row in rows:
            table_rows.append(dict(zip(cols, row, strict=True)))
    return tables


def _statement_end(text: str, start: int) -> int:
    """从 start 开始扫描,返回该语句结束分号(;)的位置,跳过字符串。"""
    in_str = False
    n = len(text)
    i = start
    while i < n:
        ch = text[i]
        if ch == "'" and not in_str:
            in_str = True
        elif ch == "'" and in_str:
            if i + 1 < n and text[i + 1] == "'":
                i += 1
            else:
                in_str = False
        elif ch == "\\" and in_str and i + 1 < n:
            i += 1
        elif ch == ";" and not in_str:
            return i
        i += 1
    return n


def load_seed_tables(
    seed_path: str, include: set[str] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """加载种子数据并只保留需要的表。"""
    tables = load_seed_sql(seed_path)
    if include is None:
        return tables
    return {k: v for k, v in tables.items() if k in include}
