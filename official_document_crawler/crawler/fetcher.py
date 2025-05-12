"""
URL抓取模块

处理文章URL的抓取功能
"""

import re
import time
import logging
import copy
from .utils import http_get, sleep_with_progress
from .config import LIST_URL_TEMPLATE, INFO_URL_PREFIX, SLEEP_INTERVAL, BASE_URL


def fetch_article_list(page_number):
    """
    抓取指定页面的文章列表

    Args:
        page_number: 页码

    Returns:
        list: 包含文章信息的字典列表，失败返回空列表
    """
    url = LIST_URL_TEMPLATE.format(page=page_number)
    response = http_get(url)

    if not response:
        return []

    html_content = response.text

    # 使用正则表达式提取内容
    types = re.findall(r'target="_self">(.*?)</a></div>', html_content)
    units = re.findall(r'style="font-size: 14px;">(.*?)</a></div>', html_content)
    dates = re.findall(r'style="width:11%;">(.*?)</div>', html_content)
    titles = re.findall(r'.htm" title="(.*?)"  target="_blank" style="', html_content)
    urls = re.findall(r'"><a href="info/(.*?)" title="', html_content)

    # 转换为完整URL
    full_urls = [f"{INFO_URL_PREFIX}{url}" for url in urls]

    # 验证提取的数据长度是否一致
    if len(types) == len(units) == len(dates) == len(titles) == len(full_urls):
        logging.info(f"页面 {page_number} 提取成功，共 {len(types)} 条记录")

        # 将数据整合为文章信息列表
        articles = []
        for i in range(len(types)):
            articles.append(
                {
                    "type": types[i],
                    "source": units[i],
                    "title": titles[i],
                    "date": dates[i],
                    "url": full_urls[i],
                }
            )

        return articles
    else:
        logging.error("数据提取结构错误，各字段长度不一致")
        logging.error(
            f"类型: {len(types)}, 单位: {len(units)}, 日期: {len(dates)}, "
            f"标题: {len(titles)}, URL: {len(full_urls)}"
        )
        return []


def fetch_article_content(url):
    """
    抓取文章内容

    Args:
        url: 文章URL

    Returns:
        str: 文章HTML内容，失败返回None
    """
    response = http_get(url)
    if not response:
        return None

    # 处理编码问题
    try:
        decoded_data = response.text.encode("latin1").decode("utf-8")
        return decoded_data
    except UnicodeError:
        # 如果上面的解码失败，尝试直接使用响应文本
        return response.text


def fetch_articles_batch(start_page, end_page, db_manager):
    """
    批量抓取多个页面的文章

    Args:
        start_page: 起始页码
        end_page: 结束页码
        db_manager: 数据库管理器实例
    """
    new_urls = []
    # 从高到低抓取（通常新文章在前面的页码）
    
    for page in range(end_page, start_page, -1):
        logging.info(f"正在抓取第 {page} 页")

        # 抓取文章列表
        articles = fetch_article_list(page)
        if not articles:
            logging.error(f"页面 {page} 抓取失败")
            success = False
            continue

        # 抓取每篇文章的详细内容
        for article in articles:
            logging.info(f"抓取文章: {article['title']} - {article['url']}")
            raw_data = fetch_article_content(article["url"])

            if raw_data:
                # 添加原始数据
                article["raw_data"] = raw_data

                # 存储到数据库
                new_url = db_manager.add_article(article)
                if new_url:
                    new_urls.append(new_url)
                    logging.info(f"发现新文章: {article['url']}")

                # 短暂休眠避免请求过快
                time.sleep(SLEEP_INTERVAL["default"])
            else:
                logging.error(f"文章内容抓取失败: {article['url']}")

        # 按页码进行适当的休眠
        if page % 10 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_10']} 秒")
            time.sleep(SLEEP_INTERVAL["every_10"])
        if page % 30 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_30']} 秒")
            time.sleep(SLEEP_INTERVAL["every_30"])
        if page % 50 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_50']} 秒")
            time.sleep(SLEEP_INTERVAL["every_50"])

    return new_urls
