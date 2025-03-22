import hashlib
import string
from random import choice
from typing import Union

import aiohttp
import qrcode

from .base import *
from .protect import protector
from ..errors import *


class LoginMixin(WechatAPIClientBase):
    async def is_running(self) -> bool:
        """检查服务是否正在运行

        Returns:
            bool: 如果服务正在运行，则为True
        """
        try:
            # 尝试多个可能的端点
            endpoints = ["", "/is_running", "/IsRunning", "/health", "/ping", "/status"]
            timeout = aiohttp.ClientTimeout(total=2)  # 设置2秒超时
            
            for endpoint in endpoints:
                try:
                    url = f"http://{self.ip}:{self.port}{endpoint}"
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url) as response:
                            if response.status < 500:  # 任何非服务器错误都表示服务器在运行
                                return True
                except Exception as e:
                    # 如果一个端点失败，尝试下一个
                    continue
                    
            # 如果所有端点都失败，尝试一种替代方法
            try:
                # 测试TCP连接
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.ip, self.port))
                sock.close()
                return result == 0  # 如果端口开放，则认为服务在运行
            except Exception:
                pass
                
            return False
        except Exception:
            return False

    async def get_login_status(self) -> dict:
        """获取当前微信登录状态
        
        Returns:
            dict: 包含登录状态信息的字典，如下所示：
                {
                    "is_logged_in": bool,  # 是否已登录
                    "wxid": str,           # 微信ID (如已登录)
                    "nickname": str,       # 微信昵称 (如已登录)
                    "login_time": int,     # 登录时间戳 (如已登录)
                    "device_type": str     # 设备类型 (如已登录)
                }
        """
        # 获取基本登录信息
        logged_in = bool(self.wxid)
        
        result = {
            "is_logged_in": logged_in,
            "wxid": self.wxid,
            "nickname": self.nickname,
            "login_time": 0,  # 默认值
            "device_type": "Unknown"  # 默认值
        }
        
        # 如果已登录，尝试获取更多详细信息
        if logged_in:
            try:
                # 尝试获取更多详细信息
                cached_info = await self.get_cached_info(self.wxid)
                if cached_info:
                    result["nickname"] = cached_info.get("nickname", self.nickname)
                    # 添加其他可能有用的信息
            except Exception:
                # 如果获取额外信息失败，使用已有的基本信息
                pass
        
        return result

    async def get_qr_code(self, device_name: str, device_id: str = "", proxy: Proxy = None, print_qr: bool = False) -> (
            str, str):
        """获取登录二维码。

        Args:
            device_name (str): 设备名称
            device_id (str, optional): 设备ID. Defaults to "".
            proxy (Proxy, optional): 代理信息. Defaults to None.
            print_qr (bool, optional): 是否在控制台打印二维码. Defaults to False.

        Returns:
            tuple[str, str]: 返回登录二维码的UUID和URL

        Raises:
            根据error_handler处理错误
        """
        async with aiohttp.ClientSession() as session:
            json_param = {'DeviceName': device_name, 'DeviceID': device_id}
            if proxy:
                json_param['ProxyInfo'] = {'ProxyIp': f'{proxy.ip}:{proxy.port}',
                                           'ProxyPassword': proxy.password,
                                           'ProxyUser': proxy.username}

            response = await session.post(f'http://{self.ip}:{self.port}/GetQRCode', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):

                if print_qr:
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(f'http://weixin.qq.com/x/{json_resp.get("Data").get("Uuid")}')
                    qr.make(fit=True)
                    qr.print_ascii()

                return json_resp.get("Data").get("Uuid"), json_resp.get("Data").get("QRCodeURL")
            else:
                self.error_handler(json_resp)

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
        """登出当前账号。

        Returns:
            bool: 登出成功返回True，否则返回False

        Raises:
            UserLoggedOut: 如果未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid}
            response = await session.post(f'http://{self.ip}:{self.port}/Logout', json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return True
            elif json_resp.get("Success"):
                return False
            else:
                self.error_handler(json_resp)

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
