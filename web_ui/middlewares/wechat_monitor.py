"""
微信服务监控中间件
负责检测微信API服务状态并在需要时恢复服务
"""
import logging
import asyncio
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

class WechatMonitorMiddleware(BaseHTTPMiddleware):
    """
    微信服务监控中间件
    """
    def __init__(self, app, service_recovery_func=None, check_interval=300):
        """
        初始化中间件
        
        :param app: FastAPI应用实例
        :param service_recovery_func: 服务恢复函数，必须是一个异步函数
        :param check_interval: 检查间隔(秒)
        """
        super().__init__(app)
        self.service_recovery_func = service_recovery_func
        self.check_interval = check_interval
        self.last_check_time = 0
        self.is_recovering = False
        
        # 启动监控任务
        if self.service_recovery_func:
            asyncio.create_task(self._monitor_service())
        
    async def _monitor_service(self):
        """持续监控服务状态的后台任务"""
        while True:
            try:
                # 检查微信服务状态
                from web_ui.utils.wechat_utils import check_wechat_connection
                
                is_connected = await check_wechat_connection()
                
                if not is_connected and not self.is_recovering:
                    logger.warning("检测到微信服务未连接，尝试恢复...")
                    self.is_recovering = True
                    
                    # 调用恢复函数
                    recovery_result = await self.service_recovery_func()
                    
                    if recovery_result:
                        logger.info("微信服务恢复成功")
                    else:
                        logger.error("微信服务恢复失败")
                        
                    self.is_recovering = False
            except Exception as e:
                logger.error(f"监控微信服务时出错: {str(e)}")
                self.is_recovering = False
                
            # 间隔检查
            await asyncio.sleep(self.check_interval)
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并检查服务状态
        """
        # 检查是否需要恢复服务
        current_time = time.time()
        if (current_time - self.last_check_time > self.check_interval and 
            self.service_recovery_func and not self.is_recovering):
            
            self.last_check_time = current_time
            
            # 在单独的任务中检查，不阻塞请求
            asyncio.create_task(self._check_service())
        
        # 继续处理请求
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"处理请求时出错: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误"}
            )
    
    async def _check_service(self):
        """检查服务状态并在需要时恢复"""
        try:
            from web_ui.utils.wechat_utils import check_wechat_connection
            
            is_connected = await check_wechat_connection()
            
            if not is_connected and not self.is_recovering:
                logger.warning("检测到微信服务未连接，尝试恢复...")
                self.is_recovering = True
                
                # 调用恢复函数
                recovery_result = await self.service_recovery_func()
                
                if recovery_result:
                    logger.info("微信服务恢复成功")
                else:
                    logger.error("微信服务恢复失败")
                    
                self.is_recovering = False
        except Exception as e:
            logger.error(f"检查微信服务时出错: {str(e)}")
            self.is_recovering = False 