from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import os
from sqlalchemy.ext.declarative import declarative_base

# 数据库连接URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://username:password@localhost/xybot"
)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 设置为True可以在控制台查看SQL语句
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
    """初始化数据库表结构"""
    from database.models import Base
    
    async with engine.begin() as conn:
        # 创建所有表
        # await conn.run_sync(Base.metadata.drop_all)  # 取消注释此行将重置数据库
        await conn.run_sync(Base.metadata.create_all) 