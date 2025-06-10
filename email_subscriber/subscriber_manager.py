"""
邮件订阅管理模块

提供订阅者管理和邮件发送功能
"""

import re
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime, timedelta

from .subscriberDB import EmailSubscriberManager
from .config import SMTP_SERVER, SMTP_PASSWORD, MY_EMAIL, SUBSCRIBER_MASK


class SubscriberService:
    """邮件订阅服务类，提供订阅管理和邮件发送功能"""

    def __init__(self):
        """初始化数据库管理器和日志配置"""
        self._setup_logging()
        self.logger.info("开始初始化邮件订阅服务")

        # 初始化数据库管理器
        self.db_manager = EmailSubscriberManager()

        self.smtp_server = SMTP_SERVER
        self.smtp_port = 587  # 默认使用TLS端口
        self.sender_email = MY_EMAIL
        self.sender_password = SMTP_PASSWORD
        self.subscriber_pattern = re.compile(SUBSCRIBER_MASK)

        self.logger.info("邮件订阅服务初始化完成")

    def _setup_logging(self):
        """配置日志"""
        self.logger = logging.getLogger("SubscriberService")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def get_all_platforms(self):
        """获取所有可订阅平台"""
        platforms = self.db_manager.get_all_platforms()
        return [(p.id, p.name) for p in platforms]

    def get_subscriber_platforms(self, email):
        """获取订阅者已订阅的平台和发送频率"""
        session = self.db_manager.get_session()
        try:
            from sqlalchemy.orm import joinedload
            from .subscriberDB import EmailSubscriberDB

            subscriber = (
                session.query(EmailSubscriberDB)
                .options(joinedload(EmailSubscriberDB.platforms))
                .filter(EmailSubscriberDB.email == email)
                .first()
            )

            if not subscriber:
                return None

            if subscriber.all_platforms:
                return {
                    "all_platforms": True,
                    "platform_ids": [],
                    "send_frequency": subscriber.send_frequency or 24,
                }
            else:
                return {
                    "all_platforms": False,
                    "platform_ids": [p.id for p in subscriber.platforms],
                    "send_frequency": subscriber.send_frequency or 24,
                }
        finally:
            session.close()

    def add_subscriber(
        self, email, platform_ids=None, all_platforms=True, send_frequency=24
    ):
        """
        添加新的订阅者到数据库或更新现有订阅者的平台设置

        Args:
            email: 订阅者邮箱
            platform_ids: 选择的平台ID列表
            all_platforms: 是否订阅所有平台
            send_frequency: 发送频率（小时）

        Returns:
            tuple: (是否成功, 消消息, 是否为新用户)
        """
        self.logger.info(
            f"处理订阅请求: {email}, all_platforms={all_platforms}, platform_ids={platform_ids}, send_frequency={send_frequency}"
        )

        # 验证邮箱格式
        if not self._is_valid_email(email):
            self.logger.warning(f"邮箱格式无效: {email}")
            return False, "邮箱格式无效", False

        # 验证是否符合掩码规则
        if not self._match_mask(email):
            self.logger.warning(f"邮箱不符合订阅规则: {email}")
            return False, "仅接受学号邮箱（全学号@stumail.sztu.edu.cn）订阅", False

        # 验证发送频率
        try:
            send_frequency = int(send_frequency)
            if not (1 <= send_frequency <= 24):
                send_frequency = 24
        except (ValueError, TypeError):
            send_frequency = 24

        # 处理platform_ids，确保其为整数列表
        if platform_ids:
            try:
                platform_ids = [int(pid) for pid in platform_ids]
                self.logger.info(f"处理后的平台ID: {platform_ids}")
            except (ValueError, TypeError) as e:
                self.logger.error(f"平台ID格式错误: {platform_ids}, 错误: {str(e)}")
                platform_ids = []
                all_platforms = True

        try:
            result, is_new_subscriber = self.db_manager.add_subscriber(
                email, platform_ids, all_platforms, send_frequency
            )

            if result:
                message = "订阅成功" if is_new_subscriber else "订阅设置已更新"
                self.logger.info(
                    f"成功{'添加' if is_new_subscriber else '更新'}订阅者: {email}"
                )
                return True, message, is_new_subscriber
            else:
                self.logger.warning(f"订阅者处理失败: {email}")
                return False, "订阅处理失败，请稍后重试", False

        except Exception as e:
            self.logger.error(f"调用数据库管理器失败: {str(e)}")
            return False, "订阅处理失败，请稍后重试", False

    def delete_subscriber(self, email):
        """
        从数据库中删除订阅者

        Args:
            email: 订阅者邮箱

        Returns:
            tuple: (是否成功, 消息)
        """
        result = self.db_manager.delete_subscriber(email)
        if result:
            self.logger.info(f"成功删除订阅者: {email}")
            return True, "退订成功"
        else:
            self.logger.warning(f"退订失败，邮箱不存在: {email}")
            return False, "该邮箱未订阅或已退订"

    def send_email_to_all_subscribers(
        self, subject, content, html=False, source_platform=None
    ):
        """
        向订阅者发送邮件，可根据文章来源平台筛选

        Args:
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式内容
            source_platform: 文章来源平台名称

        Returns:
            tuple: (成功发送数量, 总订阅者数量)
        """
        subscribers = self.db_manager.get_all_subscribers()
        if not subscribers:
            self.logger.warning("没有订阅者，邮件发送取消")
            return 0, 0

        self.logger.info(f"开始筛选订阅者，来源平台: {source_platform}")
        self.logger.info(f"总订阅者数量: {len(subscribers)}")

        # 如果指定了来源平台，筛选订订阅了该平台的用户
        if source_platform:
            # 先根据平台名称获取平台ID
            platform_id = self.db_manager.get_platform_id_by_name(source_platform)
            if platform_id is None:
                self.logger.warning(f"未找到平台: {source_platform}")
                return 0, 0

            self.logger.info(f"平台 {source_platform} 的ID: {platform_id}")

            filtered_subscribers = []
            for sub in subscribers:
                if sub.all_platforms:
                    # 订阅所有平台的用户
                    filtered_subscribers.append(sub)
                    self.logger.debug(
                        f"用户 {sub.email} 订阅所有平台，包含在发送列表中"
                    )
                else:
                    # 检查用户是否订阅了该平台（使用平台ID匹配）
                    subscribed_platform_ids = [p.id for p in sub.platforms]
                    if platform_id in subscribed_platform_ids:
                        filtered_subscribers.append(sub)
                        self.logger.debug(
                            f"用户 {sub.email} 订阅了平台 {source_platform}，包含在发送列表中"
                        )
                    else:
                        self.logger.debug(
                            f"用户 {sub.email} 未订阅平台 {source_platform}，跳过"
                        )

            subscribers = filtered_subscribers
            self.logger.info(f"筛选后的订阅者数量: {len(subscribers)}")

        # 获取所有订阅者邮箱
        receiver_emails = [sub.email for sub in subscribers]

        # 发送邮件
        success_count = self._send_batch_email(
            subject=subject, content=content, receivers=receiver_emails, is_html=html
        )

        self.logger.info(f"邮件发送完成，成功: {success_count}/{len(subscribers)}")
        return success_count, len(subscribers)

    def send_email_to_subscribers_by_frequency(
        self, subject, content, html=False, source_platform=None, frequency_hours=1
    ):
        """
        根据发送频率向订阅者发送邮件

        Args:
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式内容
            source_platform: 文章来源平台名称
            frequency_hours: 当前发送频率（小时）

        Returns:
            tuple: (成功发送数量, 总订阅者数量)
        """
        # 使用数据库管理器的新方法获取指定频率的订阅者
        subscribers = self.db_manager.get_subscribers_by_frequency(frequency_hours)

        if not subscribers:
            self.logger.info(f"没有频率为{frequency_hours}小时的订阅者")
            return 0, 0

        self.logger.info(
            f"开始筛选频率为{frequency_hours}小时的订阅者，来源平台: {source_platform}"
        )
        self.logger.info(f"该频率订阅者数量: {len(subscribers)}")

        # 如果指定了来源平台，筛选订阅了该平台的用户
        if source_platform:
            platform_id = self.db_manager.get_platform_id_by_name(source_platform)
            if platform_id is None:
                self.logger.warning(f"未找到平台: {source_platform}")
                return 0, 0

            self.logger.info(f"平台 {source_platform} 的ID: {platform_id}")

            filtered_subscribers = []
            for sub in subscribers:
                if sub.all_platforms:
                    filtered_subscribers.append(sub)
                    self.logger.debug(
                        f"用户 {sub.email} 订阅所有平台，包含在发送列表中"
                    )
                else:
                    subscribed_platform_ids = [p.id for p in sub.platforms]
                    if platform_id in subscribed_platform_ids:
                        filtered_subscribers.append(sub)
                        self.logger.debug(
                            f"用户 {sub.email} 订阅了平台 {source_platform}，包含在发送列表中"
                        )
                    else:
                        self.logger.debug(
                            f"用户 {sub.email} 未订阅平台 {source_platform}，跳过"
                        )

            subscribers = filtered_subscribers
            self.logger.info(f"筛选后的订阅者数量: {len(subscribers)}")

        # 获取所有订阅者邮箱
        receiver_emails = [sub.email for sub in subscribers]

        # 发送邮件
        success_count = self._send_batch_email(
            subject=subject, content=content, receivers=receiver_emails, is_html=html
        )

        self.logger.info(
            f"频率{frequency_hours}小时邮件发送完成，成功: {success_count}/{len(subscribers)}"
        )
        return success_count, len(subscribers)

    def send_email_to_subscribers_by_individual_frequency(
        self, subject, content, html=False, source_platform=None
    ):
        """
        根据每个订阅者的个人推送频率发送邮件

        Args:
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式内容
            source_platform: 文章来源平台名称

        Returns:
            tuple: (成功发送数量, 总符合条件订阅者数量)
        """
        from datetime import datetime

        # 获取当前应该接收邮件的订阅者
        due_subscribers = self.db_manager.get_subscribers_due_for_email()

        if not due_subscribers:
            self.logger.info("当前没有需要推送的订阅者")
            return 0, 0

        self.logger.info(f"找到 {len(due_subscribers)} 个需要推送的订阅者")

        # 统计首次发送的用户数量（兼容性监控）
        first_time_users = [
            sub for sub in due_subscribers if sub.last_email_sent_time is None
        ]
        if first_time_users:
            self.logger.info(
                f"其中 {len(first_time_users)} 个用户为首次推送（包括版本升级前的老用户）"
            )

        # 如果指定了来源平台，筛选订阅了该平台的用户
        if source_platform:
            platform_id = self.db_manager.get_platform_id_by_name(source_platform)
            if platform_id is None:
                self.logger.warning(f"未找到平台: {source_platform}")
                return 0, 0

            self.logger.info(f"平台 {source_platform} 的ID: {platform_id}")

            filtered_subscribers = []
            for sub in due_subscribers:
                if sub.all_platforms:
                    filtered_subscribers.append(sub)
                    self.logger.debug(
                        f"用户 {sub.email} 订阅所有平台，包含在发送列表中"
                    )
                else:
                    subscribed_platform_ids = [p.id for p in sub.platforms]
                    if platform_id in subscribed_platform_ids:
                        filtered_subscribers.append(sub)
                        self.logger.debug(
                            f"用户 {sub.email} 订阅了平台 {source_platform}，包含在发送列表中"
                        )
                    else:
                        self.logger.debug(
                            f"用户 {sub.email} 未订阅平台 {source_platform}，跳过"
                        )

            due_subscribers = filtered_subscribers
            self.logger.info(f"筛选后的订阅者数量: {len(due_subscribers)}")

        if not due_subscribers:
            self.logger.info("筛选后没有需要推送的订阅者")
            return 0, 0

        # 按用户逐个发送邮件（确保每个用户的发送时间都能正确记录）
        success_count = 0
        current_time = datetime.now()

        for subscriber in due_subscribers:
            try:
                # 记录是否为首次发送（用于日志）
                is_first_time = subscriber.last_email_sent_time is None

                # 为单个用户发送邮件
                individual_success = self._send_batch_email(
                    subject=subject,
                    content=content,
                    receivers=[subscriber.email],
                    is_html=html,
                )

                if individual_success > 0:
                    # 发送成功，更新该用户的最后发送时间
                    self.db_manager.update_last_email_sent_time(
                        subscriber.id, current_time
                    )
                    success_count += 1

                    if is_first_time:
                        self.logger.info(
                            f"成功发送邮件给 {subscriber.email}（首次推送），推送频率: {subscriber.send_frequency}小时"
                        )
                    else:
                        self.logger.info(
                            f"成功发送邮件给 {subscriber.email}，推送频率: {subscriber.send_frequency}小时"
                        )
                else:
                    self.logger.warning(f"发送邮件给 {subscriber.email} 失败")

            except Exception as e:
                self.logger.error(f"发送邮件给 {subscriber.email} 时出错: {str(e)}")

        self.logger.info(
            f"个性化频率邮件发送完成，成功: {success_count}/{len(due_subscribers)}"
        )
        return success_count, len(due_subscribers)

    def get_stats(self):
        """获取统计数据"""
        return self.db_manager.get_stats()

    def _is_valid_email(self, email):
        """检查邮箱格式是否有效"""
        # 简单的邮箱格式验证
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return bool(pattern.match(email))

    def _match_mask(self, email):
        """检查邮箱是否符合订阅掩码规则"""
        return bool(self.subscriber_pattern.match(email))

    def _send_batch_email(self, subject, content, receivers, is_html=False):
        """
        批量发送邮件

        Args:
            subject: 邮件主题
            content: 邮件内容
            receivers: 接收者邮箱列表
            is_html: 是否为HTML内容

        Returns:
            int: 成功发送的数量
        """
        if not receivers:
            return 0

        try:
            # 创建邮件
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = ";".join(receivers)
            message["Subject"] = Header(subject, "utf-8")

            # 邮件正文
            content_type = "html" if is_html else "plain"
            message.attach(MIMEText(content, content_type, "utf-8"))

            # 连接SMTP服务器
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)

            # 发送邮件
            server.sendmail(self.sender_email, receivers, message.as_string())
            self.logger.info(f"邮件已发送给{len(receivers)}位订阅者")

            # 更新邮件发送统计
            if receivers and len(receivers) > 0:
                self.db_manager.increment_emails_sent(len(receivers))
                self.logger.info(f"邮件统计已更新，增加 {len(receivers)} 封")

            # 关闭连接
            server.quit()
            return len(receivers)

        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            return 0
