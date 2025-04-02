from typing import List, Dict, Optional
from pydantic import BaseModel

# 权限相关的模型
class PermissionCreate(BaseModel):
    db_name: str
    table_name: str
    field_list: List[str] = None
    where_clause: str = None

# 角色权限相关的模型
class RolePermissionCreate(BaseModel):
    db_name: str
    table_name: str
    field_list: List[str]
    where_clause: str = None
    field_info: List[dict] = None  # 添加字段信息，包括注释

# 数据库连接模型
class DatabaseConnection(BaseModel):
    host: str
    port: int = 3306
    username: str
    password: str
    database: str = None

# 数据库配置模型
class DatabaseConfig(BaseModel):
    host: str
    port: int = 3306
    username: str
    password: str

# LLM API配置模型
class LLMConfig(BaseModel):
    api_url: str
    api_key: str
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.95
    timeout: int = 60