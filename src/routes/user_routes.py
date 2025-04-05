from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from typing import List  # 添加这一行导入List类型

from ..config.auth_db import get_auth_db
from ..database.models.user import User
from ..database.models.role import UserRole, RolePermission, Role  # 添加Role导入
from ..utils.auth import verify_token

router = APIRouter(tags=["用户管理"])

@router.get("/users", dependencies=[Depends(verify_token)])
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

@router.get("/users/{user_id}", dependencies=[Depends(verify_token)])
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

@router.post("/users", dependencies=[Depends(verify_token)])
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
        
        # 创建新用户，使用与验证一致的密码加密方法
        from ..utils.auth import get_password_hash  # 导入与验证一致的加密方法
        hashed_password = get_password_hash(password)  # 使用一致的加密方法
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

@router.put("/users/{user_id}/password", dependencies=[Depends(verify_token)])
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

@router.delete("/users/{user_id}", dependencies=[Depends(verify_token)])
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

@router.get("/api/users/{user_id}/permissions", dependencies=[Depends(verify_token)])
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

# 需要添加获取用户角色的接口
@router.get("/users/{user_id}/roles", dependencies=[Depends(verify_token)])
async def get_user_roles(user_id: int, db: Session = Depends(get_auth_db)):
    """获取用户的角色列表"""
    try:
        # 查询用户角色关系
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        
        if not user_roles:
            return []
        
        # 获取角色详情
        role_ids = [ur.role_id for ur in user_roles]
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
        
        # 转换为JSON格式
        result = [{"id": role.id, "name": role.role_name, "description": role.description} 
                 for role in roles]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户角色失败: {str(e)}")

# 需要添加设置用户角色的接口
@router.post("/users/{user_id}/roles", dependencies=[Depends(verify_token)])
async def set_user_roles(user_id: int, role_ids: List[int], db: Session = Depends(get_auth_db)):
    """设置用户的角色"""
    try:
        # 先删除用户现有的所有角色
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        
        # 添加新的角色关系
        for role_id in role_ids:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            db.add(user_role)
        
        db.commit()
        return {"status": "success", "message": "用户角色设置成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"设置用户角色失败: {str(e)}")