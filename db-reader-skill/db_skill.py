#!/usr/bin/env python3
"""
DB Reader Skill - SQLite数据库命令行工具
提供完整的数据库读取和操作功能
"""

import sqlite3
import os
import sys
import json
from typing import Any, Dict, List


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.connect()
    
    def connect(self):
        """连接数据库"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print(f"✓ 已连接到数据库: {os.path.basename(self.db_path)}")
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """获取表结构信息"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default": row[4],
                "pk": bool(row[5])
            })
        return columns
    
    def get_all_data(self, table_name: str) -> Dict[str, Any]:
        """获取表的所有数据"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            data.append(row_dict)
        
        return {
            "columns": columns,
            "data": data,
            "total_rows": len(data)
        }
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """执行SELECT查询"""
        cursor = self.conn.cursor()
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
                "columns": columns,
                "data": data,
                "row_count": len(data)
            }
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def insert_row(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """插入数据"""
        cursor = self.conn.cursor()
        columns = list(data.keys())
        placeholders = ','.join(['?' for _ in columns])
        values = list(data.values())
        
        sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(sql, values)
            self.conn.commit()
            return {
                "success": True,
                "inserted_id": cursor.lastrowid,
                "affected_rows": cursor.rowcount
            }
        except sqlite3.Error as e:
            self.conn.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_row(self, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> Dict[str, Any]:
        """更新数据"""
        cursor = self.conn.cursor()
        
        set_clause = ','.join([f"{k} = ?" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = ?" for k in where.keys()])
        
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(where.values())
        
        try:
            cursor.execute(sql, values)
            self.conn.commit()
            return {
                "success": True,
                "affected_rows": cursor.rowcount
            }
        except sqlite3.Error as e:
            self.conn.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_row(self, table_name: str, where: Dict[str, Any]) -> Dict[str, Any]:
        """删除数据"""
        cursor = self.conn.cursor()
        
        where_clause = ' AND '.join([f"{k} = ?" for k in where.keys()])
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        values = list(where.values())
        
        try:
            cursor.execute(sql, values)
            self.conn.commit()
            return {
                "success": True,
                "affected_rows": cursor.rowcount
            }
        except sqlite3.Error as e:
            self.conn.rollback()
            return {
                "success": False,
                "error": str(e)
            }


def format_table(data: List[Dict], columns: List[str]) -> str:
    """格式化表格输出"""
    if not data:
        return "无数据"
    
    # 计算每列宽度
    col_widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            value = str(row.get(col, ''))
            col_widths[col] = max(col_widths[col], len(value))
    
    # 限制最大宽度
    max_width = 50
    for col in col_widths:
        col_widths[col] = min(col_widths[col], max_width)
    
    # 表头
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)
    
    # 数据行
    rows = []
    for row in data:
        row_str = " | ".join(str(row.get(col, ''))[:max_width].ljust(col_widths[col]) for col in columns)
        rows.append(row_str)
    
    return f"{header}\n{separator}\n" + "\n".join(rows)


def format_json(data: Any, indent: int = 2) -> str:
    """格式化JSON输出"""
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("DB Reader Skill - SQLite数据库命令行工具")
        print()
        print("用法: python db_skill.py <db文件路径> [命令] [参数]")
        print()
        print("命令:")
        print("  list              - 列出所有表")
        print("  schema <表名>     - 显示表结构")
        print("  data <表名>       - 显示表所有数据")
        print("  query <SQL>       - 执行SQL查询")
        print("  insert <表名> <JSON数据>")
        print("  update <表名> <JSON数据> <JSON条件>")
        print("  delete <表名> <JSON条件>")
        print()
        print("示例:")
        print("  python db_skill.py database.db list")
        print("  python db_skill.py database.db data users")
        print("  python db_skill.py database.db query \"SELECT * FROM users\"")
        return
    
    db_path = sys.argv[1]
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return
    
    db = DatabaseManager(db_path)
    
    if len(sys.argv) == 2:
        tables = db.get_all_tables()
        print("\n数据库中的表:")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        return
    
    command = sys.argv[2] if len(sys.argv) > 2 else "list"
    
    try:
        if command == "list":
            tables = db.get_all_tables()
            print("\n数据库中的表:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
        
        elif command == "schema":
            if len(sys.argv) < 4:
                print("错误: 请指定表名")
                return
            table_name = sys.argv[3]
            info = db.get_table_info(table_name)
            print(f"\n表 {table_name} 结构:")
            print(format_json(info))
        
        elif command == "data":
            if len(sys.argv) < 4:
                print("错误: 请指定表名")
                return
            table_name = sys.argv[3]
            result = db.get_all_data(table_name)
            print(f"\n表 {table_name} 数据 (共 {result['total_rows']} 行):")
            print(format_table(result['data'], result['columns']))
        
        elif command == "query":
            if len(sys.argv) < 4:
                print("错误: 请指定SQL语句")
                return
            sql = ' '.join(sys.argv[3:])
            result = db.execute_query(sql)
            if result['success']:
                print(f"\n查询结果 ({result['row_count']} 行):")
                print(format_table(result['data'], result['columns']))
            else:
                print(f"错误: {result['error']}")
        
        elif command == "insert":
            if len(sys.argv) < 5:
                print("错误: 请指定表名和JSON数据")
                return
            table_name = sys.argv[3]
            data = json.loads(sys.argv[4])
            result = db.insert_row(table_name, data)
            if result['success']:
                print(f"✓ 插入成功，ID: {result['inserted_id']}")
            else:
                print(f"错误: {result['error']}")
        
        elif command == "update":
            if len(sys.argv) < 6:
                print("错误: 请指定表名、JSON数据和JSON条件")
                return
            table_name = sys.argv[3]
            data = json.loads(sys.argv[4])
            where = json.loads(sys.argv[5])
            result = db.update_row(table_name, data, where)
            if result['success']:
                print(f"✓ 更新成功，影响行数: {result['affected_rows']}")
            else:
                print(f"错误: {result['error']}")
        
        elif command == "delete":
            if len(sys.argv) < 5:
                print("错误: 请指定表名和JSON条件")
                return
            table_name = sys.argv[3]
            where = json.loads(sys.argv[4])
            result = db.delete_row(table_name, where)
            if result['success']:
                print(f"✓ 删除成功，影响行数: {result['affected_rows']}")
            else:
                print(f"错误: {result['error']}")
        
        else:
            print(f"未知命令: {command}")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
