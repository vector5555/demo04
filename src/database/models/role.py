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

class RolePermission(AuthBase):
    __tablename__ = 'role_permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    db_name = Column(String(50), nullable=False)
    table_name = Column(String(50), nullable=False)
    field_list = Column(JSON)
    where_clause = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())