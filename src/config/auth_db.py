from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 修改数据库连接信息，使用正确的用户名和密码
SQLALCHEMY_AUTH_DATABASE_URL = "mysql+pymysql://root:sa123@localhost/auth_db"

auth_engine = create_engine(SQLALCHEMY_AUTH_DATABASE_URL)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)
AuthBase = declarative_base()