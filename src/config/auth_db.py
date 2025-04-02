from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 修改数据库连接信息，使用正确的用户名和密码
SQLALCHEMY_AUTH_DATABASE_URL = "mysql+pymysql://root:sa123@localhost/auth_db"

try:
    # 添加连接池配置和错误处理
    auth_engine = create_engine(
        SQLALCHEMY_AUTH_DATABASE_URL,
        pool_recycle=3600,  # 连接在池中保持时间
        pool_pre_ping=True,  # 在使用前测试连接
        pool_size=10,        # 连接池大小
        max_overflow=20      # 最大溢出连接数
    )
    logger.info("认证数据库引擎初始化成功")
except Exception as e:
    logger.error(f"认证数据库引擎初始化失败: {str(e)}")
    raise

AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)
AuthBase = declarative_base()

# 数据库依赖
def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()