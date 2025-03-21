import os
import pathlib
import subprocess
import threading

import xywechatpad_binary
from loguru import logger


class WechatAPIServer:
    def __init__(self):
        self.executable_path = xywechatpad_binary.copy_binary(pathlib.Path(__file__).parent.parent / "core")
        self.executable_path = self.executable_path.absolute()

        self.log_process = None
        self.process = None
        self.server_process = None

        self.arguments = ["--port", "9000", "--mode", "release", "--redis-host", "127.0.0.1", "--redis-port", "6379",
                          "--redis-password", "", "--redis-db", "0"]

    def __del__(self):
        self.stop()

    def start(self, port: int = 9000, mode: str = "release", redis_host: str = "127.0.0.1", redis_port: int = 6379,
              redis_password: str = "", redis_db: int = 0):
        """
        Start WechatAPI server
        :param port:
        :param mode:
        :param redis_host:
        :param redis_port:
        :param redis_password:
        :param redis_db:
        :return:
        """

        arguments = ["-p", str(port), "-m", mode, "-rh", redis_host, "-rp", str(redis_port), "-rpwd", redis_password,
                     "-rdb", str(redis_db)]

        command = [self.executable_path] + arguments

        self.process = subprocess.Popen(command, cwd=os.path.dirname(os.path.abspath(__file__)), stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.log_process = threading.Thread(target=self.process_stdout_to_log, daemon=True)
        self.error_log_process = threading.Thread(target=self.process_stderr_to_log, daemon=True)
        self.log_process.start()
        self.error_log_process.start()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.log_process.join()
            self.error_log_process.join()

    def process_stdout_to_log(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            # logger.log("API", line.decode("utf-8").strip())

        # 检查进程是否异常退出
        return_code = self.process.poll()
        if return_code is not None and return_code != 0:
            logger.error("WechatAPI服务器异常退出，退出码: {}", return_code)

    def process_stderr_to_log(self):
        while True:
            line = self.process.stderr.readline()
            if not line:
                break
            logger.info(line.decode("utf-8").strip())