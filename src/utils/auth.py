import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Request  # 添加Request导入
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import PyJWTError  # 修改为PyJWTError

SECRET_KEY = "your-secret-key"  # 实际应用中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 添加获取当前用户ID的函数
async def get_current_user_id(request: Request):
    """
    从请求中获取当前用户ID或用户名
    """
    token = request.cookies.get("token") or request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 获取用户标识符
        user_id = payload.get("user_id")
        if user_id is None:
            user_id = payload.get("sub")
            
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
            
        # 尝试将用户ID转换为整数，如果失败则返回原始值
        try:
            return int(user_id)
        except (ValueError, TypeError):
            # 如果是用户名等非数字值，直接返回
            return user_id
    except PyJWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")