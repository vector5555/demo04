from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List

from ..config.auth_db import get_auth_db
from ..database.models.role import Role, RolePermission
from ..utils.auth import verify_token
from .models import RolePermissionCreate

router = APIRouter(tags=["角色管理"])

@router.get("/roles", dependencies=[Depends(verify_token)])
async def get_roles(db: Session = Depends(get_auth_db)):
    """获取所有角色列表"""
    try:
        roles = db.query(Role).all()
        return {"status": "success", "data": [{"id": role.id, "name": role.role_name, "description": role.description} for role in roles]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/roles/{role_id}", dependencies=[Depends(verify_token)])
async def get_role(role_id: int, db: Session = Depends(get_auth_db)):
    """获取指定角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"status": "success", "data": {"id": role.id, "name": role.role_name, "description": role.description}}

@router.post("/roles", dependencies=[Depends(verify_token)])
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

@router.put("/roles/{role_id}", dependencies=[Depends(verify_token)])
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

@router.delete("/roles/{role_id}", dependencies=[Depends(verify_token)])
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

@router.post("/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
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

@router.get("/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
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

@router.get("/api/roles/{role_id}/permissions", dependencies=[Depends(verify_token)])
async def get_role_permissions_api(
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

@router.delete("/api/permissions/{permission_id}", dependencies=[Depends(verify_token)])
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