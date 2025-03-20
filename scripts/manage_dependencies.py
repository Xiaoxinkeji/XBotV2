#!/usr/bin/env python3
"""
全面的依赖管理工具
"""
import sys
import os
import re
import subprocess
import json
import argparse
from typing import List, Dict, Tuple, Any

# 已知的有问题依赖及其替代方案
PROBLEMATIC_DEPS = {
    r"matplotlib~=3\.10\.0": "matplotlib~=3.9.0",
    r"pysilk>=0\.5": "pysilk-mod>=1.6.4",
    r"xywechatpad-binary==1\.1\.0": None  # None表示没有替代方案，需要特殊处理
}

def check_package_availability(package: str) -> Tuple[bool, str]:
    """检查包的可用性"""
    try:
        package_name = package.split("~=")[0].split(">=")[0].split("==")[0].strip()
        result = subprocess.run(
            ["pip", "index", "versions", package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)

def fix_requirements(input_file: str, output_file: str) -> List[str]:
    """修复requirements.txt文件中的问题依赖"""
    problems = []
    fixed_lines = []
    
    with open(input_file, "r") as f:
        for line in f:
            original_line = line.strip()
            
            # 跳过空行和注释
            if not original_line or original_line.startswith("#"):
                fixed_lines.append(original_line)
                continue
            
            # 检查是否是已知的问题依赖
            is_problematic = False
            for pattern, replacement in PROBLEMATIC_DEPS.items():
                if re.search(pattern, original_line):
                    is_problematic = True
                    problems.append(f"检测到问题依赖: {original_line}")
                    
                    if replacement:
                        fixed_lines.append(replacement)
                        problems.append(f"已替换为: {replacement}")
                    else:
                        problems.append(f"将跳过: {original_line}")
                    break
            
            if not is_problematic:
                fixed_lines.append(original_line)
    
    # 写入修复后的文件
    with open(output_file, "w") as f:
        for line in fixed_lines:
            f.write(f"{line}\n")
    
    return problems

def check_all_dependencies(requirements_file: str) -> List[str]:
    """检查所有依赖的可用性"""
    issues = []
    
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith("#"):
                continue
                
            # 检查包的可用性
            available, message = check_package_availability(line)
            if not available:
                issues.append(f"包 {line} 可能存在问题: {message}")
    
    return issues

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="依赖管理工具")
    parser.add_argument("--check", action="store_true", help="检查依赖")
    parser.add_argument("--fix", action="store_true", help="修复依赖")
    parser.add_argument("--input", default="requirements.txt", help="输入文件")
    parser.add_argument("--output", default="requirements_fixed.txt", help="输出文件")
    
    args = parser.parse_args()
    
    # 默认行为：如果没有指定操作，则检查和修复
    if not (args.check or args.fix):
        args.check = True
        args.fix = True
    
    # 检查依赖
    if args.check:
        print(f"检查依赖问题({args.input})...")
        issues = check_all_dependencies(args.input)
        
        if issues:
            print("\n发现以下依赖问题:")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("未发现依赖问题!")
    
    # 修复依赖
    if args.fix:
        print(f"修复依赖问题({args.input} -> {args.output})...")
        problems = fix_requirements(args.input, args.output)
        
        if problems:
            print("\n已修复以下问题:")
            for problem in problems:
                print(f"- {problem}")
            print(f"\n修复后的依赖已写入: {args.output}")
        else:
            print("未发现需要修复的问题!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 