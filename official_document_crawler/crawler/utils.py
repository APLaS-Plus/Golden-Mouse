"""
工具模块

提供通用的工具函数
"""

import os
import time
import requests
import logging
from .config import HEADERS, PAYLOAD, MAX_RETRIES, REQUEST_TIMEOUT


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def http_get(url, retry=MAX_RETRIES, timeout=REQUEST_TIMEOUT):
    """
    发送HTTP GET请求并处理重试逻辑

    Args:
        url: 请求的URL
        retry: 重试次数
        timeout: 请求超时时间

    Returns:
        响应文本，失败返回None
    """
    for i in range(1, retry + 1):
        try:
            response = requests.get(
                url=url, headers=HEADERS, data=PAYLOAD, proxies=None, timeout=timeout
            )
            response.raise_for_status()  # 检查HTTP错误
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败 ({i}/{retry}): {url} - {str(e)}")
            if i == retry:
                logging.error(f"请求彻底失败: {url}")
                return None
            time.sleep(3)  # 重试前等待


def sleep_with_progress(seconds):
    """带进度的休眠"""
    for i in range(seconds):
        time.sleep(1)
        if (i + 1) % 5 == 0:
            logging.info(f"休眠中... {i+1}/{seconds}秒")
