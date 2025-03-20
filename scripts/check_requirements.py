#!/usr/bin/env python3
"""
检查requirements.txt中的包版本兼容性
"""
import sys
import re
import subprocess
import json

def check_package_availability(package):
    """检查包的可用性"""
    try:
        # 使用pip index versions命令检查包的可用版本
        result = subprocess.run(
            ["pip", "index", "versions", package.split("~=")[0].split(">=")[0].split("==")[0].strip()],
            capture_output=True,
            text=True
        )
        
        # 如果成功获取版本信息
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    requirements_file = "requirements.txt"
    problem_packages = []
    
    print(f"检查 {requirements_file} 中的包兼容性...")
    
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith("#"):
                continue
                
            # 提取包名和版本
            package = line
            
            # 检查包的可用性
            available, message = check_package_availability(package)
            if not available:
                problem_packages.append((package, message))
            else:
                print(f"✅ {package} 可用")
    
    # 输出问题包
    if problem_packages:
        print("\n以下包可能存在问题:")
        for package, message in problem_packages:
            print(f"❌ {package}\n   错误: {message}")
        return 1
    
    print("\n✅ 所有包检查通过!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 