"""
配置模块

存储爬虫的全局配置参数
"""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).absolute().parent
DATABASE_DIR = (ROOT_DIR.parent.parent / "database").resolve()
if not DATABASE_DIR.exists():
    DATABASE_DIR.mkdir(parents=True)

# 数据库配置
DATABASE_URI = f"sqlite:///{str(DATABASE_DIR)}/articles.sqlite3"

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
