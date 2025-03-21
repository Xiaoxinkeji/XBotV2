import os
import sys
import json
import zipfile
import shutil
import tempfile
import importlib
import importlib.util
from pathlib import Path
from loguru import logger
import re
import asyncio
import aiohttp
import time

class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir="plugins"):
        """
        初始化插件管理器
        
        Args:
            plugins_dir: 插件目录
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.installed_plugins = {}
        self.plugin_instances = {}
        self.scan_plugins()
    
    def scan_plugins(self):
        """扫描已安装的插件"""
        self.installed_plugins = {}
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            info_file = plugin_dir / "info.json"
            if not info_file.exists():
                continue
            
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                plugin_id = info.get("id")
                if not plugin_id:
                    continue
                
                self.installed_plugins[plugin_id] = {
                    "id": plugin_id,
                    "name": info.get("name", plugin_id),
                    "description": info.get("description", ""),
                    "version": info.get("version", "0.0.1"),
                    "author": info.get("author", ""),
                    "requirements": info.get("requirements", []),
                    "path": str(plugin_dir),
                    "info": info
                }
            except Exception as e:
                logger.error(f"扫描插件 {plugin_dir} 出错: {e}")
        
        return self.installed_plugins
    
    async def install_plugin(self, plugin_file, update=False):
        """
        安装或更新插件
        
        Args:
            plugin_file: 插件文件路径（zip）
            update: 是否为更新模式
            
        Returns:
            安装结果
        """
        if not os.path.exists(plugin_file):
            return {"success": False, "message": f"插件文件不存在: {plugin_file}"}
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        plugin_id = None
        plugin_info = None
        
        try:
            # 解压插件文件
            with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找插件信息文件
            info_files = list(Path(temp_dir).glob("**/info.json"))
            if not info_files:
                return {"success": False, "message": "插件包中没有找到 info.json 文件"}
            
            # 读取插件信息
            with open(info_files[0], "r", encoding="utf-8") as f:
                plugin_info = json.load(f)
            
            plugin_id = plugin_info.get("id")
            if not plugin_id:
                return {"success": False, "message": "插件信息中缺少 ID"}
            
            plugin_name = plugin_info.get("name", plugin_id)
            plugin_version = plugin_info.get("version", "0.0.1")
            
            # 检查插件是否已安装
            is_installed = plugin_id in self.installed_plugins
            
            # 如果已安装且不是更新模式，则返回错误
            if is_installed and not update:
                installed_version = self.installed_plugins[plugin_id].get("version", "0.0.1")
                return {
                    "success": False, 
                    "message": f"插件 {plugin_name} (ID: {plugin_id}) 已安装 (版本: {installed_version})。"
                           f"如需更新，请使用更新功能。"
                }
            
            # 如果是更新模式但插件未安装，则返回错误
            if not is_installed and update:
                return {
                    "success": False, 
                    "message": f"插件 {plugin_name} (ID: {plugin_id}) 未安装，无法更新。"
                }
            
            # 检查依赖项
            dependencies = plugin_info.get("requirements", [])
            if dependencies:
                # 安装 Python 依赖项
                python_deps = [dep for dep in dependencies if not dep.startswith("plugin:")]
                if python_deps:
                    try:
                        for dep in python_deps:
                            await self._install_python_dependency(dep)
                    except Exception as e:
                        return {"success": False, "message": f"安装依赖项失败: {e}"}
                
                # 检查插件依赖项
                plugin_deps = [dep[7:] for dep in dependencies if dep.startswith("plugin:")]
                for dep in plugin_deps:
                    if dep not in self.installed_plugins:
                        return {"success": False, "message": f"缺少依赖插件: {dep}，请先安装该插件"}
            
            # 插件目标目录
            plugin_dir = self.plugins_dir / plugin_id
            
            # 如果是更新模式，先备份旧版本
            if update and plugin_dir.exists():
                backup_dir = f"{plugin_dir}.bak.{int(time.time())}"
                shutil.move(str(plugin_dir), backup_dir)
            
            # 如果目标目录存在，先删除
            if plugin_dir.exists():
                shutil.rmtree(str(plugin_dir))
            
            # 确定插件根目录
            plugin_src_dir = Path(temp_dir)
            plugin_files = list(plugin_src_dir.glob("**/info.json"))
            if plugin_files:
                plugin_src_dir = plugin_files[0].parent
            
            # 复制插件文件到目标目录
            shutil.copytree(str(plugin_src_dir), str(plugin_dir))
            
            # 重新扫描插件
            self.scan_plugins()
            
            return {
                "success": True, 
                "message": f"插件 {plugin_name} (v{plugin_version}) 安装成功", 
                "plugin_id": plugin_id
            }
        except Exception as e:
            logger.error(f"安装插件出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "message": f"安装插件失败: {str(e)}"}
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    async def uninstall_plugin(self, plugin_id):
        """
        卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            卸载结果
        """
        if plugin_id not in self.installed_plugins:
            return {"success": False, "message": f"插件 {plugin_id} 未安装"}
        
        try:
            plugin_info = self.installed_plugins[plugin_id]
            plugin_path = plugin_info.get("path")
            
            # 检查是否有其他插件依赖此插件
            for pid, pinfo in self.installed_plugins.items():
                if pid == plugin_id:
                    continue
                
                requirements = pinfo.get("requirements", [])
                for req in requirements:
                    if req.startswith("plugin:") and req[7:] == plugin_id:
                        return {
                            "success": False, 
                            "message": f"插件 {pinfo.get('name', pid)} 依赖此插件，无法卸载"
                        }
            
            # 删除插件目录
            if plugin_path and os.path.exists(plugin_path):
                shutil.rmtree(plugin_path)
            
            # 从已安装插件列表中移除
            del self.installed_plugins[plugin_id]
            
            # 如果已加载，从实例列表中移除
            if plugin_id in self.plugin_instances:
                del self.plugin_instances[plugin_id]
            
            return {"success": True, "message": f"插件 {plugin_info.get('name', plugin_id)} 卸载成功"}
        except Exception as e:
            logger.error(f"卸载插件出错: {e}")
            return {"success": False, "message": f"卸载插件失败: {str(e)}"}
    
    async def update_plugin(self, plugin_file):
        """
        更新插件
        
        Args:
            plugin_file: 插件文件路径（zip）
            
        Returns:
            更新结果
        """
        return await self.install_plugin(plugin_file, update=True)
    
    async def _install_python_dependency(self, dependency):
        """
        安装Python依赖项
        
        Args:
            dependency: 依赖项描述
            
        Returns:
            安装结果
        """
        import subprocess
        
        logger.info(f"安装依赖项: {dependency}")
        
        # 执行pip安装
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", dependency,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"安装依赖项失败: {stderr.decode('utf-8', errors='ignore')}")
                raise Exception(f"安装依赖项失败，返回码: {process.returncode}")
            
            logger.info(f"依赖项安装成功: {dependency}")
            return True
        except Exception as e:
            logger.error(f"安装依赖项出错: {e}")
            raise
    
    def get_plugin_list(self):
        """
        获取已安装的插件列表
        
        Returns:
            插件列表
        """
        return list(self.installed_plugins.values())
    
    def get_plugin_info(self, plugin_id):
        """
        获取插件信息
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件信息，如果不存在则返回None
        """
        return self.installed_plugins.get(plugin_id)
    
    async def load_plugin(self, plugin_id):
        """
        加载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            加载结果
        """
        if plugin_id not in self.installed_plugins:
            return {"success": False, "message": f"插件 {plugin_id} 未安装"}
        
        if plugin_id in self.plugin_instances:
            return {"success": True, "message": f"插件 {plugin_id} 已加载", "instance": self.plugin_instances[plugin_id]}
        
        try:
            plugin_info = self.installed_plugins[plugin_id]
            plugin_path = plugin_info.get("path")
            
            # 检查插件目录是否存在
            if not plugin_path or not os.path.exists(plugin_path):
                return {"success": False, "message": f"插件目录不存在: {plugin_path}"}
            
            # 查找主模块文件
            main_file = Path(plugin_path) / "main.py"
            if not main_file.exists():
                return {"success": False, "message": f"插件主模块文件不存在: {main_file}"}
            
            # 加载插件模块
            module_name = f"plugin_{plugin_id}"
            spec = importlib.util.spec_from_file_location(module_name, str(main_file))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 检查模块是否有Plugin类
            if not hasattr(module, "Plugin"):
                return {"success": False, "message": f"插件 {plugin_id} 缺少Plugin类"}
            
            # 实例化插件
            plugin_class = getattr(module, "Plugin")
            plugin_instance = plugin_class()
            
            # 存储插件实例
            self.plugin_instances[plugin_id] = plugin_instance
            
            return {"success": True, "message": f"插件 {plugin_info.get('name', plugin_id)} 加载成功", "instance": plugin_instance}
        except Exception as e:
            logger.error(f"加载插件出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "message": f"加载插件失败: {str(e)}"}
    
    async def unload_plugin(self, plugin_id):
        """
        卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            卸载结果
        """
        if plugin_id not in self.plugin_instances:
            return {"success": False, "message": f"插件 {plugin_id} 未加载"}
        
        try:
            plugin_instance = self.plugin_instances[plugin_id]
            
            # 如果插件有卸载方法，先调用
            if hasattr(plugin_instance, "unload") and callable(getattr(plugin_instance, "unload")):
                await plugin_instance.unload()
            
            # 从实例列表中移除
            del self.plugin_instances[plugin_id]
            
            return {"success": True, "message": f"插件 {self.installed_plugins.get(plugin_id, {}).get('name', plugin_id)} 已卸载"}
        except Exception as e:
            logger.error(f"卸载插件出错: {e}")
            return {"success": False, "message": f"卸载插件失败: {str(e)}"}
    
    async def rollback_plugin(self, plugin_id):
        """
        回滚插件到之前版本
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            回滚结果
        """
        if plugin_id not in self.installed_plugins:
            return {"success": False, "message": f"插件 {plugin_id} 未安装"}
        
        try:
            plugin_info = self.installed_plugins[plugin_id]
            plugin_path = plugin_info.get("path")
            
            # 查找备份
            plugin_backups = list(Path(self.plugins_dir).glob(f"{plugin_id}.bak.*"))
            if not plugin_backups:
                return {"success": False, "message": f"未找到插件 {plugin_id} 的备份版本"}
            
            # 按时间排序，找到最新的备份
            latest_backup = sorted(plugin_backups, key=lambda p: int(p.name.split(".")[-1]))[-1]
            
            # 先卸载插件
            if plugin_id in self.plugin_instances:
                await self.unload_plugin(plugin_id)
            
            # 删除当前版本
            if os.path.exists(plugin_path):
                shutil.rmtree(plugin_path)
            
            # 恢复备份
            shutil.move(str(latest_backup), plugin_path)
            
            # 重新扫描插件
            self.scan_plugins()
            
            return {"success": True, "message": f"插件 {plugin_info.get('name', plugin_id)} 已回滚到之前版本"}
        except Exception as e:
            logger.error(f"回滚插件出错: {e}")
            return {"success": False, "message": f"回滚插件失败: {str(e)}"}
    
    async def enable_plugin(self, plugin_id):
        """
        启用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            启用结果
        """
        if plugin_id not in self.installed_plugins:
            return {"success": False, "message": f"插件 {plugin_id} 未安装"}
        
        try:
            # 加载插件
            load_result = await self.load_plugin(plugin_id)
            if not load_result.get("success"):
                return load_result
            
            # 如果插件有启用方法，调用
            plugin_instance = self.plugin_instances[plugin_id]
            if hasattr(plugin_instance, "enable") and callable(getattr(plugin_instance, "enable")):
                await plugin_instance.enable()
            
            # 更新插件状态
            plugin_info = self.installed_plugins[plugin_id]
            plugin_path = plugin_info.get("path")
            info_file = Path(plugin_path) / "info.json"
            
            if info_file.exists():
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                info["enabled"] = True
                
                with open(info_file, "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "message": f"插件 {plugin_info.get('name', plugin_id)} 已启用"}
        except Exception as e:
            logger.error(f"启用插件出错: {e}")
            return {"success": False, "message": f"启用插件失败: {str(e)}"}
    
    async def disable_plugin(self, plugin_id):
        """
        禁用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            禁用结果
        """
        if plugin_id not in self.installed_plugins:
            return {"success": False, "message": f"插件 {plugin_id} 未安装"}
        
        try:
            # 如果插件已加载，先卸载
            if plugin_id in self.plugin_instances:
                unload_result = await self.unload_plugin(plugin_id)
                if not unload_result.get("success"):
                    return unload_result
            
            # 更新插件状态
            plugin_info = self.installed_plugins[plugin_id]
            plugin_path = plugin_info.get("path")
            info_file = Path(plugin_path) / "info.json"
            
            if info_file.exists():
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                info["enabled"] = False
                
                with open(info_file, "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "message": f"插件 {plugin_info.get('name', plugin_id)} 已禁用"}
        except Exception as e:
            logger.error(f"禁用插件出错: {e}")
            return {"success": False, "message": f"禁用插件失败: {str(e)}"}

# 创建一个全局的插件管理器实例
plugin_manager = None

def init_plugin_manager():
    """初始化全局插件管理器实例"""
    global plugin_manager
    if not plugin_manager:
        plugin_manager = PluginManager()
    return plugin_manager

def get_plugin_manager():
    """获取插件管理器实例"""
    global plugin_manager
    if not plugin_manager:
        plugin_manager = init_plugin_manager()
    return plugin_manager 