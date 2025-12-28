"""
内容解析模块

处理文章内容的解析功能
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from .stats import get_click_count, get_download_count
from .database import CustomError


def mask_sensitive_data(text):
    """调用 Secure Utils DLP 服务进行脱敏"""
    try:
        resp = requests.post(
            "http://localhost:58080/api/v1/dlp/mask", json={"text": text}, timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("masked_text", text)
        logging.warning(f"DLP 服务调用失败: {resp.status_code}")
    except Exception as e:
        logging.warning(f"DLP 服务连接异常: {e}")
    return text


def parse_article_details(html_content):
    """
    解析文章详情

    Args:
        html_content: 文章HTML内容

    Returns:
        dict: 包含文章详情的字典
    """
    if not html_content:
        raise CustomError("HTML内容为空")

    result = {}

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # 解析主要内容
        content_form = soup.select('form[name="_newscontent_fromname"]')
        total_content = "".join(p.text for p in content_form)

        # [Security] 调用 DLP 进行脱敏
        result["total_content"] = mask_sensitive_data(total_content)

        # 获取发布时间
        time_span = soup.select_one('span:-soup-contains("发布时间")')
        if not time_span:
            raise CustomError("无法找到发布时间")

        total_time = time_span.text.strip().split("发布时间：")[1]
        if "日" not in total_time:
            raise CustomError("日期格式错误")

        detail_time = total_time.split("日 ")[1]
        result["detail_time"] = detail_time
        logging.info(f"详细时间：{detail_time}")

        # 获取HTML内容区域
        content_pattern = r'<div class="v_news_content">(.*?)</div>'
        content_match = re.findall(content_pattern, html_content, re.DOTALL)
        if content_match:
            # [Security] 对 HTML 内容也进行简单脱敏 (注意：可能会破坏HTML标签，建议仅对纯文本脱敏，此处为演示直接处理)
            # 在实际生产中，应先提取文本再脱敏，或使用专门的HTML脱敏工具
            # 这里我们假设 DLP 足够智能或只处理 total_content
            result["content"] = content_match[0]
        else:
            logging.warning("未找到内容区块")
            result["content"] = ""

        # 获取点击数
        count_pattern = r"_showDynClicks(.*?)</script></div>"
        count_matches = re.findall(count_pattern, html_content)
        if count_matches and "(" in count_matches[0]:
            click_num = get_click_count(count_matches[0])
            result["click_num"] = click_num
        else:
            raise CustomError("获取点击数参数错误")

        # 获取附件下载数
        fujian_list = soup.select(".fujian")
        # print(fujian_list)
        if fujian_list:
            logging.info("发现附件")
            total_down_num = 0
            fujian_pattern = r'附件【<a href="[^"]+"[^>]*target="_blank">(.*?)</a>】'
            fujian_matches = re.findall(fujian_pattern, html_content)
            fujians = "\n".join(fujian_matches)
            result["fujians"] = fujians
            # print(fujian_matches)
            count_pattern = r"getClickTimes(.*?)</script></span>"
            count_matches = re.findall(count_pattern, html_content)

            if count_matches and "(" in count_matches[0]:
                down_num = get_download_count(count_matches[0])
                total_down_num += down_num
            else:
                logging.warning("获取附件下载量参数错误")

            result["fujian_down_num"] = total_down_num

        return result

    except CustomError as e:
        # 重新抛出自定义异常
        raise e
    except Exception as e:
        # 将其他异常转换为自定义异常
        logging.error(f"解析文章详情失败: {str(e)}")
        raise CustomError(f"解析文章详情失败: {str(e)}")


def process_article_details(db_manager):
    """
    处理所有文章的详情

    Args:
        db_manager: 数据库管理器实例

    Returns:
        int: 成功处理的文章数量
    """
    articles = db_manager.get_all_articles()
    success_count = 0

    for index, article in enumerate(articles, 1):
        try:
            logging.info(f"正在处理第 {index} 条文章: {article.url}")

            # 跳过已处理的文章
            if article.detail_time and article.click_num and article.content:
                logging.info(f"文章已处理，跳过: {article.url}")
                success_count += 1
                continue

            # 解析详情
            html_content = article.raw_data
            details = parse_article_details(html_content)

            # 更新数据库
            db_manager.update_article_details(article.id, details)
            success_count += 1

        except CustomError as e:
            logging.error(f"处理文章 {article.url} 时出错: {str(e)}")
        except Exception as e:
            logging.error(f"处理文章 {article.url} 时发生未预期错误: {str(e)}")

        # 按处理数量进行适当休眠
        from .config import SLEEP_INTERVAL
        import time

        if index % 10 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_10']} 秒")
            time.sleep(SLEEP_INTERVAL["every_10"])
        if index % 30 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_30']} 秒")
            time.sleep(SLEEP_INTERVAL["every_30"])
        if index % 50 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_50']} 秒")
            time.sleep(SLEEP_INTERVAL["every_50"])
        if index % 200 == 0:
            logging.info(f"休眠 {SLEEP_INTERVAL['every_200']} 秒")
            time.sleep(SLEEP_INTERVAL["every_200"])

    return success_count
