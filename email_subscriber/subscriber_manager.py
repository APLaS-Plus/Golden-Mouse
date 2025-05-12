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

from .subscriberDB import EmailSubscriberManager
from .config import SMTP_SERVER, SMTP_PASSWORD, MY_EMAIL, SUBSCRIBER_MASK


class SubscriberService:
    """邮件订阅服务类，提供订阅管理和邮件发送功能"""

    def __init__(self):
        """初始化数据库管理器和日志配置"""
        self.db_manager = EmailSubscriberManager()
        self._setup_logging()
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

    def add_subscriber(self, email):
        """
        添加新的订阅者到数据库

        Args:
            email: 订阅者邮箱

        Returns:
            bool: 添加是否成功
        """
        # 验证邮箱格式
        if not self._is_valid_email(email):
            self.logger.warning(f"邮箱格式无效: {email}")
            return False, "邮箱格式无效"

        # 验证是否符合掩码规则
        if not self._match_mask(email):
            self.logger.warning(f"邮箱不符合订阅规则: {email}")
            return False, "仅接受符合规则的邮箱订阅（如学校邮箱）"

        # 添加到数据库
        result = self.db_manager.add_subscriber(email)
        if result:
            self.logger.info(f"成功添加订阅者: {email}")
            return True, "订阅成功"
        else:
            self.logger.info(f"订阅者已存在: {email}")
            return False, "该邮箱已订阅，请勿重复操作"

    def delete_subscriber(self, email):
        """
        从数据库中删除订阅者

        Args:
            email: 订阅者邮箱

        Returns:
            bool: 删除是否成功
        """
        result = self.db_manager.delete_subscriber(email)
        if result:
            self.logger.info(f"成功删除订阅者: {email}")
            return True, "退订成功"
        else:
            self.logger.warning(f"退订失败，邮箱不存在: {email}")
            return False, "该邮箱未订阅或已退订"

    def send_email_to_all_subscribers(self, subject, content, html=False):
        """
        向所有订阅者发送邮件

        Args:
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式内容

        Returns:
            tuple: (成功发送数量, 总订阅者数量)
        """
        subscribers = self.db_manager.get_all_subscribers()
        if not subscribers:
            self.logger.warning("没有订阅者，邮件发送取消")
            return 0, 0

        # 获取所有订阅者邮箱
        receiver_emails = [sub.email for sub in subscribers]

        # 发送邮件
        success_count = self._send_batch_email(
            subject=subject, content=content, receivers=receiver_emails, is_html=html
        )

        self.logger.info(f"邮件发送完成，成功: {success_count}/{len(subscribers)}")
        return success_count, len(subscribers)

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

            # 关闭连接
            server.quit()
            return len(receivers)

        except smtplib.SMTPException as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            return 0
        except Exception as e:
            self.logger.error(f"发送邮件时遇到未知错误: {str(e)}")
            return 0