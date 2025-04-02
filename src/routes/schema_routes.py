from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config.auth_db import get_auth_db
from ..database.models.role import RolePermission, UserRole
from ..utils.auth import verify_token
from ..schema.schema_builder import SchemaBuilder

router = APIRouter(tags=["Schema管理"])

# 依赖项：获取Schema构建器
def get_schema_builder():
    from ..main import schema_builder
    return schema_builder

@router.post("/schema/build/{role_id}", dependencies=[Depends(verify_token)])
async def build_schema_for_role(
    role_id: int, 
    db: Session = Depends(get_auth_db),
    schema_builder: SchemaBuilder = Depends(get_schema_builder)
):
    """为指定角色构建schema"""
    try:
        # 获取角色权限
        permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
        
        if not permissions:
            return {"status": "error", "message": f"角色 {role_id} 没有配置权限"}
        
        # 转换权限格式
        perm_list = [{
            "id": perm.id,
            "db_name": perm.db_name,
            "table_name": perm.table_name,
            "field_list": perm.field_list,
            "where_clause": perm.where_clause,
            "field_info": perm.field_info
        } for perm in permissions]
        
        # 构建schema
        schema = schema_builder.build_schema_for_role(perm_list)
        
        if schema:
            return {"status": "success", "data": schema, "message": f"角色 {role_id} 的schema构建成功"}
        else:
            return {"status": "error", "message": f"角色 {role_id} 的schema构建失败"}
    except Exception as e:
        print(f"构建schema失败: {str(e)}")
        return {"status": "error", "message": f"构建schema失败: {str(e)}"}

@router.get("/schema/{role_id}", dependencies=[Depends(verify_token)])
async def get_schema_for_role(
    role_id: int, 
    db: Session = Depends(get_auth_db),
    schema_builder: SchemaBuilder = Depends(get_schema_builder)
):
    """获取指定角色的schema"""
    try:
        # 获取角色权限
        permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
        
        if not permissions:
            return {"status": "error", "message": f"角色 {role_id} 没有配置权限"}
        
        # 转换权限格式
        perm_list = [{
            "id": perm.id,
            "db_name": perm.db_name,
            "table_name": perm.table_name,
            "field_list": perm.field_list,
            "where_clause": perm.where_clause,
            "field_info": perm.field_info
        } for perm in permissions]
        
        # 构建schema
        schema = schema_builder.build_schema_for_role(perm_list)
        
        if schema:
            return {"status": "success", "data": schema}
        else:
            return {"status": "error", "message": f"角色 {role_id} 的schema构建失败"}
    except Exception as e:
        return {"status": "error", "message": f"获取schema失败: {str(e)}"}

@router.get("/schema/user/{user_id}", dependencies=[Depends(verify_token)])
async def get_user_schemas(
    user_id: int, 
    db: Session = Depends(get_auth_db),
    schema_builder: SchemaBuilder = Depends(get_schema_builder)
):
    """获取用户的所有角色schema"""
    try:
        # 获取用户的所有角色
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            return {"status": "error", "message": f"用户 {user_id} 没有分配角色"}
        
        # 获取所有角色的权限
        schemas = {}
        for role_id in role_ids:
            permissions = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
            
            if permissions:
                perm_list = [{
                    "id": perm.id,
                    "db_name": perm.db_name,
                    "table_name": perm.table_name,
                    "field_list": perm.field_list,
                    "where_clause": perm.where_clause,
                    "field_info": perm.field_info
                } for perm in permissions]
                
                schema = schema_builder.build_schema_for_role(perm_list)
                if schema:
                    schemas[role_id] = schema
        
        if schemas:
            return {
                "status": "success", 
                "data": schemas,
                "message": f"成功获取用户 {user_id} 的 {len(schemas)} 个角色schema"
            }
        else:
            return {"status": "error", "message": f"用户 {user_id} 的角色没有配置权限"}
    except Exception as e:
        return {"status": "error", "message": f"获取用户schema失败: {str(e)}"}