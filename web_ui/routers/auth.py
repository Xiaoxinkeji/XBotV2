from fastapi import APIRouter, HTTPException, Depends, Cookie, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import os
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from web_ui.utils import api_response, error_response

router = APIRouter()

# 简单的会话存储
# 生产环境中应该使用Redis或数据库
SESSIONS = {}

class LoginForm(BaseModel):
    username: str
    password: str
    remember_me: bool = False

def get_admin_credentials():
    """获取管理员凭据"""
    admin_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "admin.json")
    if not os.path.exists(admin_file):
        # 如果文件不存在，创建默认管理员账户
        default_admin = {
            "username": "admin",
            # 默认密码: admin123
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        }
        os.makedirs(os.path.dirname(admin_file), exist_ok=True)
        with open(admin_file, "w") as f:
            json.dump(default_admin, f)
        return default_admin
    
    with open(admin_file, "r") as f:
        return json.load(f)

def verify_session(session_id: Optional[str] = Cookie(None)):
    """验证会话是否有效"""
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(
            status_code=401,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查会话是否过期
    session = SESSIONS[session_id]
    if datetime.now() > session["expires"]:
        SESSIONS.pop(session_id, None)
        raise HTTPException(
            status_code=401,
            detail="会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新会话过期时间
    if session["remember_me"]:
        session["expires"] = datetime.now() + timedelta(days=7)
    else:
        session["expires"] = datetime.now() + timedelta(hours=2)
    
    return session["username"]

@router.post("/login")
async def login(form_data: LoginForm, response: Response):
    """用户登录"""
    admin = get_admin_credentials()
    
    # 验证用户名和密码
    password_hash = hashlib.sha256(form_data.password.encode()).hexdigest()
    if form_data.username != admin["username"] or password_hash != admin["password_hash"]:
        return error_response("用户名或密码错误", status_code=401)
    
    # 创建会话
    session_id = secrets.token_urlsafe(32)
    expires = datetime.now()
    
    if form_data.remember_me:
        expires += timedelta(days=7)
    else:
        expires += timedelta(hours=2)
    
    SESSIONS[session_id] = {
        "username": form_data.username,
        "expires": expires,
        "remember_me": form_data.remember_me
    }
    
    # 设置Cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=7 * 24 * 3600 if form_data.remember_me else 2 * 3600,
        samesite="lax",
        secure=False  # 生产环境中应设为True
    )
    
    return api_response(
        message="登录成功",
        data={"username": form_data.username}
    )

@router.post("/logout")
async def logout(response: Response, username: str = Depends(verify_session)):
    """用户登出"""
    # 清除会话
    for sid, session in list(SESSIONS.items()):
        if session["username"] == username:
            SESSIONS.pop(sid, None)
    
    # 清除Cookie
    response.delete_cookie(key="session_id")
    
    return api_response(message="登出成功")

@router.get("/check")
async def check_auth(username: str = Depends(verify_session)):
    """检查用户是否已登录"""
    return api_response(
        data={"logged_in": True, "username": username},
        message="已登录"
    )

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    username: str = Depends(verify_session)
):
    """修改密码"""
    admin = get_admin_credentials()
    
    # 验证旧密码
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    if old_hash != admin["password_hash"]:
        return error_response("原密码错误", status_code=400)
    
    # 更新密码
    admin["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
    
    # 保存更新
    admin_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "admin.json")
    with open(admin_file, "w") as f:
        json.dump(admin, f)
    
    # 使所有会话失效（强制重新登录）
    for sid in list(SESSIONS.keys()):
        SESSIONS.pop(sid, None)
    
    return api_response(message="密码修改成功，请重新登录") 