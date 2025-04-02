from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import json
import os

from ..utils.auth import verify_token
from .models import DatabaseConnection, DatabaseConfig

router = APIRouter(tags=["数据库管理"])

# 数据库配置文件路径
DB_CONFIG_FILE = "config\\db_config.json"
os.makedirs(os.path.dirname(DB_CONFIG_FILE), exist_ok=True)

@router.post("/database/test-connection")
async def test_connection(conn: DatabaseConnection):
    """测试数据库连接"""
    try:
        conn_str = f'mysql+pymysql://{conn.username}:{conn.password}@{conn.host}:{conn.port}'
        if conn.database:
            conn_str += f'/{conn.database}'
        
        engine = create_engine(conn_str)
        with engine.connect() as connection:
            return {"status": "success", "message": "连接成功"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/databases")
async def get_databases(conn: DatabaseConnection):
    """获取数据库列表"""
    try:
        conn_str = f'mysql+pymysql://{conn.username}:{conn.password}@{conn.host}:{conn.port}'
        engine = create_engine(conn_str)
        inspector = inspect(engine)
        databases = inspector.get_schema_names()
        print(databases)
        # 排除系统数据库并格式化返回数据
        user_databases = [{"name": db} for db in databases 
                         if db not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
        
        return {"status": "success", "data": user_databases}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/databases/{db_name}/tables")
async def get_tables(db_name: str, conn: DatabaseConnection):
    """获取指定数据库的表和视图"""
    try:
        # 使用相同的 engine，只是添加数据库名
        conn_str = f'mysql+pymysql://{conn.username}:{conn.password}@{conn.host}:{conn.port}/{db_name}'
        engine = create_engine(conn_str)
        inspector = inspect(engine)
        
        # 获取表和视图
        tables = inspector.get_table_names()
        views = inspector.get_view_names()
        
        return {
            "status": "success",
            "data": {
                "tables": tables,
                "views": views
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/databases/{db_name}/tables/{table_name}/fields", dependencies=[Depends(verify_token)])
async def get_fields(db_name: str, table_name: str):
    """获取指定表的所有字段信息"""
    try:
        engine = create_engine(f'mysql+pymysql://root:sa123@localhost:3306/{db_name}')
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        
        # 获取字段注释
        with engine.connect() as connection:
            # 查询字段注释
            comment_query = text("""
                SELECT COLUMN_NAME, COLUMN_COMMENT 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name
            """)
            comment_result = connection.execute(comment_query, {"db_name": db_name, "table_name": table_name})
            comments = {row[0]: row[1] for row in comment_result}
        
        # 组合字段信息，包括注释
        fields = []
        for column in columns:
            field = {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column.get("nullable", True),
                "comment": comments.get(column["name"], "")  # 添加注释
            }
            fields.append(field)
        
        return {
            "status": "success",
            "data": {
                "fields": fields
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/database/config", dependencies=[Depends(verify_token)])
async def get_database_config():
    """获取全局数据库连接配置"""
    try:
        if not os.path.exists(DB_CONFIG_FILE):
            raise HTTPException(status_code=404, detail="数据库配置不存在")
        
        with open(DB_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return {"status": "success", "data": config}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/config", dependencies=[Depends(verify_token)])
async def save_database_config(config: DatabaseConfig):
    """保存全局数据库连接配置"""
    try:
        # 先测试连接
        conn_str = f'mysql+pymysql://{config.username}:{config.password}@{config.host}:{config.port}'
        engine = create_engine(conn_str)
        with engine.connect():
            pass  # 只测试连接是否成功
        
        # 保存配置到文件
        with open(DB_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config.dict(), f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "message": "数据库配置保存成功"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"数据库连接失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))