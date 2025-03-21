"""
Web UI 依赖项
提供用于 FastAPI 路由依赖注入的功能
"""

import logging
from typing import Optional, Union, Dict, Any
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

# 日志配置
logger = logging.getLogger(__name__)

# 设置 OAuth2 处理器
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 用户模型
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False
    permissions: Optional[Dict[str, Any]] = {}

# JWT 配置
SECRET_KEY = "xybot_secret_key_change_in_production"  # 请在生产环境中更改
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 用于测试的测试用户
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "管理员",
        "email": "admin@example.com",
        "hashed_password": "password123",  # 生产环境应使用加密密码
        "disabled": False,
        "permissions": {"admin": True}
    }
}

def get_sessions():
    """获取会话管理器"""
    try:
        from web_ui.routers.auth import SESSIONS
        return SESSIONS
    except ImportError:
        logger.warning("无法导入会话管理器，使用空字典")
        return {}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    验证令牌并获取当前用户
    
    Args:
        token: JWT令牌
        
    Returns:
        User: 用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码 JWT 令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # 测试环境直接使用测试用户
    if username in fake_users_db:
        user_data = fake_users_db[username]
        return User(**user_data)
    
    # 生产环境应从数据库查询用户
    raise credentials_exception

async def get_optional_user(request: Request):
    """
    尝试获取当前用户，但不强制要求认证
    
    Args:
        request: 请求对象
        
    Returns:
        Optional[User]: 用户对象或None
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # 尝试从会话获取用户
            session_id = request.cookies.get("session_id")
            if session_id:
                sessions = get_sessions()
                user_data = sessions.get(session_id, {}).get("user")
                if user_data:
                    return User(**user_data)
            return None
            
        # 解析认证头
        token = auth_header.split()[1] if len(auth_header.split()) > 1 else None
        if not token:
            return None
            
        # 解码令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
            
        # 查找用户
        if username in fake_users_db:
            user_data = fake_users_db[username]
            return User(**user_data)
            
        return None
    except Exception as e:
        logger.warning(f"获取可选用户时出错: {str(e)}")
        return None

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    检查用户是否已激活
    
    Args:
        current_user: 当前已验证的用户
        
    Returns:
        User: 已激活的用户
        
    Raises:
        HTTPException: 用户被禁用时抛出异常
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    """
    检查用户是否有管理员权限
    
    Args:
        current_user: 当前已验证的用户
        
    Returns:
        User: 管理员用户
        
    Raises:
        HTTPException: 用户不是管理员时抛出异常
    """
    if not current_user.permissions.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user

# 会话管理
def get_user_from_session(session_id: Optional[str] = Cookie(None)):
    """
    从会话ID获取用户
    
    Args:
        session_id: 会话ID cookie
        
    Returns:
        Optional[User]: 用户对象或None
    """
    if not session_id:
        return None
        
    sessions = get_sessions()
    session_data = sessions.get(session_id)
    if not session_data:
        return None
        
    user_data = session_data.get("user")
    if not user_data:
        return None
        
    return User(**user_data) 