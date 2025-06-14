"""
深圳技术大学公文通爬虫模块

该模块提供了从深圳技术大学公文通系统抓取文章的功能
"""

from .main_crawler import main_crawler
from .crawler.database import DatabaseManager, Article
from .crawler.fetcher import fetch_articles_batch
from .crawler.parser import process_article_details

__all__ = [
    "main_crawler",
    "DatabaseManager",
    "Article",
    "fetch_articles_batch",
    "process_article_details",
]

__version__ = "1.0.0"
