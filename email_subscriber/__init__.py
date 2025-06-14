"""
邮件订阅模块

提供邮件订阅管理功能
"""

from .subscriber_manager import SubscriberService
from .subscriberDB import EmailSubscriberManager, Platform, EmailSubscriberDB

__all__ = [
    "SubscriberService",
    "EmailSubscriberManager",
    "Platform",
    "EmailSubscriberDB",
]

__version__ = "1.0.0"
