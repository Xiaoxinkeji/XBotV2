from fastapi import APIRouter, HTTPException, BackgroundTasks
from WechatAPI import WechatAPIClient
import base64
from io import BytesIO
import time
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger("web_ui.wechat")

# 存储登录状态的全局变量
login_status = {
    "status": "idle",  # idle, waiting, success, failed
    "message": "",
    "qrcode": None,
    "user_info": None,
    "last_update": 0
}

# 任务状态
bg_task_running = False

async def check_login_status():
    """后台任务：检查登录状态"""
    global bg_task_running, login_status
    
    try:
        client = WechatAPIClient()
        bg_task_running = True
        logger.info("开始监控微信登录状态")
        
        retry_count = 0
        max_retries = 30  # 最多尝试30次，约5分钟
        
        while login_status["status"] == "waiting" and retry_count < max_retries:
            try:
                # 获取登录状态
                result = client.get_login_info()
                
                if result.get("success"):
                    if result.get("is_logged_in"):
                        # 已登录
                        login_status["status"] = "success"
                        login_status["message"] = "登录成功"
                        
                        # 获取更详细的用户信息
                        phone_number = result.get("phone", "")
                        # 处理手机号显示
                        if phone_number and len(phone_number) >= 11:
                            # 确保格式化为标准手机号显示
                            formatted_phone = phone_number
                        else:
                            formatted_phone = result.get("wxid", "")
                        
                        login_status["user_info"] = {
                            "nickname": result.get("nickname", "未知"),
                            "avatar": result.get("avatar", ""),
                            "wxid": result.get("wxid", ""),
                            "phone": formatted_phone
                        }
                        logger.info(f"微信登录成功: {result.get('nickname')}")
                        break
                    else:
                        # 等待扫码
                        logger.debug("等待扫码...")
                else:
                    # API返回错误
                    logger.warning(f"获取登录状态失败: {result.get('message')}")
            
            except Exception as e:
                logger.error(f"检查登录状态时出错: {str(e)}")
            
            # 等待10秒后再次检查
            retry_count += 1
            login_status["last_update"] = time.time()
            await asyncio.sleep(10)
        
        if retry_count >= max_retries and login_status["status"] == "waiting":
            login_status["status"] = "failed"
            login_status["message"] = "登录超时，请重新获取二维码"
            logger.warning("登录超时")
    
    except Exception as e:
        logger.error(f"登录监控任务异常: {str(e)}")
        login_status["status"] = "failed"
        login_status["message"] = f"发生错误: {str(e)}"
    
    finally:
        bg_task_running = False
        logger.info("微信登录监控任务结束")


@router.get("/login/qrcode")
async def get_login_qrcode(background_tasks: BackgroundTasks):
    """获取登录二维码"""
    global login_status, bg_task_running
    
    try:
        client = WechatAPIClient()
        result = client.generate_login_qrcode()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "获取二维码失败"))
        
        # 获取二维码图片
        qrcode_data = result.get("qrcode")
        if not qrcode_data:
            raise HTTPException(status_code=500, detail="二维码数据为空")
        
        # 将二维码转为Base64
        if isinstance(qrcode_data, bytes):
            qrcode_base64 = base64.b64encode(qrcode_data).decode('utf-8')
        else:
            # 如果API返回的是图片URL，直接使用
            qrcode_base64 = qrcode_data
        
        # 更新状态
        login_status["status"] = "waiting"
        login_status["message"] = "请使用微信扫描二维码登录"
        login_status["qrcode"] = qrcode_base64
        login_status["last_update"] = time.time()
        
        # 启动后台任务监控登录状态
        if not bg_task_running:
            background_tasks.add_task(check_login_status)
        
        return {
            "success": True,
            "qrcode": qrcode_base64,
            "message": "请使用微信扫描二维码登录"
        }
    
    except Exception as e:
        logger.error(f"获取登录二维码失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login/status")
async def get_login_status():
    """获取当前登录状态"""
    global login_status
    
    # 添加时间戳方便前端判断是否有更新
    response = {
        "success": True,
        "status": login_status["status"],
        "message": login_status["message"],
        "timestamp": login_status["last_update"]
    }
    
    # 成功登录时返回用户信息
    if login_status["status"] == "success" and login_status["user_info"]:
        response["user_info"] = login_status["user_info"]
    
    return response


@router.post("/logout")
async def logout_wechat():
    """退出微信登录"""
    global login_status
    
    try:
        client = WechatAPIClient()
        result = client.logout()
        
        if result.get("success"):
            # 重置登录状态
            login_status = {
                "status": "idle",
                "message": "已退出登录",
                "qrcode": None,
                "user_info": None,
                "last_update": time.time()
            }
            
            return {"success": True, "message": "成功退出微信登录"}
        else:
            return {"success": False, "message": result.get("message", "退出失败")}
    
    except Exception as e:
        logger.error(f"退出微信登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 