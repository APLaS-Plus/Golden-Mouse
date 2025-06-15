"""
邮件订阅模块配置

从项目根配置文件导入相关配置
"""

import sys
import pathlib

# 添加项目根目录到路径
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from config import (
    DATABASE_DIR,
    SUBSCRIBERS_DATABASE_URI as DB_URL,
    SMTP_SERVER,
    SMTP_PASSWORD,
    MY_EMAIL,
    SUBSCRIBER_MASK,
)

# 保持向后兼容
DB_DIR = DATABASE_DIR
