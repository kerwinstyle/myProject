#!/usr/bin/env python3
"""
SQLite数据库(.db文件)处理Handler
支持：查看表、查询数据、增删改数据
"""

import sqlite3
import os
import re
from typing import Any, Dict, List, Optional

# 全局变量存储当前数据库连接和路径
_current_db_path: Optional[str] = None
_current_conn: Optional[sqlite3.Connection] = None


def _get_db_path(user_input: str) -> Optional[str]:
    """从用户输入中提取数据库文件路径"""
    # 直接提取.db/.sqlite文件
    words = user_input.replace('"', ' ').replace("'", ' ').split()
    for word in words:
        if word.endswith('.db') or word.endswith('.sqlite') or word.endswith('.sqlite3'):
            if os.path.exists(word):
                return word
    
    # 检查/workspace目录下的.db文件
    for filename in os.listdir('/workspace'):
        if filename.endswith('.db') or filename.endswith('.sqlite'):
            return os.path.join('/workspace', filename)
    
    # 检查/root/uploads目录
    for filename in os.listdir('/root/uploads'):
        if filename.endswith('.db') or filename.endswith('.sqlite'):
            return os.path.join('/root/uploads', filename)
    
    return None


def _ensure_connection(db_path: str) -> sqlite3.Connection:
    """确保数据库连接有效"""
    global _current_db_path, _current_conn
    
    if _current_conn is not None and _current_db_path == db_path:
        return _current_conn
    
    # 关闭旧连接
    if _current_conn is not None:
        try:
            _current_conn.close()
        except:
            pass
    
    # 创建新连接
    _current_conn = sqlite3.connect(db_path)
    _current_conn.row_factory = sqlite3.Row
    _current_db_path = db_path
    
    return _current_conn


def list_tables(db_path: str) -> Dict[str, Any]:
    """
    列出数据库中所有表
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        包含表列表的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    return {
        "success": True,
        "db_file": os.path.basename(db_path),
        "table_count": len(tables),
        "tables": tables
    }


def get_table_schema(db_path: str, table_name: str) -> Dict[str, Any]:
    """
    获取表结构信息
    
    Args:
        db_path: 数据库文件路径
        table_name: 表名
        
    Returns:
        包含表结构的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": bool(row[3]),
            "default_value": row[4],
            "primary_key": bool(row[5])
        })
    
    return {
        "success": True,
        "table": table_name,
        "columns": columns,
        "column_count": len(columns)
    }


def get_table_data(db_path: str, table_name: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    获取表的全部数据（与源文件完全一致）
    
    Args:
        db_path: 数据库文件路径
        table_name: 表名
        limit: 可选的行数限制
        
    Returns:
        包含表数据的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    # 获取结构
    schema = get_table_schema(db_path, table_name)
    
    # 获取数据
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # 转换为字典列表
    data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(schema["columns"]):
            row_dict[col["name"]] = row[i]
        data.append(row_dict)
    
    return {
        "success": True,
        "table": table_name,
        "schema": schema,
        "data": data,
        "row_count": len(data),
        "total_rows": len(data)
    }


def execute_query(db_path: str, sql: str) -> Dict[str, Any]:
    """
    执行SQL查询（仅SELECT语句）
    
    Args:
        db_path: 数据库文件路径
        sql: SQL查询语句
        
    Returns:
        包含查询结果的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    sql = sql.strip()
    
    # 安全检查：只允许SELECT语句
    if not sql.lower().startswith('select'):
        return {
            "success": False,
            "error": "只允许执行SELECT查询语句"
        }
    
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            data.append(row_dict)
        
        return {
            "success": True,
            "query": sql,
            "columns": columns,
            "data": data,
            "row_count": len(data)
        }
        
    except sqlite3.Error as e:
        return {
            "success": False,
            "error": str(e)
        }


def insert_data(db_path: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    插入新数据
    
    Args:
        db_path: 数据库文件路径
        table_name: 表名
        data: 要插入的数据字典
        
    Returns:
        包含插入结果的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    columns = list(data.keys())
    placeholders = ','.join(['?' for _ in columns])
    values = list(data.values())
    
    sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        
        return {
            "success": True,
            "operation": "insert",
            "table": table_name,
            "inserted_id": cursor.lastrowid,
            "affected_rows": cursor.rowcount,
            "data": data
        }
        
    except sqlite3.Error as e:
        conn.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def update_data(db_path: str, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新数据
    
    Args:
        db_path: 数据库文件路径
        table_name: 表名
        data: 要更新的数据字典
        where: 条件字典
        
    Returns:
        包含更新结果的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    set_clause = ','.join([f"{k} = ?" for k in data.keys()])
    where_clause = ' AND '.join([f"{k} = ?" for k in where.keys()])
    
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    values = list(data.values()) + list(where.values())
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        
        return {
            "success": True,
            "operation": "update",
            "table": table_name,
            "affected_rows": cursor.rowcount,
            "set_values": data,
            "where_conditions": where
        }
        
    except sqlite3.Error as e:
        conn.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def delete_data(db_path: str, table_name: str, where: Dict[str, Any]) -> Dict[str, Any]:
    """
    删除数据
    
    Args:
        db_path: 数据库文件路径
        table_name: 表名
        where: 条件字典
        
    Returns:
        包含删除结果的字典
    """
    conn = _ensure_connection(db_path)
    cursor = conn.cursor()
    
    where_clause = ' AND '.join([f"{k} = ?" for k in where.keys()])
    sql = f"DELETE FROM {table_name} WHERE {where_clause}"
    values = list(where.values())
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        
        return {
            "success": True,
            "operation": "delete",
            "table": table_name,
            "affected_rows": cursor.rowcount,
            "where_conditions": where
        }
        
    except sqlite3.Error as e:
        conn.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def close_connection() -> None:
    """关闭数据库连接"""
    global _current_conn, _current_db_path
    
    if _current_conn is not None:
        try:
            _current_conn.close()
        except:
            pass
        _current_conn = None
        _current_db_path = None


def handle(user_input: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    主处理函数 - 根据用户输入执行相应操作
    
    Args:
        user_input: 用户输入的命令
        params: 可选的参数字典
        
    Returns:
        包含操作结果的字典
    """
    params = params or {}
    
    # 获取数据库路径
    db_path = params.get('db_path')
    if not db_path:
        db_path = _get_db_path(user_input)
    
    if not db_path:
        return {
            "success": False,
            "error": "未找到数据库文件。请提供.db文件的路径，或将文件上传到/workspace目录"
        }
    
    if not os.path.exists(db_path):
        return {
            "success": False,
            "error": f"数据库文件不存在: {db_path}"
        }
    
    input_lower = user_input.lower()
    
    # 列出所有表
    if '列出' in user_input and '表' in user_input:
        return list_tables(db_path)
    
    # 查看表数据
    if '查看' in user_input or '显示' in user_input or ('表' in user_input and 'data' in params):
        table_match = re.search(r'[表查看显示]\s+(\w+)', user_input)
        if table_match:
            table_name = table_match.group(1)
            return get_table_data(db_path, table_name)
    
    # 查询数据
    if '查询' in user_input or 'select' in input_lower:
        sql_match = re.search(r'(select\s+.+)', user_input, re.IGNORECASE)
        if sql_match:
            return execute_query(db_path, sql_match.group(1))
    
    # 插入数据
    if '插入' in user_input or '新增' in user_input:
        table_match = re.search(r'[到在]\s*(\w+)\s*表', user_input)
        if table_match and 'data' in params:
            return insert_data(db_path, table_match.group(1), params['data'])
    
    # 更新数据
    if '更新' in user_input or '修改' in user_input:
        table_match = re.search(r'[表]\s*(\w+)', user_input)
        if table_match and 'data' in params and 'where' in params:
            return update_data(db_path, table_match.group(1), params['data'], params['where'])
    
    # 删除数据
    if '删除' in user_input:
        table_match = re.search(r'[表]\s*(\w+)', user_input)
        if table_match and 'where' in params:
            return delete_data(db_path, table_match.group(1), params['where'])
    
    # 默认：列出所有表
    return list_tables(db_path)


__all__ = [
    'handle',
    'list_tables',
    'get_table_schema',
    'get_table_data',
    'execute_query',
    'insert_data',
    'update_data',
    'delete_data',
    'close_connection'
]


if __name__ == "__main__":
    print("DB Reader Skill Handler v1.0.0")
    print("=" * 50)
    print("Available functions:")
    print("  - list_tables(db_path): 列出所有表")
    print("  - get_table_schema(db_path, table_name): 获取表结构")
    print("  - get_table_data(db_path, table_name): 获取表全部数据")
    print("  - execute_query(db_path, sql): 执行SQL查询")
    print("  - insert_data(db_path, table_name, data): 插入数据")
    print("  - update_data(db_path, table_name, data, where): 更新数据")
    print("  - delete_data(db_path, table_name, where): 删除数据")
