"""
访问统计模块

处理点击数和下载数的统计功能
"""

import re
import logging
import requests
from .utils import http_get
from .database import CustomError
from .config import BASE_URL


def is_all_digits(s):
    """检查字符串是否全为数字"""
    if not bool(re.fullmatch(r"\d+", s)):
        raise CustomError("'点击数'格式错误")
    return True


def get_click_count(data_str):
    """获取文章点击数

    Args:
        data_str: 包含点击数参数的字符串，格式为 '("wbnews", 1728834619, 45421)'

    Returns:
        int: 点击数
    """
    try:
        count_params = data_str.strip("()").split(", ")
        owner = count_params[1]
        clickid = count_params[2]

        url = f"{BASE_URL}/system/resource/code/news/click/dynclicks.jsp?clickid={clickid}&owner={owner}&clicktype=wbnews"

        response = http_get(url)
        if not response:
            return 0

        resp_text = response.text
        logging.info(f"点击数：{resp_text}")

        # 校验格式
        is_all_digits(resp_text)

        num = int(resp_text)
        # 点击数减1，因为统计包含了爬虫的访问
        if num > 1:
            num -= 1

        return num
    except (IndexError, ValueError) as e:
        logging.error(f"解析点击数失败: {str(e)}")
        raise CustomError("解析点击数参数错误")


def get_download_count(data_str):
    """获取附件下载数

    Args:
        data_str: 包含下载数参数的字符串，格式为 '(6582534,1728834619,"wbnewsfile","attach")'

    Returns:
        int: 下载数
    """
    try:
        count_params = data_str.strip("()").split(",")
        wbnewsid = count_params[0]
        owner = count_params[1]

        url = f"{BASE_URL}/system/resource/code/news/click/clicktimes.jsp?wbnewsid={wbnewsid}&owner={owner}&type=wbnewsfile&randomid=nattach"

        response = http_get(url)
        if not response:
            return 0

        json_data = response.json()
        num = int(json_data["wbshowtimes"])
        logging.info(f"下载数：{num}")

        return num
    except (IndexError, ValueError, KeyError) as e:
        logging.error(f"解析下载数失败: {str(e)}")
        raise CustomError("解析下载数参数错误")
