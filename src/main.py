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
