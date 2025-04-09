from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, ProgrammingError
# 修改导入路径，从database.models导入而不是models
from ..database.models.error_models import ErrorResponse, ErrorType


class AppError(Exception):
    """应用程序自定义错误"""
    def __init__(
        self, 
        message: str, 
        error_type: ErrorType = ErrorType.BUSINESS,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = None,
        code: str = None,
        suggestion: str = None,
        fields: list = None
    ):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.detail = detail
        self.code = code
        self.suggestion = suggestion
        self.fields = fields
        super().__init__(self.message)


def handle_sql_error(error: SQLAlchemyError) -> AppError:
    """处理SQL错误并提供友好的错误信息"""
    error_msg = str(error)
    
    # 处理不同类型的SQL错误
    if isinstance(error, ProgrammingError):
        if "syntax error" in error_msg.lower():
            return AppError(
                message="SQL语法错误",
                error_type=ErrorType.SQL,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
                code="SQL_SYNTAX_ERROR",
                suggestion="请检查SQL语法，特别是关键字、括号和引号的使用"
            )
        elif "permission denied" in error_msg.lower():
            return AppError(
                message="SQL权限错误",
                error_type=ErrorType.SQL,
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
                code="SQL_PERMISSION_DENIED",
                suggestion="您没有执行此操作的权限，请联系管理员申请相应权限"
            )
        elif "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            return AppError(
                message="表不存在",
                error_type=ErrorType.SQL,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
                code="TABLE_NOT_FOUND",
                suggestion="请检查表名是否正确，或者您可能没有访问该表的权限"
            )
        elif "column" in error_msg.lower() and "does not exist" in error_msg.lower():
            return AppError(
                message="字段不存在",
                error_type=ErrorType.SQL,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
                code="COLUMN_NOT_FOUND",
                suggestion="请检查字段名是否正确，或者您可能没有访问该字段的权限"
            )
    
    # 处理完整性约束错误
    if isinstance(error, IntegrityError):
        if "unique constraint" in error_msg.lower():
            return AppError(
                message="数据已存在",
                error_type=ErrorType.DATABASE,
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
                code="UNIQUE_CONSTRAINT_VIOLATION",
                suggestion="请提供唯一的数据值"
            )
        elif "foreign key constraint" in error_msg.lower():
            return AppError(
                message="外键约束错误",
                error_type=ErrorType.DATABASE,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
                code="FOREIGN_KEY_VIOLATION",
                suggestion="请确保引用的数据存在"
            )
    
    # 默认SQL错误处理
    return AppError(
        message="数据库操作失败",
        error_type=ErrorType.DATABASE,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_msg,
        code="DATABASE_ERROR",
        suggestion="请联系管理员或稍后重试"
    )


def create_error_response(error: AppError) -> ErrorResponse:
    """创建统一的错误响应"""
    return ErrorResponse(
        status="error",
        error_type=error.error_type,
        message=error.message,
        detail=error.detail,
        code=error.code,
        suggestion=error.suggestion,
        fields=error.fields
    )