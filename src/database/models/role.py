from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ...config.auth_db import AuthBase

class Role(AuthBase):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserRole(AuthBase):
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

# 检查 RolePermission 模型是否包含 field_info 字段
class RolePermission(AuthBase):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    db_name = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    field_list = Column(JSON, nullable=True)
    where_clause = Column(Text, nullable=True)
    # 如果没有这个字段，需要添加
    field_info = Column(JSON, nullable=True)  # 存储字段的完整信息，包括注释
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())