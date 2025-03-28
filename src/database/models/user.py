from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from ...config.auth_db import AuthBase

class User(AuthBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)