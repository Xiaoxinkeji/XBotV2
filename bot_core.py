import asyncio
import json
import os
import time
import tomllib
import traceback
from pathlib import Path

from loguru import logger

import WechatAPI
from database.XYBotDB import XYBotDB
from database.keyvalDB import KeyvalDB
from database.messsagDB import MessageDB
from utils.decorators import scheduler
from utils.plugin_manager import plugin_manager
from utils.xybot import XYBot
from utils.config_utils import load_toml_config


async def bot_core():
    # 设置工作目录
    script_dir = Path(__file__).resolve().parent

    # 读取主设置
    config_path = script_dir / "main_config.toml"
    main_config = load_toml_config(config_path)
    if not main_config:
        logger.error("读取主设置失败")
        return

    logger.success("读取主设置成功")

    # 启动WechatAPI服务
    server = WechatAPI.WechatAPIServer()
    api_config = main_config.get("WechatAPIServer", {})
    redis_host = api_config.get("redis-host", "127.0.0.1")
    redis_port = api_config.get("redis-port", 6379)
    logger.debug("Redis 主机地址: {}:{}", redis_host, redis_port)
    server.start(port=api_config.get("port", 9000),
                 mode=api_config.get("mode", "release"),
                 redis_host=redis_host,
                 redis_port=redis_port,
                 redis_password=api_config.get("redis-password", ""),
                 redis_db=api_config.get("redis-db", 0))

    # 实例化WechatAPI客户端
    bot = WechatAPI.WechatAPIClient("127.0.0.1", api_config.get("port", 9000))
    bot.ignore_protect = main_config.get("XYBot", {}).get("ignore-protection", False)

    # 等待WechatAPI服务启动
    time_out = 10
    while not await bot.is_running() and time_out > 0:
        logger.info("等待WechatAPI启动中")
        await asyncio.sleep(2)
        time_out -= 2

    if time_out <= 0:
        logger.error("WechatAPI服务启动超时")
        return

    # 检查Redis连接
    redis_status = await bot.check_database()
    if not redis_status:
        logger.error("Redis连接失败，请检查以下配置:")
        logger.error(f"  - Redis主机: {redis_host}")
        logger.error(f"  - Redis端口: {redis_port}")
        logger.error(f"  - Redis密码: {'已设置' if api_config.get('redis-password') else '未设置'}")
        logger.error(f"  - Redis数据库: {api_config.get('redis-db', 0)}")
        logger.error("请确保Redis服务已经启动并可以正常连接。")
        
        # 添加更详细的错误处理和恢复建议
        if redis_host == "127.0.0.1" or redis_host == "localhost":
            logger.error("本地Redis连接失败，请尝试以下操作:")
            logger.error("  1. 确认Redis服务是否已安装并运行")
            logger.error("  2. Windows下可在命令行执行: redis-server")
            logger.error("  3. Linux下可执行: sudo service redis-server start 或 sudo systemctl start redis")
        else:
            logger.error("远程Redis连接失败，请尝试以下操作:")
            logger.error("  1. 检查服务器防火墙是否允许 Redis 端口 (默认6379) 的连接")
            logger.error("  2. 确认Redis配置是否允许远程连接 (bind配置项)")
            logger.error("  3. 验证Redis密码是否正确")
        
        if os.path.exists("/etc/redis/redis.conf"):
            logger.error("检测到Redis配置文件，请确认绑定地址和密码设置是否正确")
        
        # Docker环境处理
        if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
            logger.error("在Docker环境中，请检查容器网络和Redis容器状态:")
            logger.error("  1. 执行 'docker ps' 查看Redis容器是否正常运行")
            logger.error("  2. 确认Docker网络配置允许容器间通信")
            logger.error("  3. 如果使用docker-compose，检查docker-compose.yml中的网络配置")
        
        return

    logger.success("WechatAPI服务已启动")

    # 检查并创建robot_stat.json文件
    robot_stat_path = script_dir / "resource" / "robot_stat.json"
    
    try:
        # ==========登陆==========
        if not os.path.exists(robot_stat_path):
            default_config = {
                "wxid": "",
                "device_name": "",
                "device_id": "",
                "online": False,
                "login_time": 0,
                "last_active": 0
            }
            os.makedirs(os.path.dirname(robot_stat_path), exist_ok=True)
            with open(robot_stat_path, "w") as f:
                json.dump(default_config, f)
            robot_stat = default_config
        else:
            with open(robot_stat_path, "r") as f:
                robot_stat = json.load(f)

        wxid = robot_stat.get("wxid", None)
        device_name = robot_stat.get("device_name", None)
        device_id = robot_stat.get("device_id", None)

        if not await bot.is_logged_in(wxid):
            while not await bot.is_logged_in(wxid):
                # 需要登录
                try:
                    if await bot.get_cached_info(wxid):
                        # 尝试唤醒登录
                        uuid = await bot.awaken_login(wxid)
                        logger.success("获取到登录uuid: {}", uuid)
                    else:
                        # 二维码登录
                        if not device_name:
                            device_name = bot.create_device_name()
                        if not device_id:
                            device_id = bot.create_device_id()
                        uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                        logger.success("获取到登录uuid: {}", uuid)
                        logger.success("获取到登录二维码: {}", url)

                        # 添加登录变量
                        max_retries = 3  # 最大连续失败重试次数
                        retry_count = 0
                        login_timeout = 300  # 总登录超时时间（秒）
                        start_time = time.time()

                        while True:
                            try:
                                # 检查UUID是否需要重新获取
                                if retry_count >= max_retries or time.time() - start_time > login_timeout:
                                    logger.warning("登录重试次数过多或超时，重新获取二维码")
                                    uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                                    logger.success("获取到新的登录uuid: {}", uuid)
                                    logger.success("获取到新的登录二维码: {}", url)
                                    retry_count = 0
                                    start_time = time.time()
                                
                                # 检查登录状态
                                stat, data = await bot.check_login_uuid(uuid, device_id=device_id)
                                
                                if stat:  # 登录成功
                                    logger.success("登录成功！")
                                    break
                                elif isinstance(data, int) and data <= 30:
                                    # UUID无效或即将过期，需要重新获取
                                    logger.warning("UUID无效或即将过期，重新获取二维码")
                                    uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                                    logger.success("获取到新的登录uuid: {}", uuid)
                                    logger.success("获取到新的登录二维码: {}", url)
                                    retry_count = 0
                                    start_time = time.time()
                                else:
                                    # 正常等待扫码
                                    logger.info("等待登录中，过期倒计时：{}", data)
                                    
                                # 等待一段时间再检查
                                await asyncio.sleep(5)
                                
                            except Exception as e:
                                logger.error("登录过程发生错误: {}", str(e))
                                retry_count += 1
                                
                                if "UUid not found" in str(e) or "UUID not found" in str(e):
                                    logger.warning("UUID不存在，需要重新获取")
                                    uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                                    logger.success("获取到新的登录uuid: {}", uuid)
                                    logger.success("获取到新的登录二维码: {}", url)
                                    retry_count = 0
                                
                                # 避免频繁重试导致API请求过多
                                await asyncio.sleep(3)
                except:
                    # 二维码登录
                    if not device_name:
                        device_name = bot.create_device_name()
                    if not device_id:
                        device_id = bot.create_device_id()
                    uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                    logger.success("获取到登录uuid: {}", uuid)
                    logger.success("获取到登录二维码: {}", url)

                while True:
                    stat, data = await bot.check_login_uuid(uuid, device_id=device_id)
                    if stat:
                        break
                    logger.info("等待登录中，过期倒计时：{}", data)
                    await asyncio.sleep(5)
                    
                    # 检查UUID是否过期或无效
                    if isinstance(data, int) and data <= 30:
                        logger.warning("UUID即将过期或无效，重新获取二维码")
                        try:
                            uuid, url = await bot.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
                            logger.success("获取到新的登录uuid: {}", uuid)
                            logger.success("获取到新的登录二维码: {}", url)
                        except Exception as e:
                            logger.error("重新获取二维码失败: {}", e)
                            await asyncio.sleep(3)

            # 保存登录信息
            robot_stat["wxid"] = bot.wxid
            robot_stat["device_name"] = device_name
            robot_stat["device_id"] = device_id
            robot_stat["online"] = True
            robot_stat["login_time"] = int(time.time())
            robot_stat["last_active"] = int(time.time())
            with open(robot_stat_path, "w", encoding="utf-8") as f:
                json.dump(robot_stat, f, ensure_ascii=False)

            # 获取登录账号信息
            bot.wxid = data.get("acctSectResp").get("userName")
            bot.nickname = data.get("acctSectResp").get("nickName")
            bot.alias = data.get("acctSectResp").get("alias")
            bot.phone = data.get("acctSectResp").get("bindMobile")

            logger.info("登录账号信息: wxid: {}  昵称: {}  微信号: {}  手机号: {}", bot.wxid, bot.nickname, bot.alias,
                        bot.phone)
            
            # 获取头像URL
            try:
                # 获取个人二维码，它包含头像URL
                qrcode_data = await bot.get_my_qrcode()
                avatar_url = qrcode_data.get("headImgUrl", "")
                logger.info("获取到用户头像URL: {}", avatar_url)
            except Exception as e:
                logger.warning("获取头像URL失败: {}", e)
                avatar_url = ""
            
            # 保存用户信息到profile.json，供Web界面读取
            profile_data = {
                "wxid": bot.wxid,
                "nickname": bot.nickname,
                "alias": bot.alias,
                "phone": bot.phone,
                "login_time": int(time.time()),
                "avatar_url": avatar_url  # 添加头像URL
            }
            profile_path = script_dir / "resource" / "profile.json"
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False)
            logger.success("用户信息已保存到profile.json")

        else:  # 已登录
            bot.wxid = wxid
            profile = await bot.get_profile()

            bot.nickname = profile.get("NickName").get("string")
            
            # 获取更多个人信息
            try:
                bot.alias = profile.get("Alias") or ""
                
                # 获取头像URL
                try:
                    # 获取个人二维码，它包含头像URL
                    qrcode_data = await bot.get_my_qrcode()
                    avatar_url = qrcode_data.get("headImgUrl", "")
                    logger.info("获取到用户头像URL: {}", avatar_url)
                except Exception as e:
                    logger.warning("获取头像URL失败: {}", e)
                    avatar_url = ""
                
                # 保存或更新用户信息到profile.json，供Web界面读取
                profile_data = {
                    "wxid": bot.wxid,
                    "nickname": bot.nickname,
                    "alias": bot.alias,
                    "login_time": int(time.time()),
                    "avatar_url": avatar_url  # 添加头像URL
                }
                profile_path = script_dir / "resource" / "profile.json"
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(profile_data, f, ensure_ascii=False)
                logger.success("用户信息已保存到profile.json")
            except Exception as e:
                logger.warning("获取更多个人信息失败: {}", e)

        logger.info("登录设备信息: device_name: {}  device_id: {}", device_name, device_id)

        logger.success("登录成功")

        # ========== 登录完毕 开始初始化 ========== #

        # 开启自动心跳
        try:
            success = await bot.start_auto_heartbeat()
            if success:
                logger.success("已开启自动心跳")
            else:
                logger.warning("开启自动心跳失败")
        except ValueError:
            logger.warning("自动心跳已在运行")
        except Exception as e:
            if "在运行" not in e:
                logger.warning("自动心跳已在运行")

        # 初始化机器人
        xybot = XYBot(bot)
        xybot.update_profile(bot.wxid, bot.nickname, bot.alias, bot.phone)

        # 初始化数据库
        XYBotDB()

        message_db = MessageDB()
        await message_db.initialize()

        keyval_db = KeyvalDB()
        await keyval_db.initialize()

        # 启动调度器
        scheduler.start()
        logger.success("定时任务已启动")

        # 加载插件目录下的所有插件
        loaded_plugins = await plugin_manager.load_plugins_from_directory(bot, load_disabled_plugin=False)
        logger.success(f"已加载插件: {loaded_plugins}")

        # 更新机器人状态文件，添加online标记
        try:
            # 读取当前状态
            with open(robot_stat_path, "r", encoding="utf-8") as f:
                current_stat = json.load(f)
            
            # 更新在线状态
            current_stat["online"] = True
            current_stat["login_time"] = int(time.time())
            current_stat["wxid"] = bot.wxid
            current_stat["nickname"] = bot.nickname
            current_stat["alias"] = bot.alias
            current_stat["last_active"] = int(time.time())
            
            # 保存更新后的状态
            with open(robot_stat_path, "w", encoding="utf-8") as f:
                json.dump(current_stat, f, ensure_ascii=False)
            
            logger.success("机器人状态已更新：在线")
        except Exception as e:
            logger.error(f"更新机器人状态文件失败: {e}")

        # ========== 开始接受消息 ========== #

        # 先接受堆积消息
        logger.info("处理堆积消息中")
        count = 0
        while True:
            data = await bot.sync_message()
            data = data.get("AddMsgs")
            if not data:
                if count > 2:
                    break
                else:
                    count += 1
                    continue

            logger.debug("接受到 {} 条消息", len(data))
            await asyncio.sleep(1)
        logger.success("处理堆积消息完毕")

        logger.success("开始处理消息")
        
        try:
            while True:
                now = time.time()

                try:
                    data = await bot.sync_message()
                except Exception as e:
                    logger.warning("获取新消息失败 {}", e)
                    await asyncio.sleep(5)
                    continue
                    
                # 更新最后活动时间
                try:
                    with open(robot_stat_path, "r", encoding="utf-8") as f:
                        current_stat = json.load(f)
                    current_stat["last_active"] = int(time.time())
                    with open(robot_stat_path, "w", encoding="utf-8") as f:
                        json.dump(current_stat, f, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"更新活动时间失败: {e}")

                data = data.get("AddMsgs")
                if not data:
                    await asyncio.sleep(1)
                    continue

                logger.debug("接收到 {} 条消息", len(data))

                for msg in data:
                    # 使用原来的消息处理方式，创建异步任务处理消息
                    asyncio.create_task(xybot.process_message(msg))

                await asyncio.sleep(0.5)
        finally:
            # 无论如何都会执行的代码，确保机器人状态更新为离线
            logger.info("机器人即将退出，更新状态为离线")
            try:
                # 停止自动心跳
                try:
                    await bot.stop_auto_heartbeat()
                    logger.info("已停止自动心跳")
                except Exception as e:
                    logger.warning(f"停止自动心跳失败: {e}")
                
                # 更新机器人状态为离线
                if os.path.exists(robot_stat_path):
                    with open(robot_stat_path, "r", encoding="utf-8") as f:
                        current_stat = json.load(f)
                    
                    current_stat["online"] = False
                    current_stat["last_active"] = int(time.time())
                    
                    with open(robot_stat_path, "w", encoding="utf-8") as f:
                        json.dump(current_stat, f, ensure_ascii=False)
                    
                    logger.success("机器人状态已更新：离线")
            except Exception as e:
                logger.error(f"更新机器人离线状态失败: {e}")
    except KeyboardInterrupt:
        logger.info("接收到键盘中断，正在退出...")
    except Exception as e:
        logger.error(f"机器人运行时发生异常: {e}")
        logger.error(traceback.format_exc())
    finally:
        # 再次确保机器人状态更新为离线
        logger.info("确保机器人状态更新为离线")
        try:
            # 更新机器人状态为离线
            if os.path.exists(robot_stat_path):
                with open(robot_stat_path, "r", encoding="utf-8") as f:
                    current_stat = json.load(f)
                
                current_stat["online"] = False
                current_stat["last_active"] = int(time.time())
                
                with open(robot_stat_path, "w", encoding="utf-8") as f:
                    json.dump(current_stat, f, ensure_ascii=False)
                
                logger.success("机器人状态已更新：离线")
        except Exception as e:
            logger.error(f"最终更新机器人离线状态失败: {e}")
