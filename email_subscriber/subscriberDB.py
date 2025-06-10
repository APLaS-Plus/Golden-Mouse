from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Table,
    ForeignKey,
    Boolean,
    DateTime,
    text,  # 添加 text 导入
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import IntegrityError
import logging
import pathlib
from datetime import datetime
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
    last_email_sent_time = Column(DateTime, nullable=True)  # 上次发送邮件的时间

    # 与平台的多对多关系
    platforms = relationship(
        "Platform", secondary=subscriber_platform, backref="subscribers"
    )

    def __repr__(self):
        return f"EmailSubscriber(id={self.id}, email='{self.email}', all_platforms={self.all_platforms}, send_frequency={self.send_frequency}, last_sent={self.last_email_sent_time})"


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

        # 检查并升级数据库结构
        self._upgrade_database_structure()

        # 初始化平台数据
        self._init_platforms()

        # 检查数据库兼容性并处理老用户
        self._ensure_database_compatibility()

        print("数据库初始化完成")

    def _upgrade_database_structure(self):
        """升级数据库结构，添加缺失的字段"""
        try:
            # 检查 last_email_sent_time 字段是否存在
            with self.engine.connect() as conn:
                # 获取表信息
                result = conn.execute(text("PRAGMA table_info(email_subscribers)"))
                columns = [row[1] for row in result.fetchall()]

                if "last_email_sent_time" not in columns:
                    print("检测到数据库结构需要升级：添加 last_email_sent_time 字段")
                    # 添加缺失的字段
                    conn.execute(
                        text(
                            "ALTER TABLE email_subscribers ADD COLUMN last_email_sent_time DATETIME"
                        )
                    )
                    conn.commit()
                    print("数据库结构升级完成：已添加 last_email_sent_time 字段")
                    logging.info("数据库结构升级：添加了 last_email_sent_time 字段")
                else:
                    print("数据库结构检查完成：last_email_sent_time 字段已存在")

        except Exception as e:
            print(f"数据库结构升级失败: {str(e)}")
            logging.error(f"数据库结构升级失败: {str(e)}")
            # 不抛出异常，继续执行其他初始化步骤

    def _ensure_database_compatibility(self):
        """确保数据库兼容性，处理版本升级前的用户数据"""
        session = self.get_session()
        try:
            # 检查是否有last_email_sent_time字段为NULL的老用户
            old_users_count = (
                session.query(EmailSubscriberDB)
                .filter(EmailSubscriberDB.last_email_sent_time.is_(None))
                .count()
            )

            if old_users_count > 0:
                print(
                    f"发现 {old_users_count} 个版本升级前的老用户（last_email_sent_time为NULL）"
                )
                print("这些用户将在下次推送时收到邮件（作为首次推送处理）")
                logging.info(f"数据库兼容性检查完成，发现 {old_users_count} 个老用户")
            else:
                print("所有用户数据都已是新版本格式")

        except Exception as e:
            logging.error(f"数据库兼容性检查失败: {str(e)}")
            print(f"数据库兼容性检查失败: {str(e)}")
        finally:
            session.close()

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

    def get_subscribers_due_for_email(self, current_time=None):
        """获取应该接收邮件的订阅者（基于上次发送时间和频率）"""
        if current_time is None:
            current_time = datetime.now()

        session = self.get_session()
        try:
            from sqlalchemy.orm import joinedload

            # 查询条件：
            # 1. 从未发送过邮件的用户（last_email_sent_time为NULL） - 包括版本升级前的老用户
            # 2. 距离上次发送时间已超过设定频率的用户
            subscribers = []

            # 获取所有订阅者
            all_subscribers = (
                session.query(EmailSubscriberDB)
                .options(joinedload(EmailSubscriberDB.platforms))
                .all()
            )

            for subscriber in all_subscribers:
                should_send = False

                if subscriber.last_email_sent_time is None:
                    # 从未发送过邮件（包括版本升级前的老用户）
                    should_send = True
                    logging.debug(
                        f"用户 {subscriber.email} 首次推送或版本升级前用户，将发送邮件"
                    )
                else:
                    # 计算距离上次发送的时间（小时）
                    time_diff = current_time - subscriber.last_email_sent_time
                    hours_since_last = time_diff.total_seconds() / 3600

                    # 检查是否达到发送频率
                    if hours_since_last >= subscriber.send_frequency:
                        should_send = True
                        logging.debug(
                            f"用户 {subscriber.email} 距离上次发送已过 {hours_since_last:.1f} 小时，"
                            f"设定频率 {subscriber.send_frequency} 小时，将发送邮件"
                        )
                    else:
                        logging.debug(
                            f"用户 {subscriber.email} 距离上次发送仅 {hours_since_last:.1f} 小时，"
                            f"设定频率 {subscriber.send_frequency} 小时，暂不发送"
                        )

                if should_send:
                    subscribers.append(subscriber)

            logging.info(
                f"共找到 {len(subscribers)} 个需要推送的用户（总用户数: {len(all_subscribers)}）"
            )
            return subscribers

        finally:
            session.close()

    def update_last_email_sent_time(self, subscriber_id, sent_time=None):
        """更新订阅者的最后邮件发送时间"""
        if sent_time is None:
            sent_time = datetime.now()

        session = self.get_session()
        try:
            subscriber = (
                session.query(EmailSubscriberDB)
                .filter(EmailSubscriberDB.id == subscriber_id)
                .first()
            )

            if subscriber:
                old_time = subscriber.last_email_sent_time
                subscriber.last_email_sent_time = sent_time
                session.commit()

                if old_time is None:
                    logging.info(
                        f"首次更新订阅者 {subscriber.email} 的发送时间为 {sent_time}（版本升级兼容）"
                    )
                else:
                    logging.info(
                        f"更新订阅者 {subscriber.email} 的发送时间：{old_time} -> {sent_time}"
                    )
                return True
            else:
                logging.warning(f"未找到ID为 {subscriber_id} 的订阅者")
                return False

        except Exception as e:
            session.rollback()
            logging.error(f"更新发送时间失败: {str(e)}")
            return False
        finally:
            session.close()

    def batch_update_last_email_sent_time(self, subscriber_ids, sent_time=None):
        """批量更新订阅者的最后邮件发送时间"""
        if sent_time is None:
            sent_time = datetime.now()

        session = self.get_session()
        try:
            updated_count = (
                session.query(EmailSubscriberDB)
                .filter(EmailSubscriberDB.id.in_(subscriber_ids))
                .update({"last_email_sent_time": sent_time}, synchronize_session=False)
            )

            session.commit()
            logging.info(f"批量更新了 {updated_count} 个订阅者的发送时间为 {sent_time}")
            return updated_count

        except Exception as e:
            session.rollback()
            logging.error(f"批量更新发送时间失败: {str(e)}")
            return 0
        finally:
            session.close()
