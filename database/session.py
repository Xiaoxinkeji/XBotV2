from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import os
import logging
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger("web_ui.db")

# 尝试从环境变量获取数据库连接URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 如果没有设置环境变量或连接失败，使用SQLite
if not DATABASE_URL:
    logger.warning("数据库URL未设置，使用SQLite作为备选")
    # 使用异步SQLite引擎 
    DATABASE_URL = "sqlite+aiosqlite:///./xybot.db"

# 创建异步引擎
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # 设置为True可以在控制台查看SQL语句
        future=True
    )
    logger.info(f"使用数据库: {DATABASE_URL.split('://', 1)[0]}")
except Exception as e:
    logger.error(f"创建数据库引擎失败: {str(e)}")
    # 使用内存SQLite作为最后的备选
    logger.warning("使用内存SQLite作为备选")
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True
    )

# 创建异步会话工厂
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@asynccontextmanager
async def get_session():
    """获取异步数据库会话的上下文管理器"""
    session = async_session_factory()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

# 暂时提供一个同步版本，用于测试或简单场景
def get_sync_session():
    """获取同步数据库会话（仅用于测试）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker as sync_sessionmaker
    
    sync_engine = create_engine(
        DATABASE_URL.replace('+asyncpg', ''),
        echo=False
    )
    
    SyncSessionLocal = sync_sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=sync_engine
    )
    
    return SyncSessionLocal()

# 数据库初始化函数
async def init_db():
    """初始化数据库"""
    global engine, async_session_factory  # 添加global声明，使函数内可以修改全局变量
    
    # 导入模型类以确保它们被注册
    from database.models import Base
    
    try:
        # 尝试连接数据库
        async with engine.begin() as conn:
            # 创建所有表
            # await conn.run_sync(Base.metadata.drop_all)  # 取消注释此行将重置数据库
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        if "sqlite" in DATABASE_URL:
            logger.warning("SQLite数据库初始化失败，可能影响部分功能")
        else:
            logger.warning("尝试使用SQLite作为备选数据库...")
            # 重新创建SQLite引擎
            sqlite_url = "sqlite+aiosqlite:///./xybot.db" 
            engine = create_async_engine(sqlite_url, echo=False, future=True)
            async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            # 重新尝试初始化
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("使用SQLite备选数据库初始化成功") 