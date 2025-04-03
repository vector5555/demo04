from fastapi import Request, Depends
from typing import Optional

def get_current_user_id(request: Request) -> Optional[int]:
    """从当前请求的session中获取用户ID"""
    return request.session.get("user_id")

def get_user_roles(request: Request) -> list:
    """从当前请求的session中获取用户角色"""
    return request.session.get("roles", [])

def get_user_schemas(request: Request) -> dict:
    """从当前请求的session中获取用户schema信息"""
    return request.session.get("schemas", {})

def get_db_session(request: Request):
    """从当前请求的session中获取数据库会话"""
    return request.session.get("auth_db")