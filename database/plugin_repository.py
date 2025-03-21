import json
import os
import time
from pathlib import Path
import aiohttp
import asyncio
import sqlite3
from loguru import logger

class PluginRepository:
    """
    插件市场仓库管理类
    负责从远程仓库获取插件信息，并提供本地缓存和检索功能
    """
    
    def __init__(self, db_path="database/plugin_repo.db", cache_dir="resource/plugin_cache"):
        """
        初始化插件仓库
        
        Args:
            db_path: 数据库路径
            cache_dir: 插件缓存目录
        """
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 官方插件仓库URL
        self.official_repos = [
            "https://raw.githubusercontent.com/XYBot/plugins-repo/main/index.json",
        ]
        
        # 第三方插件仓库列表（从配置中读取）
        self.third_party_repos = []
        
        # 确保数据库存在并初始化表结构
        self._init_db()
        
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建插件信息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plugins (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            author TEXT,
            version TEXT,
            tags TEXT,
            repository TEXT,
            download_url TEXT,
            homepage_url TEXT,
            last_update INTEGER,
            stars INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            is_official INTEGER DEFAULT 0,
            requirements TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
        ''')
        
        # 创建插件版本历史表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plugin_versions (
            plugin_id TEXT,
            version TEXT,
            download_url TEXT,
            release_notes TEXT,
            released_at INTEGER,
            PRIMARY KEY (plugin_id, version),
            FOREIGN KEY (plugin_id) REFERENCES plugins(id)
        )
        ''')
        
        # 创建用户插件评分表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plugin_ratings (
            plugin_id TEXT,
            user_id TEXT,
            rating INTEGER,
            comment TEXT,
            created_at INTEGER,
            PRIMARY KEY (plugin_id, user_id),
            FOREIGN KEY (plugin_id) REFERENCES plugins(id)
        )
        ''')
        
        # 创建仓库表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            url TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            is_official INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            last_sync INTEGER DEFAULT 0
        )
        ''')
        
        # 如果没有官方仓库记录，添加默认的
        cursor.execute('SELECT COUNT(*) FROM repositories WHERE is_official = 1')
        if cursor.fetchone()[0] == 0:
            for repo in self.official_repos:
                cursor.execute(
                    'INSERT INTO repositories (url, name, description, is_official, enabled) VALUES (?, ?, ?, ?, ?)',
                    (repo, "官方插件仓库", "XYBot官方维护的插件仓库", 1, 1)
                )
        
        conn.commit()
        conn.close()
    
    async def sync_repositories(self):
        """从所有启用的仓库同步插件信息"""
        logger.info("开始同步插件仓库")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有启用的仓库
        cursor.execute('SELECT url FROM repositories WHERE enabled = 1')
        repos = cursor.fetchall()
        
        for repo_url, in repos:
            try:
                await self._sync_repository(repo_url, conn)
            except Exception as e:
                logger.error(f"同步仓库 {repo_url} 失败: {e}")
        
        # 更新仓库最后同步时间
        cursor.execute(
            'UPDATE repositories SET last_sync = ? WHERE enabled = 1',
            (int(time.time()),)
        )
        
        conn.commit()
        conn.close()
        logger.success("插件仓库同步完成")
    
    async def _sync_repository(self, repo_url, conn):
        """
        从指定仓库同步插件信息
        
        Args:
            repo_url: 仓库URL
            conn: 数据库连接
        """
        logger.info(f"开始同步仓库: {repo_url}")
        cursor = conn.cursor()
        
        # 检查仓库是否为官方仓库
        cursor.execute('SELECT is_official FROM repositories WHERE url = ?', (repo_url,))
        is_official = cursor.fetchone()[0]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(repo_url) as response:
                    if response.status == 200:
                        repo_data = await response.json()
                        
                        # 处理仓库中的插件列表
                        for plugin in repo_data.get("plugins", []):
                            plugin_id = plugin.get("id")
                            
                            # 检查插件是否已存在
                            cursor.execute('SELECT id FROM plugins WHERE id = ?', (plugin_id,))
                            exists = cursor.fetchone()
                            
                            current_time = int(time.time())
                            
                            if exists:
                                # 更新现有插件
                                cursor.execute('''
                                UPDATE plugins SET 
                                    name = ?, description = ?, author = ?, version = ?,
                                    tags = ?, repository = ?, download_url = ?, homepage_url = ?,
                                    last_update = ?, requirements = ?, updated_at = ?,
                                    is_official = ?
                                WHERE id = ?
                                ''', (
                                    plugin.get("name", ""),
                                    plugin.get("description", ""),
                                    plugin.get("author", ""),
                                    plugin.get("version", ""),
                                    json.dumps(plugin.get("tags", [])),
                                    repo_url,
                                    plugin.get("download_url", ""),
                                    plugin.get("homepage_url", ""),
                                    plugin.get("last_update", current_time),
                                    json.dumps(plugin.get("requirements", [])),
                                    current_time,
                                    is_official,
                                    plugin_id
                                ))
                            else:
                                # 添加新插件
                                cursor.execute('''
                                INSERT INTO plugins (
                                    id, name, description, author, version,
                                    tags, repository, download_url, homepage_url,
                                    last_update, requirements, created_at, updated_at,
                                    is_official
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    plugin_id,
                                    plugin.get("name", ""),
                                    plugin.get("description", ""),
                                    plugin.get("author", ""),
                                    plugin.get("version", ""),
                                    json.dumps(plugin.get("tags", [])),
                                    repo_url,
                                    plugin.get("download_url", ""),
                                    plugin.get("homepage_url", ""),
                                    plugin.get("last_update", current_time),
                                    json.dumps(plugin.get("requirements", [])),
                                    current_time,
                                    current_time,
                                    is_official
                                ))
                            
                            # 处理插件版本信息
                            for version in plugin.get("versions", []):
                                cursor.execute('''
                                INSERT OR REPLACE INTO plugin_versions (
                                    plugin_id, version, download_url, release_notes, released_at
                                ) VALUES (?, ?, ?, ?, ?)
                                ''', (
                                    plugin_id,
                                    version.get("version", ""),
                                    version.get("download_url", ""),
                                    version.get("release_notes", ""),
                                    version.get("released_at", current_time)
                                ))
                    else:
                        logger.warning(f"获取仓库数据失败: {repo_url}, 状态码: {response.status}")
        except Exception as e:
            logger.error(f"同步仓库出错: {repo_url}, 错误: {e}")
            raise
    
    def get_plugins(self, category=None, query=None, limit=50, offset=0, sort_by="updated_at", sort_order="desc"):
        """
        获取插件列表
        
        Args:
            category: 插件分类
            query: 搜索关键字
            limit: 返回数量限制
            offset: 偏移量（分页）
            sort_by: 排序字段
            sort_order: 排序顺序 (asc, desc)
            
        Returns:
            插件列表和总数
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        params = []
        where_clauses = []
        
        if category:
            where_clauses.append("json_extract(tags, '$') LIKE ?")
            params.append(f"%{category}%")
        
        if query:
            where_clauses.append("(name LIKE ? OR description LIKE ? OR author LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) FROM plugins WHERE {where_clause}", params)
        total = cursor.fetchone()[0]
        
        # 构建排序语句
        valid_sort_fields = ["name", "author", "updated_at", "stars", "downloads"]
        valid_sort_orders = ["asc", "desc"]
        
        sort_by = sort_by if sort_by in valid_sort_fields else "updated_at"
        sort_order = sort_order.lower() if sort_order.lower() in valid_sort_orders else "desc"
        
        # 获取插件列表
        cursor.execute(f'''
        SELECT 
            p.*, 
            (SELECT AVG(rating) FROM plugin_ratings WHERE plugin_id = p.id) as avg_rating,
            (SELECT COUNT(*) FROM plugin_ratings WHERE plugin_id = p.id) as rating_count
        FROM plugins p
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order}
        LIMIT ? OFFSET ?
        ''', params + [limit, offset])
        
        plugins = []
        for row in cursor.fetchall():
            plugin = dict(row)
            
            # 解析JSON字段
            try:
                plugin['tags'] = json.loads(plugin['tags'])
            except:
                plugin['tags'] = []
                
            try:
                plugin['requirements'] = json.loads(plugin['requirements'])
            except:
                plugin['requirements'] = []
            
            plugins.append(plugin)
        
        conn.close()
        return plugins, total
    
    def get_plugin_details(self, plugin_id):
        """
        获取插件详细信息
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件详细信息，包括版本历史和评分
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取插件基本信息
        cursor.execute('''
        SELECT 
            p.*, 
            (SELECT AVG(rating) FROM plugin_ratings WHERE plugin_id = p.id) as avg_rating,
            (SELECT COUNT(*) FROM plugin_ratings WHERE plugin_id = p.id) as rating_count
        FROM plugins p
        WHERE id = ?
        ''', (plugin_id,))
        
        plugin_row = cursor.fetchone()
        if not plugin_row:
            conn.close()
            return None
        
        plugin = dict(plugin_row)
        
        # 解析JSON字段
        try:
            plugin['tags'] = json.loads(plugin['tags'])
        except:
            plugin['tags'] = []
            
        try:
            plugin['requirements'] = json.loads(plugin['requirements'])
        except:
            plugin['requirements'] = []
        
        # 获取版本历史
        cursor.execute('''
        SELECT * FROM plugin_versions
        WHERE plugin_id = ?
        ORDER BY released_at DESC
        ''', (plugin_id,))
        
        plugin['versions'] = [dict(row) for row in cursor.fetchall()]
        
        # 获取评分和评论
        cursor.execute('''
        SELECT * FROM plugin_ratings
        WHERE plugin_id = ?
        ORDER BY created_at DESC
        ''', (plugin_id,))
        
        plugin['ratings'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return plugin
    
    async def download_plugin(self, plugin_id, version=None):
        """
        下载插件
        
        Args:
            plugin_id: 插件ID
            version: 指定版本，如不指定则下载最新版本
            
        Returns:
            插件本地缓存路径
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if version:
                # 下载指定版本
                cursor.execute('''
                SELECT pv.download_url, p.name
                FROM plugin_versions pv
                JOIN plugins p ON p.id = pv.plugin_id
                WHERE pv.plugin_id = ? AND pv.version = ?
                ''', (plugin_id, version))
                result = cursor.fetchone()
                
                if not result:
                    conn.close()
                    raise ValueError(f"找不到插件 {plugin_id} 的版本 {version}")
                
                download_url = result['download_url']
                plugin_name = result['name']
                
            else:
                # 下载最新版本
                cursor.execute('''
                SELECT download_url, name, version
                FROM plugins
                WHERE id = ?
                ''', (plugin_id,))
                result = cursor.fetchone()
                
                if not result:
                    conn.close()
                    raise ValueError(f"找不到插件 {plugin_id}")
                
                download_url = result['download_url']
                plugin_name = result['name']
                version = result['version']
            
            # 构建缓存文件路径
            cache_file_path = self.cache_dir / f"{plugin_id}_{version}.zip"
            
            # 下载插件
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        # 保存到缓存文件
                        with open(cache_file_path, 'wb') as f:
                            f.write(await response.read())
                        
                        # 更新下载计数
                        cursor.execute('''
                        UPDATE plugins
                        SET downloads = downloads + 1
                        WHERE id = ?
                        ''', (plugin_id,))
                        
                        conn.commit()
                        
                        return str(cache_file_path)
                    else:
                        raise ValueError(f"下载插件失败: 状态码 {response.status}")
                        
        except Exception as e:
            logger.error(f"下载插件出错: {e}")
            raise
        finally:
            conn.close()
    
    def add_plugin_rating(self, plugin_id, user_id, rating, comment=""):
        """
        为插件添加评分和评论
        
        Args:
            plugin_id: 插件ID
            user_id: 用户ID
            rating: 评分 (1-5)
            comment: 评论内容
            
        Returns:
            成功返回True，失败返回False
        """
        if not 1 <= rating <= 5:
            raise ValueError("评分必须在1-5之间")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查插件是否存在
            cursor.execute('SELECT id FROM plugins WHERE id = ?', (plugin_id,))
            if not cursor.fetchone():
                conn.close()
                raise ValueError(f"插件 {plugin_id} 不存在")
            
            current_time = int(time.time())
            
            # 插入或更新评分
            cursor.execute('''
            INSERT OR REPLACE INTO plugin_ratings (
                plugin_id, user_id, rating, comment, created_at
            ) VALUES (?, ?, ?, ?, ?)
            ''', (plugin_id, user_id, rating, comment, current_time))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加插件评分出错: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def add_repository(self, url, name, description="", is_official=0):
        """
        添加插件仓库
        
        Args:
            url: 仓库URL
            name: 仓库名称
            description: 仓库描述
            is_official: 是否为官方仓库
            
        Returns:
            成功返回True，失败返回False
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查仓库是否已存在
            cursor.execute('SELECT url FROM repositories WHERE url = ?', (url,))
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"仓库 {url} 已存在")
            
            # 添加仓库
            cursor.execute('''
            INSERT INTO repositories (
                url, name, description, is_official, enabled
            ) VALUES (?, ?, ?, ?, 1)
            ''', (url, name, description, is_official))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加仓库出错: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_repositories(self):
        """
        获取所有仓库
        
        Returns:
            仓库列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM repositories ORDER BY is_official DESC, name')
        repos = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return repos
    
    def update_repository_status(self, url, enabled):
        """
        更新仓库状态
        
        Args:
            url: 仓库URL
            enabled: 是否启用
            
        Returns:
            成功返回True，失败返回False
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE repositories SET enabled = ? WHERE url = ?', (1 if enabled else 0, url))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新仓库状态出错: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def remove_repository(self, url):
        """
        删除插件仓库
        
        Args:
            url: 仓库URL
            
        Returns:
            成功返回True，失败返回False
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否为官方仓库，官方仓库不能删除
            cursor.execute('SELECT is_official FROM repositories WHERE url = ?', (url,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                raise ValueError(f"仓库 {url} 不存在")
            
            if result[0] == 1:
                conn.close()
                raise ValueError("不能删除官方仓库")
            
            # 删除该仓库中的插件
            cursor.execute('SELECT id FROM plugins WHERE repository = ?', (url,))
            plugins = cursor.fetchall()
            
            for plugin_id, in plugins:
                # 删除插件评分
                cursor.execute('DELETE FROM plugin_ratings WHERE plugin_id = ?', (plugin_id,))
                
                # 删除插件版本
                cursor.execute('DELETE FROM plugin_versions WHERE plugin_id = ?', (plugin_id,))
                
                # 删除插件
                cursor.execute('DELETE FROM plugins WHERE id = ?', (plugin_id,))
            
            # 删除仓库
            cursor.execute('DELETE FROM repositories WHERE url = ?', (url,))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除仓库出错: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

# 创建一个全局的仓库实例
plugin_repository = None

def init_plugin_repository():
    """初始化全局插件仓库实例"""
    global plugin_repository
    if not plugin_repository:
        plugin_repository = PluginRepository()
    return plugin_repository

def get_plugin_repository():
    """获取插件仓库实例"""
    global plugin_repository
    if not plugin_repository:
        plugin_repository = init_plugin_repository()
    return plugin_repository 