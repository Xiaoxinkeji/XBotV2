FROM python:3.9

# 设置工作目录
WORKDIR /app

# 添加编译所需的依赖
RUN apt-get update && apt-get install -y gcc python3-dev

# 首先复制requirements.txt
COPY requirements.txt .

# 过滤掉问题依赖并安装其他依赖
RUN grep -v "xywechatpad-binary" requirements.txt > requirements_filtered.txt && \
    pip install --no-cache-dir -r requirements_filtered.txt

# 复制项目文件
COPY . .

# 尝试安装本地包(如果存在)
RUN if [ -d "xywechatpad-binary" ]; then \
      echo "从本地安装xywechatpad-binary" && \
      pip install -e xywechatpad-binary; \
    elif [ -d "wheels" ] && [ -f "$(find wheels -name 'xywechatpad-binary*.whl')" ]; then \
      echo "从wheel安装xywechatpad-binary" && \
      pip install $(find wheels -name 'xywechatpad-binary*.whl'); \
    else \
      echo "警告: xywechatpad-binary 包未找到，微信API功能将不可用"; \
    fi

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "web_ui.app:app", "--host", "0.0.0.0", "--port", "8000"]

