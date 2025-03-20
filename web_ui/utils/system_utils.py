import logging
import psutil

logger = logging.getLogger("web_ui.system")

# 不再需要模拟实现，直接使用真实psutil
HAS_PSUTIL = True

# 导出psutil，供其他模块使用
__all__ = ['psutil', 'HAS_PSUTIL'] 