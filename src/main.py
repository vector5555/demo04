from fastapi import FastAPI, Request, Body, Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os

from .model.query_model import QueryModel
from .protocol.query_protocol import QueryRequest, QueryResponse
from .utils.auth import verify_token, create_access_token, verify_password
from .config.auth_db import AuthBase, auth_engine, AuthSessionLocal
from .database.models.user import User
from .database.models.role import Role, UserRole, RolePermission
from sqlalchemy import and_
# 在现有导入后添加
from werkzeug.security import generate_password_hash
from .database.models.role import RolePermission
from typing import List
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
# 在现有导入后添加
from sqlalchemy.pool import QueuePool

app = FastAPI()
security = HTTPBearer()

# 初始化认证数据库
AuthBase.metadata.create_all(bind=auth_engine)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置信息
DB_URL = "mysql+pymysql://root:sa123@localhost:3306/air"  # 目标查询数据库
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-073ca480b9184dcf9e1be31f805a356b"

# 初始化查询模型
try:
    print("正在初始化查询模型...")
    query_model = QueryModel(
        db_url=DB_URL,
        api_key=API_KEY,
        api_url=DEEPSEEK_API_URL
    )
    print("查询模型初始化成功")
except Exception as e:
    print(f"查询模型初始化失败: {str(e)}")
    raise

# 数据库依赖
def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 认证路由
# 修改登录路由
@app.post("/login")
async def login(username: str = Body(...), password: str = Body(...), db: Session = Depends(get_auth_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 获取用户角色
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    roles = []
    for user_role in user_roles:
        role = db.query(Role).filter(Role.id == user_role.role_id).first()
        if role:
            roles.append(role.role_name)
    
    token = create_access_token({
        "sub": user.username,
        "roles": roles,
        "user_id": user.id
    })
    return {"token": token}

# 其他路由保持不变
@app.post("/query_nl", dependencies=[Depends(verify_token)])
async def process_query(request: QueryRequest) -> QueryResponse:
    try:
        print(f"收到查询请求: {request.query_text}")
        
        context_id = request.context_id or query_model.context_manager.create_context()
        print(f"上下文ID: {context_id}")
        
        sql = await query_model.generate_sql(request.query_text, context_id)
        print(f"生成的SQL: {sql}")
        
        print("开始执行SQL查询...")
        result = await query_model.execute_query(sql)
        print(f"查询结果: {result}")
        
        query_model.context_manager.update_context(context_id, {
            'query': request.query_text,
            'sql': sql,
            'result': result,
            'state': 'completed'
        })
        
        return QueryResponse(
            sql=sql,
            result=result,
            context_id=context_id,
            status='success'
        )
    except Exception as e:
        print(f"查询处理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加文件路径常量
FEEDBACK_FILE = "d:\\mycode\\demo04\\feedback\\feedback_data.json"

# 确保反馈目录存在
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

@app.post("/execute_sql", dependencies=[Depends(verify_token)])  # 直接执行 SQL
async def execute_query(
    sql: str = Body(..., description="SQL语句")
):
    """直接执行SQL查询"""
    try:
        result = await query_model.execute_query(sql)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/execute_edited", dependencies=[Depends(verify_token)])  # 执行编辑后的 SQL
async def execute_edited_query(
    original_sql: str = Body(..., description="原始 SQL"),
    edited_sql: str = Body(..., description="编辑后的 SQL")
):
    """执行编辑后的 SQL 查询"""
    try:
        result = await query_model.execute_query(edited_sql)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/feedback", dependencies=[Depends(verify_token)])  # 反馈路由保持不变
async def feedback(request: Request):
    data = await request.json()
    query = data.get("query")
    sql = data.get("sql")
    rating = data.get("rating")
    
    feedback_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "sql": sql,
        "rating": rating
    }
    
    try:
        # 读取现有数据
        existing_data = []
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # 添加新数据
        existing_data.append(feedback_data)
        
        # 保存到文件
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        print(f"反馈已保存 - 查询: {query}, SQL: {sql}, 评分: {rating}")
        return {"status": "success"}
        
    except Exception as e:
        print(f"保存反馈失败: {str(e)}")
        return {"status": "error", "message": "保存反馈失败"}

# 添加角色权限管理相关路由
@app.get("/roles", dependencies=[Depends(verify_token)])
async def get_roles(db: Session = Depends(get_auth_db)):
    """获取所有角色列表"""
    try:
        roles = db.query(Role).all()
        return {"status": "success", "data": [{"id": role.id, "name": role.role_name, "description": role.description} for role in roles]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/roles/{role_id}", dependencies=[Depends(verify_token)])
async def get_role(role_id: int, db: Session = Depends(get_auth_db)):
    """获取指定角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"status": "success", "data": {"id": role.id, "name": role.role_name, "description": role.description}}

@app.post("/roles", dependencies=[Depends(verify_token)])
async def create_role(
    role_name: str = Body(...),
    description: str = Body(None),
    db: Session = Depends(get_auth_db)
):
    """创建新角色"""
    try:
        role = Role(role_name=role_name, description=description)
        db.add(role)
        db.commit()
        db.refresh(role)
        return {"status": "success", "data": {"id": role.id, "name": role.role_name}}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/roles/{role_id}", dependencies=[Depends(verify_token)])
async def update_role(
    role_id: int,
    role_name: str = Body(None),
    description: str = Body(None),
    db: Session = Depends(get_auth_db)
):
    """更新角色信息"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role_name:
        role.role_name = role_name
    if description:
        role.description = description
    
    try:
        db.commit()
        return {"status": "success", "data": {"id": role.id, "name": role.role_name}}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/roles/{role_id}", dependencies=[Depends(verify_token)])
async def delete_role(role_id: int, db: Session = Depends(get_auth_db)):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    try:
        db.delete(role)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 在角色管理路由后添加用户-角色分配相关接口
@app.get("/users/{user_id}/roles", dependencies=[Depends(verify_token)])
async def get_user_roles(user_id: int, db: Session = Depends(get_auth_db)):
    """获取用户的角色列表"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    roles = []
    for user_role in user_roles:
        role = db.query(Role).filter(Role.id == user_role.role_id).first()
        if role:
            roles.append({"id": role.id, "name": role.role_name})
    return {"status": "success", "data": roles}

@app.post("/users/{user_id}/roles", dependencies=[Depends(verify_token)])
async def assign_user_roles(
    user_id: int,
    role_ids: list[int] = Body(..., description="角色ID列表"),
    db: Session = Depends(get_auth_db)
):
    """为用户分配角色"""
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 删除用户现有的所有角色
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        
        # 分配新的角色
        for role_id in role_ids:
            # 检查角色是否存在
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail=f"角色ID {role_id} 不存在")
            
            user_role = UserRole(user_id=user_id, role_id=role_id)
            db.add(user_role)
        
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}/roles/{role_id}", dependencies=[Depends(verify_token)])
async def remove_user_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_auth_db)
):
    """移除用户的指定角色"""
    try:
        user_role = db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        
        if not user_role:
            raise HTTPException(status_code=404, detail="未找到指定的用户-角色关联")
        
        db.delete(user_role)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



# 添加用户管理相关接口
@app.get("/users", dependencies=[Depends(verify_token)])
async def get_users(db: Session = Depends(get_auth_db)):
    """获取所有用户列表"""
    try:
        users = db.query(User).all()
        return {
            "status": "success", 
            "data": [
                {
                    "id": user.id,
                    "username": user.username,
                    "created_at": user.created_at
                } for user in users
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", dependencies=[Depends(verify_token)])
async def get_user(user_id: int, db: Session = Depends(get_auth_db)):
    """获取指定用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "status": "success",
        "data": {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at
        }
    }

@app.post("/users", dependencies=[Depends(verify_token)])
async def create_user(
    username: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_auth_db)
):
    """创建新用户"""
    try:
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建新用户
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "status": "success",
            "data": {
                "id": user.id,
                "username": user.username
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}/password", dependencies=[Depends(verify_token)])
async def reset_password(
    user_id: int,
    password: str = Body(...),
    db: Session = Depends(get_auth_db)
):
    """重置用户密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        user.password = generate_password_hash(password)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}", dependencies=[Depends(verify_token)])
async def delete_user(user_id: int, db: Session = Depends(get_auth_db)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        db.delete(user)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 添加权限相关的 Schema
class PermissionCreate(BaseModel):
    db_name: str
    table_name: str
    field_list: List[str] = None
    where_clause: str = None


# 获取角色的所有权限
@app.get("/api/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_auth_db)
):
    """获取角色的所有权限"""
    permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    return {
        "status": "success",
        "data": [{
            "id": p.id,
            "db_name": p.db_name,
            "table_name": p.table_name,
            "field_list": p.field_list,
            "where_clause": p.where_clause
        } for p in permissions]
    }

# 获取用户的所有权限（通过用户的角色）
@app.get("/api/users/{user_id}/permissions", dependencies=[Depends(verify_token)])
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_auth_db)
):
    """获取用户的所有权限（通过用户的角色）"""
    # 获取用户的所有角色
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    
    # 获取这些角色的所有权限
    permissions = db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids)).all()
    
    return {
        "status": "success",
        "data": [{
            "id": p.id,
            "role_id": p.role_id,
            "db_name": p.db_name,
            "table_name": p.table_name,
            "field_list": p.field_list,
            "where_clause": p.where_clause
        } for p in permissions]
    }

# 删除指定的权限
@app.delete("/api/permissions/{permission_id}", dependencies=[Depends(verify_token)])
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_auth_db)
):
    """删除指定的权限"""
    try:
        permission = db.query(RolePermission).filter(RolePermission.id == permission_id).first()
        if not permission:
            raise HTTPException(status_code=404, detail="权限不存在")
        
        db.delete(permission)
        db.commit()
        return {"status": "success", "message": "权限删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 获取所有数据库列表
@app.get("/databases", dependencies=[Depends(verify_token)])
async def get_databases():
    """获取所有可用的数据库列表"""
    try:
        engine = create_engine('mysql://root:password@localhost/')
        inspector = inspect(engine)
        databases = inspector.get_schema_names()
        
        # 排除系统数据库
        user_databases = [db for db in databases if db not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
        
        return {
            "status": "success",
            "data": [{"name": db} for db in user_databases]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取指定数据库的所有表
@app.get("/databases/{db_name}/tables", dependencies=[Depends(verify_token)])
async def get_tables(db_name: str):
    """获取指定数据库中的所有表"""
    try:
        engine = create_engine(f'mysql://root:password@localhost/{db_name}')
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        return {
            "status": "success",
            "data": [{"name": table} for table in tables]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取指定表的所有字段
# 修复语法错误：删除重复的路由处理函数并修复 try-except 块
@app.get("/databases/{db_name}/tables/{table_name}/fields", dependencies=[Depends(verify_token)])
async def get_fields(db_name: str, table_name: str):
    """获取指定表的所有字段信息"""
    try:
        engine = create_engine(f'mysql+pymysql://root:sa123@localhost:3306/{db_name}')
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        
        # 获取字段注释
        from sqlalchemy.sql import text
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

# 添加数据库连接模型
class DatabaseConnection(BaseModel):
    host: str
    port: int = 3306
    username: str
    password: str
    database: str = None

@app.post("/database/test-connection")
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

@app.post("/databases")
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

@app.post("/databases/{db_name}/tables")
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
# 删除重复的 set_role_permissions 函数，只保留一个
# 修改角色权限相关的模型
class RolePermissionCreate(BaseModel):
    db_name: str
    table_name: str
    field_list: List[str]
    where_clause: str = None
    field_info: List[dict] = None  # 添加字段信息，包括注释

# 删除第 699 行和第 734 行附近的重复定义，只保留这一个
@app.post("/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
async def set_role_permissions(
    role_id: int,
    permissions: List[RolePermissionCreate],
    db: Session = Depends(get_auth_db)
):
    """设置角色权限，包括字段注释"""
    try:
        # 先删除原有权限
        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
        
        # 添加新权限
        for perm in permissions:
            # 打印接收到的数据，检查 field_info 是否存在
            print(f"接收到的权限数据: {perm}")
            print(f"字段信息: {perm.field_info}")
            
            new_perm = RolePermission(
                role_id=role_id,
                db_name=perm.db_name,
                table_name=perm.table_name,
                field_list=perm.field_list,
                where_clause=perm.where_clause,
                field_info=perm.field_info  # 保存字段完整信息
            )
            db.add(new_perm)
        
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        print(f"设置权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 修改获取角色权限的函数，返回字段信息
@app.get("/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
async def get_role_permissions(role_id: int, db: Session = Depends(get_auth_db)):
    """获取指定角色的权限配置"""
    try:
        permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
        return {
            "status": "success",
            "data": [{
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "field_list": perm.field_list,
                "where_clause": perm.where_clause,
                "field_info": perm.field_info  # 返回字段完整信息
            } for perm in permissions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 删除这里的重复定义
# @app.post("/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
# async def set_role_permissions(...)

# 添加数据库配置文件路径常量
DB_CONFIG_FILE = "config\\db_config.json"

# 确保配置目录存在
os.makedirs(os.path.dirname(DB_CONFIG_FILE), exist_ok=True)

# 添加数据库配置模型
class DatabaseConfig(BaseModel):
    host: str
    port: int = 3306
    username: str
    password: str

# 添加数据库配置相关的API接口
@app.get("/database/config")
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

@app.post("/database/config")
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
