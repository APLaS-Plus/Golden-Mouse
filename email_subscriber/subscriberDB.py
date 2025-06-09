from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Table,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import IntegrityError
import logging
import pathlib
from .config import DB_DIR, DB_URL

# 创建 Base 类
Base = declarative_base()

# 订阅者-平台关联表（多对多关系）
subscriber_platform = Table(
    "subscriber_platform",
    Base.metadata,
    Column(
        "subscriber_id", Integer, ForeignKey("email_subscribers.id"), primary_key=True
    ),
    Column("platform_id", Integer, ForeignKey("platforms.id"), primary_key=True),
)


class Platform(Base):
    """平台数据模型"""

    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # 平台名称唯一

    def __repr__(self):
        return f"Platform(id={self.id}, name='{self.name}')"


class EmailSubscriberDB(Base):
    """邮箱订阅者数据模型"""

    __tablename__ = "email_subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)  # 邮箱地址唯一
    all_platforms = Column(Boolean, default=True)  # 是否订阅所有平台
    send_frequency = Column(Integer, default=24)  # 发送频率（小时），默认24小时

    # 与平台的多对多关系
    platforms = relationship(
        "Platform", secondary=subscriber_platform, backref="subscribers"
    )

    def __repr__(self):
        return f"EmailSubscriber(id={self.id}, email='{self.email}', all_platforms={self.all_platforms}, send_frequency={self.send_frequency})"


class EmailStats(Base):
    """邮件统计数据模型"""

    __tablename__ = "email_stats"

    id = Column(Integer, primary_key=True)
    total_emails_sent = Column(Integer, default=0)  # 总共发送的邮件数

    def __repr__(self):
        return f"EmailStats(id={self.id}, total_emails_sent={self.total_emails_sent})"


class EmailSubscriberManager:
    """邮箱订阅者管理类"""

    def __init__(self):
        """初始化数据库连接"""
        # 确保数据库目录存在
        DB_DIR.mkdir(parents=True, exist_ok=True)

        self.url = DB_URL
        self.engine = create_engine(DB_URL)
        print(f"数据库目录已存在: {DB_DIR.exists()}")
        print(f"连接数据库: {DB_URL}")

        # 创建或更新所有表
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # 初始化平台数据
        self._init_platforms()
        print("数据库初始化完成")

    def _init_platforms(self):
        """初始化平台数据"""
        session = self.get_session()
        try:
            # 检查是否已有平台数据
            platforms_count = session.query(Platform).count()
            print(f"当前平台数量: {platforms_count}")

            if platforms_count == 0:
                # 按拼音顺序添加平台
                platforms = [
                    "安全保卫中心",
                    "采购与招投标管理中心",
                    "餐饮服务中心",
                    "城市交通与物流学院",
                    "创意设计学院",
                    "大数据与互联网学院",
                    "党委宣传部",
                    "党委组织部（党委统战部）",
                    "党政办公室",
                    "分析测试中心",
                    "工程物理学院",
                    "工会",
                    "国际合作与交流部（港澳台工作办公室）",
                    "国有资产与实验室管理开发部",
                    "后勤保障部",
                    "健康与环境工程学院",
                    "教学质量督导室",
                    "教务部",
                    "计划财务部",
                    "集成电路与光电芯片学院",
                    "科研与校企合作部",
                    "马克思主义学院(人文社科学院)",
                    "人力资源部",
                    "商学院",
                    "体育场馆管理中心",
                    "体育与艺术学院",
                    "图书馆",
                    "外国语学院",
                    "未来技术学院",
                    "网络安全和信息化工作办公室",
                    "校团委",
                    "校医院",
                    "新材料与新能源学院",
                    "学生部",
                    "学生就业指导中心",
                    "药学院",
                    "研究生院",
                    "战略规划与发展办公室",
                    "中德智能制造学院",
                ]

                for name in platforms:
                    platform = Platform(name=name)
                    session.add(platform)
                    print(f"添加平台: {name}")

                session.commit()
                logging.info(f"初始化平台数据完成，添加了 {len(platforms)} 个平台")
                print(f"成功添加 {len(platforms)} 个平台")
            else:
                print(f"平台数据已存在，跳过初始化")
        except Exception as e:
            session.rollback()
            logging.error(f"初始化平台数据失败: {str(e)}")
            print(f"初始化平台数据失败: {str(e)}")
        finally:
            session.close()

    def get_session(self):
        """获取数据库会话"""
        return self.Session()

    def get_all_platforms(self):
        """获取所有平台"""
        session = self.get_session()
        try:
            return session.query(Platform).order_by(Platform.name).all()
        finally:
            session.close()

    def get_platform_id_by_name(self, platform_name):
        """根据平台名称获取平台ID"""
        session = self.get_session()
        try:
            platform = (
                session.query(Platform).filter(Platform.name == platform_name).first()
            )
            return platform.id if platform else None
        finally:
            session.close()

    def add_subscriber(
        self, email, platform_ids=None, all_platforms=True, send_frequency=24
    ):
        """添加订阅者到数据库"""
        session = self.get_session()
        try:
            # 验证发送频率
            try:
                send_frequency = int(send_frequency)
                if not (1 <= send_frequency <= 24):
                    send_frequency = 24
            except (ValueError, TypeError):
                send_frequency = 24

            # 打印调试信息
            print(
                f"尝试添加/更新订阅者: {email}, all_platforms={all_platforms}, platform_ids={platform_ids}, send_frequency={send_frequency}"
            )

            # 检查邮箱是否已存在
            existing = (
                session.query(EmailSubscriberDB)
                .filter(EmailSubscriberDB.email == email)
                .first()
            )

            is_new_subscriber = existing is None

            if existing:
                print(f"邮箱 {email} 已存在，更新订阅设置")
                # 如果已存在，更新订阅平台和频率
                existing.all_platforms = all_platforms
                existing.send_frequency = send_frequency

                if all_platforms:
                    # 全平台订阅，清空特定平台
                    existing.platforms = []
                elif platform_ids and len(platform_ids) > 0:
                    # 特定平台订阅
                    platforms = (
                        session.query(Platform)
                        .filter(Platform.id.in_(platform_ids))
                        .all()
                    )
                    print(f"找到 {len(platforms)} 个匹配的平台")
                    existing.platforms = platforms
                else:
                    # 没有选择任何平台，使用默认的全部平台
                    existing.all_platforms = True

                session.commit()
                logging.info(f"更新订阅者订阅平台: {email}")
                print(f"成功更新 {email} 的订阅设置")
                return True, is_new_subscriber
            else:
                # 创建新订阅者
                print(f"创建新订阅者: {email}")
                subscriber = EmailSubscriberDB(
                    email=email,
                    all_platforms=all_platforms,
                    send_frequency=send_frequency,
                )

                if not all_platforms and platform_ids and len(platform_ids) > 0:
                    # 如果不是全平台订阅，设置特定平台
                    platforms = (
                        session.query(Platform)
                        .filter(Platform.id.in_(platform_ids))
                        .all()
                    )
                    print(f"为新订阅者设置 {len(platforms)} 个平台")
                    subscriber.platforms = platforms

                session.add(subscriber)
                session.commit()
                logging.info(f"添加订阅者成功: {email}")
                print(f"成功添加新订阅者: {email}")
                return True, is_new_subscriber
        except IntegrityError as e:
            session.rollback()
            logging.warning(f"订阅者邮箱已存在(并发添加): {email}, 错误: {str(e)}")
            print(f"数据库完整性错误: {str(e)}")
            return False, False
        except Exception as e:
            session.rollback()
            logging.error(f"添加订阅者失败: {str(e)}")
            print(f"添加订阅者失败: {str(e)}")
            return False, False
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
            # 使用joinedload预加载platforms关系
            from sqlalchemy.orm import joinedload

            return (
                session.query(EmailSubscriberDB)
                .options(joinedload(EmailSubscriberDB.platforms))
                .all()
            )
        finally:
            session.close()

    def get_subscriber_by_email(self, email):
        """根据邮箱获取订阅者信息"""
        session = self.get_session()
        try:
            from sqlalchemy.orm import joinedload

            return (
                session.query(EmailSubscriberDB)
                .options(joinedload(EmailSubscriberDB.platforms))
                .filter(EmailSubscriberDB.email == email)
                .first()
            )
        finally:
            session.close()

    def get_subscribers_by_frequency(self, frequency_hours):
        """根据发送频率获取订阅者"""
        session = self.get_session()
        try:
            from sqlalchemy.orm import joinedload

            return (
                session.query(EmailSubscriberDB)
                .options(joinedload(EmailSubscriberDB.platforms))
                .filter(EmailSubscriberDB.send_frequency == frequency_hours)
                .all()
            )
        finally:
            session.close()

    def get_stats(self):
        """获取统计数据"""
        session = self.get_session()
        try:
            stats = session.query(EmailStats).first()
            subscriber_count = session.query(EmailSubscriberDB).count()

            if not stats:
                stats = EmailStats(total_emails_sent=0)
                session.add(stats)
                session.commit()

            return {
                "subscriber_count": subscriber_count,
                "total_emails_sent": stats.total_emails_sent,
            }
        finally:
            session.close()

    def increment_emails_sent(self, count=1):
        """增加已发送邮件计数"""
        session = self.get_session()
        try:
            stats = session.query(EmailStats).first()
            if not stats:
                stats = EmailStats(total_emails_sent=count)
                session.add(stats)
            else:
                stats.total_emails_sent += count

            session.commit()
            return stats.total_emails_sent
        except Exception as e:
            session.rollback()
            logging.error(f"更新邮件统计失败: {str(e)}")
            return 0
        finally:
            session.close()
