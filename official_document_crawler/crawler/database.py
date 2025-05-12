"""
数据库模块

定义数据库模型和操作函数
"""

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import logging
import pathlib

from .config import DATABASE_URI, DATABASE_DIR

# 创建 Base 类
Base = declarative_base()


class Article(Base):
    """文章数据模型"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    source = Column(String)
    title = Column(String)
    date = Column(String)
    detail_time = Column(String)
    click_num = Column(String)
    content = Column(String)
    url = Column(String, unique=True)  # 添加唯一约束
    fujians = Column(String)
    fujian_down_num = Column(Integer)
    raw_data = Column(String)

    def __repr__(self):
        return (
            f"Article(id={self.id}, source='{self.source}', "
            f"title='{self.title}', date='{self.date}')"
        )


class DatabaseManager:
    """数据库管理类"""

    def __init__(self):
        """初始化数据库连接"""
        self.url = DATABASE_URI
        self.engine = create_engine(DATABASE_URI)
        print(f"数据库目录已存在: {DATABASE_DIR.exists()}")
        print(f"连接数据库: {DATABASE_URI}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.Session()

    def add_article(self, article_data):
        """添加文章到数据库"""
        session = self.get_session()
        try:
            # 检查URL是否已存在
            url = article_data.get("url")
            existing = session.query(Article).filter(Article.url == url).first()
            if existing:
                logging.info(f"文章已存在，跳过添加: {url}")
                return False

            # 创建新文章
            article = Article(**article_data)
            session.add(article)
            session.commit()
            logging.info(f"添加文章成功: {url}")
            return url
        except IntegrityError:
            session.rollback()
            logging.warning(f"文章已存在(并发添加): {url}")
            return False
        except Exception as e:
            session.rollback()
            logging.error(f"添加文章失败: {str(e)}")
            return False
        finally:
            session.close()

    def update_article_details(self, article_id, details):
        """更新文章详情"""
        session = self.get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                logging.warning(f"文章不存在，ID: {article_id}")
                return False

            for key, value in details.items():
                if hasattr(article, key):
                    setattr(article, key, value)

            session.commit()
            logging.info(f"更新文章成功，ID: {article_id}")
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"更新文章失败: {str(e)}")
            return False
        finally:
            session.close()

    def get_all_articles(self):
        """获取所有文章"""
        session = self.get_session()
        try:
            return session.query(Article).all()
        finally:
            session.close()


# 自定义异常类
class CustomError(Exception):
    """自定义异常类，用于处理爬虫过程中的特定错误"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"CustomError: {self.message}"
