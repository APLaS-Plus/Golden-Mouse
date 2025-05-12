from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import logging
import pathlib
from .config import DB_DIR, DB_URL

# 创建 Base 类
Base = declarative_base()


class EmailSubscriberDB(Base):
    """邮箱订阅者数据模型"""

    __tablename__ = "email_subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)  # 邮箱地址唯一

    def __repr__(self):
        return f"EmailSubscriber(id={self.id}, email='{self.email}')"


class EmailSubscriberManager:
    """邮箱订阅者管理类"""

    def __init__(self):
        """初始化数据库连接"""
        self.url = DB_URL
        self.engine = create_engine(DB_URL)
        print(f"数据库目录已存在: {DB_DIR.exists()}")
        print(f"连接数据库: {DB_URL}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.Session()

    def add_subscriber(self, email):
        """添加订阅者到数据库"""
        session = self.get_session()
        try:
            # 检查邮箱是否已存在
            existing = (
                session.query(EmailSubscriberDB)
                .filter(EmailSubscriberDB.email == email)
                .first()
            )
            if existing:
                logging.info(f"订阅者邮箱已存在，跳过添加: {email}")
                return False

            # 创建新订阅者
            subscriber = EmailSubscriberDB(email=email)
            session.add(subscriber)
            session.commit()
            logging.info(f"添加订阅者成功: {email}")
            return True
        except IntegrityError:
            session.rollback()
            logging.warning(f"订阅者邮箱已存在(并发添加): {email}")
            return False
        except Exception as e:
            session.rollback()
            logging.error(f"添加订阅者失败: {str(e)}")
            return False
        finally:
            session.close()

    def delete_subscriber(self, email):
        """根据邮箱删除订阅者"""
        session = self.get_session()
        try:
            subscriber = (
                session.query(EmailSubscriberDB)
                .filter(EmailSubscriberDB.email == email)
                .first()
            )
            if not subscriber:
                logging.warning(f"订阅者不存在，邮箱: {email}")
                return False

            session.delete(subscriber)
            session.commit()
            logging.info(f"删除订阅者成功，邮箱: {email}")
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"删除订阅者失败: {str(e)}")
            return False
        finally:
            session.close()

    def get_all_subscribers(self):
        """获取所有订阅者"""
        session = self.get_session()
        try:
            return session.query(EmailSubscriberDB).all()
        finally:
            session.close()
