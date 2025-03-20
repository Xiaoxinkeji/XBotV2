from sqlalchemy import Column, Integer, Text, DateTime, String, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from datetime import datetime

# 创建声明性基类
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    wxid = Column(String, primary_key=True)
    nickname = Column(String)
    remark = Column(String)
    last_seen = Column(DateTime, default=datetime.now)
    
class GroupInfo(Base):
    __tablename__ = "groups"
    
    wxid = Column(String, primary_key=True)
    group_name = Column(String)
    member_count = Column(Integer)
    last_updated = Column(DateTime, default=datetime.now)

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