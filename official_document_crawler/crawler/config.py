"""
爬虫模块配置

从项目根配置文件导入相关配置
"""

import sys
import pathlib

# 添加项目根目录到路径
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from config import (
    DATABASE_DIR,
    ARTICLES_DATABASE_URI as DATABASE_URI,
    HEADERS,
    PAYLOAD,
    BASE_URL,
    LIST_URL_TEMPLATE,
    INFO_URL_PREFIX,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    SLEEP_INTERVAL,
)
