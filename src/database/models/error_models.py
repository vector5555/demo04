from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any, Dict, List


class ErrorType(str, Enum):
    """错误类型枚举"""
    VALIDATION = "validation"  # 数据验证错误
    AUTHENTICATION = "authentication"  # 认证错误
    AUTHORIZATION = "authorization"  # 授权错误
    NOT_FOUND = "not_found"  # 资源不存在
    SQL = "sql"  # SQL错误
    DATABASE = "database"  # 数据库错误
    BUSINESS = "business"  # 业务逻辑错误
    SYSTEM = "system"  # 系统错误
    UNKNOWN = "unknown"  # 未知错误


class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    status: str = "error"
    error_type: ErrorType
    message: str
    detail: Optional[str] = None
    code: Optional[str] = None
    suggestion: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "error_type": "validation",
                "message": "数据验证失败",
                "detail": "用户名不能为空",
                "code": "INVALID_INPUT",
                "suggestion": "请提供有效的用户名",
                "fields": [
                    {"name": "username", "message": "用户名不能为空"}
                ]
            }
        }