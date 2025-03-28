from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.models.user import User 
from ..utils.auth import create_access_token, verify_password
from ..config.auth_db import AuthSessionLocal

router = APIRouter()

def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_auth_db)):
    #print("收到登录请求")
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):  # 直接验证原始密码
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"token": token}