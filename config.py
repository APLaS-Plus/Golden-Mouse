"""
项目统一配置文件

包含数据库、爬虫、邮件等相关配置
"""

import os
import re
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.resolve()
DATABASE_DIR = (ROOT_DIR / "database").resolve()

# 确保数据库目录存在
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# ========== 数据库配置 ==========
# 文章数据库
ARTICLES_DATABASE_URI = f"sqlite:///{str(DATABASE_DIR)}/articles.sqlite3"

# 订阅者数据库
SUBSCRIBERS_DATABASE_URI = f"sqlite:///{str(DATABASE_DIR)}/subscribers.sqlite3"

# ========== 爬虫配置 ==========
# 请求头配置
HEADERS = {
    "Referer": "https://nbw.sztu.edu.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
}

# 请求负载
PAYLOAD = {}

# 基础URL
BASE_URL = "https://nbw.sztu.edu.cn"
LIST_URL_TEMPLATE = f"{BASE_URL}/list.jsp?totalpage=492&PAGENUM={{page}}&urltype=tree.TreeTempUrl&wbtreeid=1029"
INFO_URL_PREFIX = f"{BASE_URL}/info/"

# 请求重试次数
MAX_RETRIES = 4

# 请求超时时间（秒）
REQUEST_TIMEOUT = 5

# 休眠时间配置（秒）
SLEEP_INTERVAL = {
    "default": 0.5,
    "every_10": 1,
    "every_30": 2,
    "every_50": 2,
    "every_200": 5,
}

# 禁用代理设置
os.environ["NO_PROXY"] = "*"

# ========== 邮件配置 ==========
SMTP_SERVER = "Your smtp server"
SMTP_PASSWORD = "Your smtp password"
MY_EMAIL = "Sender email address"

if (
    SMTP_SERVER == "Your smtp server"
    or SMTP_PASSWORD == "Your smtp password"
    or MY_EMAIL == "Sender email address"
):
    raise ValueError("Please configure your SMTP settings.")

# 订阅者邮箱格式限制
SUBSCRIBER_MASK = r"^\d+@stumail\.sztu\.edu\.cn$"

# offical ip:host
OFFICAL_URL = "localhost:5000"
