import os
import logging
import asyncio
import subprocess
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

# 微信服务恢复配置
WECHAT_API_HOST = os.getenv("WECHAT_API_HOST", "localhost")
WECHAT_API_PORT = int(os.getenv("WECHAT_API_PORT", "5000"))
WECHAT_SERVICE_NAME = os.getenv("WECHAT_SERVICE_NAME", "wechat-service")
MAX_RECOVERY_ATTEMPTS = 3
RECOVERY_ATTEMPT_INTERVAL = 60  # 秒

# 恢复状态跟踪
recovery_status = {
    "last_attempt": 0,
    "attempts": 0,
    "last_success": 0
}

async def start_wechat_service() -> bool:
    """
    尝试启动微信API服务
    """
    try:
        from WechatAPI import WechatAPIServer
        
        logger.info("正在启动微信API服务...")
        # 创建服务器实例
        server = WechatAPIServer()
        
        # 检查服务器是否可用(依赖是否已安装)
        if not getattr(server, 'available', False):
            logger.error("无法启动微信API服务: xywechatpad-binary 依赖缺失")
            return False
            
        # 启动服务
        result = server.start(port=WECHAT_API_PORT)
        
        # 等待服务器启动
        for _ in range(5):  # 最多等待5秒
            await asyncio.sleep(1)
            
            # 检查服务是否启动
            try:
                from WechatAPI import WechatAPIClient
                client = WechatAPIClient(WECHAT_API_HOST, WECHAT_API_PORT)
                if await client.is_running():
                    logger.info("微信API服务已成功启动")
                    return True
            except Exception:
                pass
        
        logger.warning("微信API服务启动超时")
        return False
    except Exception as e:
        logger.error(f"启动微信API服务时出错: {str(e)}")
        return False

async def restart_wechat_service() -> bool:
    """
    尝试重启微信服务
    """
    current_time = time.time()
    
    # 检查是否可以尝试恢复
    if (recovery_status["attempts"] >= MAX_RECOVERY_ATTEMPTS and 
        current_time - recovery_status["last_attempt"] < 3600):  # 1小时内尝试过多次
        logger.warning(f"微信服务自动恢复已达到最大尝试次数: {MAX_RECOVERY_ATTEMPTS}")
        return False
    
    # 更新恢复状态
    recovery_status["attempts"] += 1
    recovery_status["last_attempt"] = current_time
    
    try:
        logger.info(f"尝试重启微信服务...")
        
        # 在Docker环境中
        if os.path.exists("/.dockerenv"):
            # 判断是否存在docker命令
            docker_exists = await check_command_exists("docker")
            
            if docker_exists:
                # 使用Docker命令重启服务
                proc = await asyncio.create_subprocess_exec(
                    'docker', 'restart', WECHAT_SERVICE_NAME,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    logger.info(f"微信服务 {WECHAT_SERVICE_NAME} 重启成功")
                    recovery_status["last_success"] = current_time
                    return True
                else:
                    error_msg = stderr.decode('utf-8') if stderr else "未知错误"
                    logger.error(f"重启微信服务失败: {error_msg}")
            else:
                logger.warning("Docker环境中找不到docker命令，尝试其他方法")
        
        # 尝试直接启动服务
        result = await start_wechat_service()
        if result:
            recovery_status["last_success"] = current_time
            return True
            
        # 尝试使用systemd重启服务
        systemctl_exists = await check_command_exists("systemctl")
        if systemctl_exists:
            proc = await asyncio.create_subprocess_exec(
                'systemctl', 'restart', WECHAT_SERVICE_NAME,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.info(f"微信服务 {WECHAT_SERVICE_NAME} 通过systemd重启成功")
                recovery_status["last_success"] = current_time
                return True
            else:
                error_msg = stderr.decode('utf-8') if stderr else "未知错误"
                logger.error(f"通过systemd重启微信服务失败: {error_msg}")
        
        return False
    
    except Exception as e:
        logger.error(f"尝试恢复微信服务时出错: {str(e)}")
        return False

async def check_command_exists(cmd: str) -> bool:
    """检查命令是否存在"""
    try:
        proc = await asyncio.create_subprocess_exec(
            'which', cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode == 0
    except Exception:
        return False

# 添加到恢复函数到微信监控中间件中
# 在WechatMonitorMiddleware类的check_and_update_status方法中添加:
'''
# 如果连续失败且达到一定次数，尝试恢复服务
if not self.wechat_status and self.reconnect_attempts >= 3:
    logger.warning("微信API连续失败，尝试恢复服务...")
    from ..utils.service_recovery import restart_wechat_service
    recovery_result = await restart_wechat_service()
    if recovery_result:
        logger.info("微信服务恢复操作成功执行")
''' 