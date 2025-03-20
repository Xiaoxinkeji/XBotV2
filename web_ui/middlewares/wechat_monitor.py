import asyncio
import logging
import time
from typing import Dict, Any, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.wechat_utils import check_wechat_connection, ping_wechat_api
from ..utils.service_recovery import restart_wechat_service

logger = logging.getLogger(__name__)

class WechatMonitorMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        check_interval: int = 300,  # 5分钟检查一次
    ):
        super().__init__(app)
        self.check_interval = check_interval
        self.last_check = 0
        self.wechat_status = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # 启动后台监控任务
        self.start_monitor_task()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并监控微信API状态"""
        # 对于API状态请求，尝试更新微信状态
        if request.url.path == "/api/status" or request.url.path == "/api/wechat/status":
            current_time = time.time()
            if current_time - self.last_check > 60:  # 至少间隔1分钟做一次检查
                asyncio.create_task(self.check_and_update_status())
        
        # 继续处理请求
        response = await call_next(request)
        return response
    
    def start_monitor_task(self):
        """启动后台监控任务"""
        asyncio.create_task(self.monitor_wechat_status())
    
    async def monitor_wechat_status(self):
        """定期监控微信API状态的后台任务"""
        while True:
            await self.check_and_update_status()
            await asyncio.sleep(self.check_interval)
    
    async def check_and_update_status(self):
        """检查并更新微信API状态"""
        self.last_check = time.time()
        
        try:
            # 先尝试主要检查方法
            self.wechat_status = await check_wechat_connection()
            
            # 如果主方法失败，尝试ping
            if not self.wechat_status:
                self.wechat_status = await ping_wechat_api()
            
            # 成功连接，重置重连计数
            if self.wechat_status:
                if self.reconnect_attempts > 0:
                    logger.info(f"微信API已恢复连接，之前尝试次数: {self.reconnect_attempts}")
                self.reconnect_attempts = 0
            else:
                # 连接失败，增加重连计数
                self.reconnect_attempts += 1
                logger.warning(f"微信API连接失败，当前尝试次数: {self.reconnect_attempts}")
                
                # 如果连续失败且达到一定次数，尝试恢复服务
                if self.reconnect_attempts >= 3:
                    logger.warning("微信API连续失败，尝试恢复服务...")
                    recovery_result = await restart_wechat_service()
                    if recovery_result:
                        logger.info("微信服务恢复操作成功执行")
                    else:
                        logger.error("微信服务恢复操作失败")
                
                # 如果尝试次数过多，减少检查频率
                if self.reconnect_attempts > self.max_reconnect_attempts:
                    logger.error("微信API重连尝试达到上限，减少检查频率")
                
        except Exception as e:
            logger.error(f"检查微信状态时出错: {str(e)}")
            self.wechat_status = False 