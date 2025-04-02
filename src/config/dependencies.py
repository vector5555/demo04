from sqlalchemy.orm import Session
from ..config.auth_db import AuthSessionLocal
from ..schema.schema_builder import SchemaBuilder
from ..model.query_model import QueryModel

# 数据库依赖
def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schema构建器依赖
def get_schema_builder():
    from ..main import schema_builder
    return schema_builder

# 查询模型依赖
def get_query_model():
    from ..main import query_model
    return query_model