#!/usr/bin/env python3
"""
检查项目中的端口配置是否一致
"""
import sys
import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("check_port")

# 预期的端口配置
EXPECTED_PORT = "8080"

def check_file(file_path, patterns):
    """检查文件中的端口配置"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern, description in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match != EXPECTED_PORT:
                    issues.append(f"{description}: 发现端口 {match}, 预期为 {EXPECTED_PORT}")
    except Exception as e:
        logger.error(f"检查文件 {file_path} 时出错: {str(e)}")
    
    return issues

def main():
    """主函数"""
    # 要检查的文件类型
    file_patterns = [
        "*.py", "*.sh", "*.toml", "*.yml", "*.yaml", 
        "Dockerfile", "docker-compose*", "*.conf", "*.md", "*.txt"
    ]
    
    # 要匹配的模式
    content_patterns = [
        (r'port\s*=\s*["\'"]?(\d+)["\'"]?', "端口配置"),
        (r'PORT\s*=\s*["\'"]?(\d+)["\'"]?', "端口常量"),
        (r'--port[=\s]+(\d+)', "命令行参数"),
        (r':\s*(\d+)\s*["}]', "端口映射"),
        (r'EXPOSE\s+(\d+)', "Docker暴露端口"),
        (r'localhost:(\d+)', "localhost URL"),
        (r'127.0.0.1:(\d+)', "IP URL"),
    ]
    
    issues = []
    
    # 查找所有匹配的文件
    for pattern in file_patterns:
        for file_path in Path('.').glob(f"**/{pattern}"):
            # 排除某些目录
            if any(part.startswith('.') for part in file_path.parts) or 'venv' in file_path.parts:
                continue
                
            file_issues = check_file(file_path, content_patterns)
            if file_issues:
                for issue in file_issues:
                    logger.warning(f"{file_path}: {issue}")
                    issues.append((file_path, issue))
    
    if issues:
        logger.error(f"发现 {len(issues)} 个端口配置问题")
        return 1
    else:
        logger.info("未发现端口配置问题")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 