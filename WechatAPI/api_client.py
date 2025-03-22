"""
WechatAPI客户端主模块
"""

from loguru import logger
from .Client.base import WechatAPIClientBase
from .Client.login import LoginMixin
from .Client.message import MessageMixin
from .Client.user import UserMixin
from .Client.chatroom import ChatroomMixin
from .Client.friend import FriendMixin
from .Client.hongbao import HongBaoMixin
from .Client.protect import ProtectMixin
from .Client.tool import ToolMixin


class WechatAPIClient(WechatAPIClientBase, 
                    LoginMixin, 
                    MessageMixin, 
                    UserMixin, 
                    ChatroomMixin, 
                    FriendMixin, 
                    HongBaoMixin, 
                    ProtectMixin, 
                    ToolMixin):
    """
    微信API客户端
    整合所有功能模块
    """
    
    def __init__(self, host="127.0.0.1", port=9000):
        """
        初始化WechatAPI客户端
        
        Args:
            host (str): API服务器地址
            port (int): API服务器端口
        """
        super().__init__(host, port)
        logger.debug(f"初始化WechatAPI客户端 {host}:{port}") 