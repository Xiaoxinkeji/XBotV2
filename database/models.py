from sqlalchemy import Column, Integer, Text, DateTime, String, ForeignKey, Index, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# 创建基本模型类
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    wxid = Column(String, primary_key=True)
    nickname = Column(String)
    avatar_url = Column(String, nullable=True)
    points = Column(Integer, default=0)
    sign_in_count = Column(Integer, default=0)
    last_sign_in = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class GroupInfo(Base):
    __tablename__ = "groups"
    
    wxid = Column(String, primary_key=True)
    name = Column(String)
    member_count = Column(Integer, default=0)
    owner_wxid = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String, ForeignKey("groups.wxid"), index=True)
    user_id = Column(String, ForeignKey("users.wxid"), index=True)
    group_nickname = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    join_time = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_group_member', 'group_id', 'user_id', unique=True),
    )

class Plugin(Base):
    __tablename__ = "plugins"
    
    name = Column(String, primary_key=True)
    description = Column(Text, nullable=True)
    version = Column(String)
    author = Column(String)
    enabled = Column(Boolean, default=True)
    category = Column(String, default="未分类")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PluginCall(Base):
    __tablename__ = "plugin_calls"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_name = Column(String, ForeignKey("plugins.name"), index=True)
    user_id = Column(String, ForeignKey("users.wxid"), nullable=True, index=True)
    group_id = Column(String, ForeignKey("groups.wxid"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    execution_time = Column(Float)  # 执行时间（毫秒）
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    sender_id = Column(String, ForeignKey("users.wxid"), index=True)
    group_id = Column(String, ForeignKey("groups.wxid"), index=True)
    msg_type = Column(Integer)
    wx_msg_id = Column(String, unique=True)
    
    __table_args__ = (
        Index('idx_message_sender_time', 'sender_id', 'timestamp'),
        Index('idx_message_group_time', 'group_id', 'timestamp')
    ) 