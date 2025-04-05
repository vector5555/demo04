from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
import logging

from ..config.auth_db import get_auth_db
from ..database.models.user import User
from ..database.models.role import Role, UserRole, RolePermission
from ..utils.auth import verify_token, create_access_token, verify_password
from ..schema.schema_builder import SchemaBuilder
from starlette.middleware.sessions import SessionMiddleware

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["认证"])

# 登录接口
@router.post("/login")
async def login(request: Request, db: Session = Depends(get_auth_db)):
    """用户登录"""
    try:
        print("用户登录开始")
        print(f"请求scope: {request.scope}")
        print(f"session是否在scope中: {'session' in request.scope}")
        
        # 打印请求信息，帮助调试
        body = await request.json()
        logger.info(f"收到登录请求: {body}")
        
        # 检查请求体中是否包含必要的字段
        if 'username' not in body or 'password' not in body:
            logger.error("请求缺少必要的字段: username 或 password")
            raise HTTPException(status_code=422, detail="请求缺少必要的字段: username 或 password")
        
        username = body['username']
        password = body['password']
        
        logger.info(f"尝试验证用户: {username}")
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"用户不存在: {username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not verify_password(password, user.password):
            logger.warning(f"密码验证失败: {username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 获取用户角色
        user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        roles = []
        role_ids = []
        
        for user_role in user_roles:
            role = db.query(Role).filter(Role.id == user_role.role_id).first()
            if role:
                roles.append(role.role_name)
                role_ids.append(role.id)
        
        # 生成访问令牌
        token = create_access_token({
            "sub": user.username,
            "roles": roles,
            "user_id": user.id
        })
        
        # 获取用户的schema信息
        schemas = {}
        schema_builder = SchemaBuilder(db_url="mysql+pymysql://root:sa123@localhost:3306/air")
        
        # 收集所有权限信息
        all_permissions = []
        
        for role_id in role_ids:
            permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
            
            if permissions:
                # 将SQLAlchemy对象转换为字典
                perm_list = [{
                    "id": perm.id,
                    "db_name": perm.db_name,
                    "table_name": perm.table_name,
                    "field_list": perm.field_list,
                    "where_clause": perm.where_clause,
                    "field_info": perm.field_info
                } for perm in permissions]
                
                # 添加到所有权限列表
                all_permissions.extend(perm_list)
                
                schema = schema_builder.build_schema_for_role(perm_list)
                if schema:
                    schemas[role_id] = schema
        
        # 将用户ID和权限信息存储到session中
        try:
            if 'session' in request.scope:
                request.session["user_id"] = user.id
                request.session["username"] = user.username
                request.session["roles"] = roles
                request.session["role_ids"] = role_ids
                # 添加权限信息到session
                request.session["permissions"] = all_permissions
                logger.info(f"用户 {username} 登录成功，信息和权限已写入session")
            else:
                logger.warning("Session中间件未正确安装，无法访问session")
        except Exception as session_error:
            logger.error(f"写入session失败: {str(session_error)}")
        
        return {
            "status": "success",
            "data": {
                "token": token,
                "user_id": user.id,
                "username": user.username,
                "roles": [{"id": role_id, "name": role_name} for role_id, role_name in zip(role_ids, roles)],
                "schemas": schemas,
                # 在响应中也返回权限信息
                "permissions": all_permissions
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录处理出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))