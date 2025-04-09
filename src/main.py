from fastapi import FastAPI, Request, status, Depends
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
import os
import json
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import secrets
from sqlalchemy.exc import SQLAlchemyError
from .utils.error_handler import AppError, handle_sql_error, create_error_response
from .database.models.error_models import ErrorType

# 创建FastAPI应用
app = FastAPI(title="自然语言数据库查询API")
security = HTTPBearer()

# 内部导入
from .config.auth_db import AuthBase, auth_engine
from .schema.schema_builder import SchemaBuilder
from .model.query_model import QueryModel
from .utils.auth import verify_token
from .routes import auth_routes, query_routes, role_routes, user_routes, database_routes, schema_routes, llm_routes

# 添加Session中间件
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),  # 生成随机密钥
    max_age=3600,  # session有效期，单位秒
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化认证数据库
AuthBase.metadata.create_all(bind=auth_engine)

# 配置信息
DB_URL = "mysql+pymysql://root:sa123@localhost:3306/air"  # 目标查询数据库

# 添加数据库配置文件路径常量
DB_CONFIG_FILE = "config\\db_config.json"
# 添加LLM API配置文件路径常量
LLM_CONFIG_FILE = "config\\llm_config.json"
# 添加反馈文件路径常量
FEEDBACK_FILE = "feedback\\feedback_data.json"

# 确保配置目录存在
os.makedirs(os.path.dirname(DB_CONFIG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(LLM_CONFIG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

# 默认LLM配置
default_llm_config = {
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "api_key": "",  # 移除硬编码的API密钥
    "model_name": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.95,
    "timeout": 60
}

# 加载LLM配置
llm_config = default_llm_config.copy()
try:
    if os.path.exists(LLM_CONFIG_FILE):
        with open(LLM_CONFIG_FILE, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
            llm_config.update(saved_config)
            print(f"已从 {LLM_CONFIG_FILE} 加载LLM配置")
    else:
        print(f"LLM配置文件不存在，使用默认配置")
except Exception as e:
    print(f"加载LLM配置失败: {str(e)}")

# 初始化Schema管理器
try:
    print("正在初始化Schema管理器...")
    schema_builder = SchemaBuilder(DB_URL)
    print("Schema管理器初始化成功")
except Exception as e:
    print(f"Schema管理器初始化失败: {str(e)}")
    raise

# 初始化查询模型
try:
    print("正在初始化查询模型...")
    query_model = QueryModel(
        db_url=DB_URL,
        api_key=llm_config["api_key"],
        api_url=llm_config["api_url"],
        model_name=llm_config["model_name"],
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"],
        top_p=llm_config["top_p"]
    )
    print("查询模型初始化成功")
except Exception as e:
    print(f"查询模型初始化失败: {str(e)}")
    raise

# 全局异常处理器
@app.exception_handler(AppError)
async def app_error_handler(request: Request, error: AppError):
    """处理应用程序自定义错误"""
    return JSONResponse(
        status_code=error.status_code,
        content=create_error_response(error).dict()
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, error: SQLAlchemyError):
    """处理SQLAlchemy错误"""
    app_error = handle_sql_error(error)
    return JSONResponse(
        status_code=app_error.status_code,
        content=create_error_response(app_error).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, error: Exception):
    """处理所有未捕获的异常"""
    app_error = AppError(
        message="服务器内部错误",
        error_type=ErrorType.SYSTEM,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(error),
        code="INTERNAL_SERVER_ERROR",
        suggestion="请联系管理员或稍后重试"
    )
    return JSONResponse(
        status_code=app_error.status_code,
        content=create_error_response(app_error).dict()
    )

# 注册路由
app.include_router(auth_routes.router)
app.include_router(query_routes.router)
app.include_router(role_routes.router)
app.include_router(user_routes.router)
app.include_router(database_routes.router)
app.include_router(schema_routes.router)
app.include_router(llm_routes.router)

# 根路由
@app.get("/", dependencies=[Depends(verify_token)])
async def root():
    return {"message": "自然语言查询API服务已启动"}

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "服务运行正常"}

# 启动事件
@app.on_event("startup")
async def startup():
    # 启动时的初始化代码
    pass

# 关闭事件
@app.on_event("shutdown")
async def shutdown():
    # 关闭时的清理代码
    pass