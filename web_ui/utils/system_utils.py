import logging

logger = logging.getLogger("web_ui.system")

# 尝试导入psutil，如果失败则使用模拟实现
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logger.warning("无法导入psutil，使用模拟实现。系统监控功能将受限。")
    HAS_PSUTIL = False
    
    # 创建模拟类
    class MockMemory:
        def __init__(self):
            self.total = 0
            self.available = 0
            self.percent = 0
            self.used = 0
            self.free = 0
    
    class MockDisk:
        def __init__(self):
            self.total = 0
            self.used = 0
            self.free = 0
            self.percent = 0
    
    class PsutilMock:
        @staticmethod
        def cpu_percent(*args, **kwargs):
            return 0.0
        
        @staticmethod
        def virtual_memory():
            return MockMemory()
        
        @staticmethod
        def disk_usage(path):
            return MockDisk()
        
        @staticmethod
        def getloadavg():
            return (0.0, 0.0, 0.0)
        
        @staticmethod
        def cpu_count():
            return 1
        
        @staticmethod
        def Process(pid):
            class MockProcess:
                @staticmethod
                def create_time():
                    import time
                    return time.time() - 3600  # 假设进程已运行1小时
            return MockProcess()
    
    # 替换psutil
    psutil = PsutilMock()

# 导出psutil，无论是真实的还是模拟的
__all__ = ['psutil', 'HAS_PSUTIL'] 