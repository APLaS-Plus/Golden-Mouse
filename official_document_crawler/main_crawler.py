"""
深圳技术大学公文通爬虫主程序

该程序实现了对深圳技术大学公文通系统的文章抓取、解析和存储功能。
"""
import logging
import time

from .crawler.utils import setup_logging
from .crawler.database import DatabaseManager
from .crawler.fetcher import fetch_articles_batch
from .crawler.parser import process_article_details


def main_crawler(start_page=1, end_page=10, mode="all"):
    """主程序入口"""
    # 设置日志
    setup_logging()
    logging.info("深圳技术大学公文通爬虫启动")

    # 初始化数据库
    db_manager = DatabaseManager()
    logging.info("数据库初始化完成")

    new_urls = []  # 初始化新文章URL列表

    try:
        # 根据模式执行不同操作
        if mode in ["fetch", "all"]:
            logging.info(f"开始抓取文章 (页码范围: {start_page} - {end_page})")
            start_time = time.time()
            new_urls = fetch_articles_batch(start_page, end_page, db_manager)
            elapsed = time.time() - start_time
            logging.info(f"耗时: {elapsed:.2f} 秒，获取新文章URLs数量: {len(new_urls)}")

        if mode in ["parse", "all"]:
            logging.info("开始解析文章详情")
            start_time = time.time()
            success_count = process_article_details(db_manager)
            elapsed = time.time() - start_time
            logging.info(
                f"文章详情解析完成，成功处理 {success_count} 篇文章，耗时: {elapsed:.2f} 秒"
            )

        logging.info("爬虫任务完成")

    except KeyboardInterrupt:
        logging.info("用户中断，程序退出")
    except Exception as e:
        logging.error(f"程序执行过程中发生错误: {str(e)}")

    # 返回新文章URL列表，用于推送或其他处理
    return new_urls
