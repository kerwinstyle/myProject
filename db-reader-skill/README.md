# DB Reader Skill

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

SQLite数据库(.db文件)读取和处理Skill，支持查看表、查询、增删改数据。

## 功能特性

| 功能 | 说明 |
|------|------|
| 列出所有表 | 显示数据库中所有表名 |
| 查看表结构 | 显示表的列信息、数据类型、主键等 |
| 查看全量数据 | 显示表的全部数据（与源文件完全一致，不截断、不修改） |
| SQL查询 | 执行SELECT查询语句 |
| 插入数据 | 向表中插入新记录 |
| 更新数据 | 更新表中符合条件的记录 |
| 删除数据 | 删除表中符合条件的记录 |

## 安装

无需额外安装依赖，使用Python标准库`sqlite3`即可运行。

```bash
git clone https://github.com/your-username/db-reader-skill.git
cd db-reader-skill
```

## 使用方法

### 命令行使用

```bash
# 列出所有表
python db_skill.py /path/to/database.db list

# 查看表结构
python db_skill.py /path/to/database.db schema users

# 查看表所有数据
python db_skill.py /path/to/database.db data users

# 执行SQL查询
python db_skill.py /path/to/database.db query "SELECT * FROM users WHERE id=1"

# 插入数据
python db_skill.py /path/to/database.db insert users '{"name":"张三","age":25}'

# 更新数据
python db_skill.py /path/to/database.db update users '{"name":"李四"}' '{"id":1}'

# 删除数据
python db_skill.py /path/to/database.db delete users '{"id":1}'
```

### Python API

```python
from db_skill import DatabaseManager

# 连接数据库
db = DatabaseManager('/path/to/database.db')

# 获取所有表
tables = db.get_all_tables()
print(tables)

# 获取表结构
schema = db.get_table_info('users')
print(schema)

# 获取表所有数据（全量，不截断）
data = db.get_all_data('users')
print(data)

# 执行SQL查询
result = db.execute_query("SELECT * FROM users WHERE age > 30")
print(result)

# 插入数据
result = db.insert_row('users', {'name': '张三', 'age': 30})
print(result)

# 更新数据
result = db.update_row('users', {'age': 35}, {'id': 1})
print(result)

# 删除数据
result = db.delete_row('users', {'id': 1})
print(result)

# 关闭连接
db.close()
```

### 作为Skill Handler使用

```python
from handler import handle, list_tables, get_table_data, insert_data

# 通过handle函数处理用户输入
result = handle("列出所有表", {"db_path": "/path/to/database.db"})
print(result)

# 或直接调用具体函数
tables = list_tables("/path/to/database.db")
data = get_table_data("/path/to/database.db", "users")
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `skill.yaml` | Skill配置文件 |
| `handler.py` | 主处理模块（供Skill系统调用） |
| `db_skill.py` | 命令行工具和Python API |
| `README.md` | 说明文档 |
| `LICENSE` | MIT许可证 |

## 注意事项

1. **数据安全**: 读取操作不会修改源文件，只有插入、更新、删除操作会修改数据库
2. **全量数据**: `get_all_data` 方法返回表的全部数据，不会截断
3. **事务处理**: 增删改操作使用事务，确保数据一致性
4. **SQL安全**: 查询功能只允许SELECT语句，防止意外修改

## 依赖

- Python 3.7+
- sqlite3 (Python标准库，无需额外安装)

## License

[MIT License](LICENSE)
