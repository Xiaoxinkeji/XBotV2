import hashlib
import string
from random import choice
from typing import Union

import aiohttp
import qrcode
from loguru import logger

from .base import *
from .protect import protector
from ..errors import *


class LoginMixin(WechatAPIClientBase):
    # 模拟数据，用于Redis不可用情况
    mock_data = {
        "is_logged_in": False,
        "wxid": "",
        "nickname": "模拟账号",
        "login_time": 0,
        "device_type": "Simulated",
        "status": "无法连接到微信服务",
        "is_simulated": True
    }
    
    async def is_running(self) -> bool:
        """检查服务器是否运行中
        
        Returns:
            bool: 运行中返回True，否则返回False
        """
        try:
            # 尝试多个可能的端点
            endpoints = [
                "/IsRunning", 
                "/is_running", 
                "/ping", 
                "/health", 
                "/status"
            ]
            
            from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError, ServerTimeoutError
            
            for endpoint in endpoints:
                try:
                    timeout = aiohttp.ClientTimeout(total=2)  # 设置2秒超时
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        url = f"http://{self.ip}:{self.port}{endpoint}"
                        async with session.get(url) as response:
                            if response.status == 200:
                                return True
                except (ClientConnectorError, ClientResponseError, ServerTimeoutError) as e:
                    continue
                except Exception as e:
                    # 捕获其他异常但继续尝试下一个端点
                    continue
            
            # 如果所有端点都失败，尝试直接检查TCP连接
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.ip, self.port))
            sock.close()
            
            # 如果端口可连接但API未响应，可能是服务正在启动
            if result == 0:
                logger.info(f"端口 {self.port} 可以连接，但API服务未正确响应")
                return False
            
            return False
        except Exception as e:
            logger.error(f"检查服务状态时发生错误: {e}")
            return False

    async def get_login_status(self) -> dict:
        """
        获取当前微信登录状态
        
        Returns:
            dict: 登录状态信息，包含以下字段:
                is_logged_in (bool): 是否已登录
                wxid (str): 微信ID
                nickname (str): 昵称
                login_time (int): 登录时间戳
                device_type (str): 设备类型
        
        Raises:
            APIConnectionError: 连接API服务器失败
            APIResponseError: API返回错误
        """
        try:
            is_logged_in = bool(self.wxid)
            if is_logged_in:
                info = await self.get_cached_info()
                return {
                    "is_logged_in": is_logged_in,
                    "wxid": self.wxid,
                    "nickname": info.get("nickname", ""),
                    "login_time": info.get("login_time", 0),
                    "device_type": info.get("device_type", ""),
                }
            else:
                return {
                    "is_logged_in": False,
                    "wxid": "",
                    "nickname": "",
                    "login_time": 0,
                    "device_type": "",
                }
                
        except Exception as e:
            logger.error(f"获取登录状态失败: {str(e)}")
            # 返回错误状态，但不模拟数据
            return {
                "is_logged_in": False,
                "wxid": "",
                "nickname": "",
                "login_time": 0,
                "device_type": "",
                "error": str(e)
            }

    async def get_qr_code(self, device_name: str, device_id: str = "", proxy: Proxy = None, print_qr: bool = False) -> (
            str, str):
        """获取登录二维码
        
        Args:
            device_name (str): 设备名称
            device_id (str, optional): 设备ID. 默认为空字符串，会自动生成
            proxy (Proxy, optional): 代理设置. 默认为None
            print_qr (bool, optional): 是否在控制台打印二维码. 默认为False
            
        Returns:
            tuple[str, str]: (uuid, qr_url)二维码ID和二维码图片URL
            
        Raises:
            APIConnectionError: 连接API服务器失败
            APIResponseError: API返回错误
        """
        try:
            if not device_id:
                device_id = self.create_device_id()
                
            # 使用正确的URL构建方式
            url = f"http://{self.ip}:{self.port}/GetQRCode"
            
            # 准备请求参数
            json_param = {
                "DeviceName": device_name,
                "DeviceID": device_id
            }
            
            # 添加代理参数（如果提供）
            if proxy:
                json_param["ProxyInfo"] = {
                    "ProxyIp": f"{proxy.ip}:{proxy.port}",
                    "ProxyPassword": proxy.password,
                    "ProxyUser": proxy.username
                }
                    
            # 发送请求
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, json=json_param)
                json_resp = await response.json()
            
                if json_resp.get("Success"):
                    uuid = json_resp.get("uuid", "")
                    qrcode_url = json_resp.get("QR_url", "")
                    
                    if print_qr and qrcode_url:
                        self._print_qrcode(qrcode_url)
                    
                    return uuid, qrcode_url
                else:
                    logger.error(f"获取二维码失败: {json_resp.get('Message', '未知错误')}")
                    raise APIResponseError(f"获取二维码失败: {json_resp.get('Message', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取登录二维码时发生错误: {str(e)}")
            raise APIConnectionError(f"获取登录二维码失败: {str(e)}")
    
    def _print_qrcode(self, qrcode_url):
        """在控制台打印二维码"""
        try:
            import qrcode
            
            qr = qrcode.QRCode()
            qr.add_data(qrcode_url)
            qr.print_ascii(invert=True)
            logger.info(f"请使用微信扫描上方二维码登录\n二维码链接: {qrcode_url}")
        except ImportError:
            logger.warning("未安装qrcode库，无法在控制台打印二维码")
            logger.info(f"请使用微信扫描二维码登录: {qrcode_url}")
        except Exception as e:
            logger.error(f"打印二维码时发生错误: {str(e)}")
            logger.info(f"请使用微信扫描二维码登录: {qrcode_url}")

    async def check_login_uuid(self, uuid: str, device_id: str = "") -> tuple[bool, Union[dict, int]]:
        """检查登录的UUID状态。

        Args:
            uuid (str): 登录的UUID
            device_id (str, optional): 设备ID. Defaults to "".

        Returns:
            tuple[bool, Union[dict, int]]: 如果登录成功返回(True, 用户信息)，否则返回(False, 过期时间)

        Raises:
            根据error_handler处理错误
        """
        # 检查是否处于模拟模式
        if hasattr(self, 'minimal_mode') and self.minimal_mode:
            logger.info("模拟模式下不支持实际登录，返回虚拟等待状态")
            return False, 300  # 返回模拟的过期时间
            
        async with aiohttp.ClientSession() as session:
            json_param = {"Uuid": uuid}
            response = await session.post(f'http://{self.ip}:{self.port}/CheckUuid', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                if json_resp.get("Data").get("acctSectResp", ""):
                    self.wxid = json_resp.get("Data").get("acctSectResp").get("userName")
                    self.nickname = json_resp.get("Data").get("acctSectResp").get("nickName")
                    protector.update_login_status(device_id=device_id)
                    return True, json_resp.get("Data")
                else:
                    return False, json_resp.get("Data").get("expiredTime")
            else:
                self.error_handler(json_resp)

    async def log_out(self) -> bool:
        """
        登出微信
        
        Returns:
            bool: 是否成功登出
            
        Raises:
            APIConnectionError: 连接API服务器失败
            APIResponseError: API返回错误
        """
        if not self.wxid:
            logger.warning("用户尚未登录，无需登出")
            return True
            
        try:
            url = f"{self.api_url}/LogOut"
            result = await self._post_json(url)
            
            if result.get("Success"):
                # 无论API调用成功与否，都清除本地登录信息
                self.wxid = ""
                self.nickname = ""
                return True
            else:
                logger.error(f"API登出失败: {result.get('Message', '未知错误')}")
                # 即使API调用失败，也清除本地登录信息
                self.wxid = ""
                self.nickname = ""
                return False
                
        except Exception as e:
            logger.error(f"登出时发生错误: {str(e)}")
            # 即使发生错误，也清除本地登录信息
            self.wxid = ""
            self.nickname = ""
            return False

    async def awaken_login(self, wxid: str = "") -> str:
        """唤醒登录。

        Args:
            wxid (str, optional): 要唤醒的微信ID. Defaults to "".

        Returns:
            str: 返回新的登录UUID

        Raises:
            Exception: 如果未提供wxid且未登录
            LoginError: 如果无法获取UUID
            根据error_handler处理错误
        """
        if not wxid and not self.wxid:
            raise Exception("Please login using QRCode first")

        if not wxid and self.wxid:
            wxid = self.wxid

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/AwakenLogin', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success") and json_resp.get("Data").get("QrCodeResponse").get("Uuid"):
                return json_resp.get("Data").get("QrCodeResponse").get("Uuid")
            elif not json_resp.get("Data").get("QrCodeResponse").get("Uuid"):
                raise LoginError("Please login using QRCode first")
            else:
                self.error_handler(json_resp)

    async def get_cached_info(self, wxid: str = None) -> dict:
        """获取登录缓存信息。

        Args:
            wxid (str, optional): 要查询的微信ID. Defaults to None.

        Returns:
            dict: 返回缓存信息，如果未提供wxid且未登录返回空字典
        """
        if not wxid:
            wxid = self.wxid

        if not wxid:
            return {}

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/GetCachedInfo', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return json_resp.get("Data")
            else:
                return {}

    async def heartbeat(self) -> bool:
        """发送心跳包。

        Returns:
            bool: 成功返回True，否则返回False

        Raises:
            UserLoggedOut: 如果未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/Heartbeat', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return True
            else:
                self.error_handler(json_resp)

    async def start_auto_heartbeat(self) -> bool:
        """开始自动心跳。

        Returns:
            bool: 成功返回True，否则返回False

        Raises:
            UserLoggedOut: 如果未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/AutoHeartbeatStart', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return True
            else:
                self.error_handler(json_resp)

    async def stop_auto_heartbeat(self) -> bool:
        """停止自动心跳。

        Returns:
            bool: 成功返回True，否则返回False

        Raises:
            UserLoggedOut: 如果未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/AutoHeartbeatStop', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return True
            else:
                self.error_handler(json_resp)

    async def get_auto_heartbeat_status(self) -> bool:
        """获取自动心跳状态。

        Returns:
            bool: 如果正在运行返回True，否则返回False

        Raises:
            UserLoggedOut: 如果未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/AutoHeartbeatStatus', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return json_resp.get("Data").get("Running")
            else:
                return self.error_handler(json_resp)

    @staticmethod
    def create_device_name() -> str:
        """生成一个随机的设备名。

        Returns:
            str: 返回生成的设备名
        """
        first_names = [
            "Oliver", "Emma", "Liam", "Ava", "Noah", "Sophia", "Elijah", "Isabella",
            "James", "Mia", "William", "Amelia", "Benjamin", "Harper", "Lucas", "Evelyn",
            "Henry", "Abigail", "Alexander", "Ella", "Jackson", "Scarlett", "Sebastian",
            "Grace", "Aiden", "Chloe", "Matthew", "Zoey", "Samuel", "Lily", "David",
            "Aria", "Joseph", "Riley", "Carter", "Nora", "Owen", "Luna", "Daniel",
            "Sofia", "Gabriel", "Ellie", "Matthew", "Avery", "Isaac", "Mila", "Leo",
            "Julian", "Layla"
        ]

        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
            "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
            "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
            "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans"
        ]

        return choice(first_names) + " " + choice(last_names) + "'s Pad"

    @staticmethod
    def create_device_id(s: str = "") -> str:
        """生成设备ID。

        Args:
            s (str, optional): 用于生成ID的字符串. Defaults to "".

        Returns:
            str: 返回生成的设备ID
        """
        if s == "" or s == "string":
            s = ''.join(choice(string.ascii_letters) for _ in range(15))
        md5_hash = hashlib.md5(s.encode()).hexdigest()
        return "49" + md5_hash[2:]
