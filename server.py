from flask import Flask, jsonify, request
import pathlib
import threading
import time
import schedule
from datetime import datetime, date

# 直接引用official_document_crawler中的模块
from official_document_crawler.crawler.database import Base, Article, DatabaseManager
from official_document_crawler.crawler.config import DATABASE_URI
from official_document_crawler.main_crawler import main_crawler

# 导入邮件订阅相关模块
from email_subscriber.subscriber_manager import SubscriberService

ROOT_PATH = pathlib.Path(__file__).parent.resolve()
STATIC_FOLDER = str(ROOT_PATH / "GoldenMouse")

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="")

# 使用DatabaseManager而非直接创建引擎和会话
db_manager = DatabaseManager()
# print(db_manager.url)

# 初始化邮件订阅服务
subscriber_service = SubscriberService()

# 保存上次发送邮件时的最新文章的URL
last_sent_urls = set()


# 爬虫任务函数
def crawl_task():
    print(f"[{datetime.now()}] 开始执行定时爬取任务...")
    try:
        new_urls = main_crawler(start_page=1, end_page=2, mode="all")
        print(
            f"[{datetime.now()}] 爬取完成，发现 {len(new_urls) if new_urls else 0} 条新内容"
        )
        # 如果有新内容，发送邮件通知订阅用户
        if new_urls and len(new_urls) > 0:
            send_new_articles_email(new_urls)
        return new_urls
    except Exception as e:
        print(f"[{datetime.now()}] 爬取任务执行失败: {str(e)}")
        return []


# 发送新文章邮件
def send_new_articles_email(new_urls):
    global last_sent_urls

    try:
        # 过滤掉已经发送过的URL
        truly_new_urls = [url for url in new_urls if url not in last_sent_urls]

        if not truly_new_urls:
            print(f"[{datetime.now()}] 没有新文章需要发送")
            return

        print(f"[{datetime.now()}] 准备发送 {len(truly_new_urls)} 条新文章到订阅邮箱")

        # 查询新文章的详细信息
        session = db_manager.get_session()
        articles = session.query(Article).filter(Article.url.in_(truly_new_urls)).all()

        if not articles:
            print("没有找到对应的文章详情")
            session.close()
            return

        # 按来源平台分组文章
        articles_by_platform = {}
        for article in articles:
            platform = article.source
            if platform not in articles_by_platform:
                articles_by_platform[platform] = []
            articles_by_platform[platform].append(article)

        # 对每个平台的文章发送邮件
        for platform, platform_articles in articles_by_platform.items():
            # 构建HTML邮件内容
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .article {{ margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }}
                    .title {{ font-size: 18px; font-weight: bold; color: #333; }}
                    .meta {{ font-size: 12px; color: #666; margin: 5px 0; }}
                    .content {{ font-size: 14px; line-height: 1.5; }}
                    .link {{ color: #0066cc; }}
                </style>
            </head>
            <body>
                <h2>深圳技术大学{platform}最新文章</h2>
                <p>以下是最新发布的文章：</p>
            """

            for article in platform_articles:
                html_content += f"""
                <div class="article">
                    <div class="title">{article.title}</div>
                    <div class="meta">
                        <span>来源: {article.source}</span> | 
                        <span>时间: {article.date} {article.detail_time}</span> | 
                        <span>点击量: {article.click_num}</span>
                    </div>
                    <div class="content">{article.content[:200]}...</div>
                    <a class="link" href="{article.url}" target="_blank">阅读全文</a>
                </div>
                """

            html_content += """
                <p>感谢您的订阅！如需调整订阅设置，请访问 <a href="http://localhost:5000/subscribe">订阅页面</a>。</p>
            </body>
            </html>
            """

            # 发送邮件
            success, total = subscriber_service.send_email_to_all_subscribers(
                subject=f"深圳技术大学{platform}文章更新提醒",
                content=html_content,
                html=True,
                source_platform=platform,
            )

            print(
                f"[{datetime.now()}] 发送 {platform} 平台邮件完成，成功: {success}/{total}"
            )

        # 更新已发送URL集合
        last_sent_urls.update(truly_new_urls)
        # 限制集合大小，避免内存无限增长
        if len(last_sent_urls) > 200:
            last_sent_urls = set(list(last_sent_urls)[-200:])

        session.close()

    except Exception as e:
        print(f"[{datetime.now()}] 发送新文章邮件失败: {str(e)}")


# 定时任务线程函数
def run_scheduler():
    # 创建定时任务，每小时执行一次
    schedule.every(0.5).hours.do(crawl_task)

    # 服务启动时先执行一次爬取
    print("服务启动，执行首次爬取...")
    crawl_task()

    while True:
        schedule.run_pending()
        time.sleep(1)


# 新增API - 获取所有平台
@app.route("/api/get_platforms", methods=["GET"])
def get_platforms():
    try:
        platforms = subscriber_service.get_all_platforms()
        return jsonify({"success": True, "platforms": platforms})
    except Exception as e:
        print(f"获取平台列表错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


# 新增API - 获取用户已订阅平台
@app.route("/api/get_subscriber_platforms", methods=["POST"])
def get_subscriber_platforms():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()

        if not email:
            return jsonify({"success": False, "message": "邮箱不能为空"}), 400

        subscription_info = subscriber_service.get_subscriber_platforms(email)
        if subscription_info is None:
            return jsonify({"success": False, "message": "未找到该邮箱的订阅信息"})

        return jsonify({"success": True, "subscription": subscription_info})

    except Exception as e:
        print(f"获取订阅平台错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


# 邮箱订阅相关API
@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        all_platforms = data.get("all_platforms", True)
        platform_ids = data.get("platform_ids", [])

        print(
            f"收到订阅请求: email={email}, all_platforms={all_platforms}, platform_ids={platform_ids}"
        )

        if not email:
            return jsonify({"success": False, "message": "邮箱不能为空"}), 400

        # 转换平台ID为整数
        if platform_ids and isinstance(platform_ids, list):
            try:
                platform_ids = [int(pid) for pid in platform_ids]
                print(f"转换后的平台ID: {platform_ids}")
            except (ValueError, TypeError) as e:
                print(f"平台ID转换错误: {str(e)}")
                platform_ids = []

        # 如果没有选择任何平台但选择了"选择特定平台"，返回错误
        if not all_platforms and not platform_ids:
            print("未选择任何平台，但设置了非全部平台订阅")
            return jsonify({"success": False, "message": "请至少选择一个平台"}), 400

        success, message = subscriber_service.add_subscriber(
            email, platform_ids, all_platforms
        )
        return jsonify({"success": success, "message": message})

    except Exception as e:
        print(f"订阅处理错误: {str(e)}")
        import traceback

        traceback.print_exc()  # 打印完整堆栈信息
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


@app.route("/api/unsubscribe", methods=["POST"])
def unsubscribe():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()

        if not email:
            return jsonify({"success": False, "message": "邮箱不能为空"}), 400

        success, message = subscriber_service.delete_subscriber(email)
        return jsonify({"success": success, "message": message})

    except Exception as e:
        print(f"退订处理错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


@app.route("/api/get_data")
def get_data():
    try:
        # 接收分页参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        # 使用database.py中的会话管理
        session = db_manager.get_session()

        # 查询总数
        total_count = session.query(Article).count()

        # 分页查询文章 - 确保按日期和时间正确排序
        articles = (
            session.query(Article)
            .order_by(Article.date.desc(), Article.detail_time.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )

        print(f"查询到 {len(articles)} 篇文章")
        result = []

        # 转换为字典列表，保持与前端接口兼容
        for article in articles:
            item = {
                "title": article.title,
                "source": article.source,
                "detail_time": (
                    article.date + " " + article.detail_time
                    if article.date and article.detail_time
                    else ""
                ),
                "click_num": article.click_num,
                "url": article.url,
                "fujians": article.fujians,
                "content": article.content,  # 添加内容字段
            }
            result.append(item)

        session.close()

        # 返回带有分页信息的结果
        response_data = {
            "data": result,
            "pagination": {
                "total": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page,
            },
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/get_today_data")
def get_today_data():
    try:
        # 获取今天的日期
        today = date.today().strftime("%Y-%m-%d")
        print(f"当前日期: {today}, 正在查询此日期的文章")

        # 使用database.py中的会话管理
        session = db_manager.get_session()

        # 查询当天的文章（使用更精确的过滤）
        articles = (
            session.query(Article)
            .filter(Article.date == today)
            .order_by(Article.detail_time.desc())
            .all()
        )

        # 打印所有日期以便调试
        all_dates = set(article.date for article in session.query(Article).all())
        print(f"数据库中的所有日期: {all_dates}")

        # 如果没有找到文章，尝试查找最近的文章
        if not articles:
            print(f"未找到今日({today})文章，尝试查找最新文章")
            articles = (
                session.query(Article)
                .order_by(Article.date.desc(), Article.detail_time.desc())
                .limit(10)
                .all()
            )
            if articles:
                latest_date = articles[0].date
                print(f"使用最新日期: {latest_date} 的文章")
                articles = (
                    session.query(Article)
                    .filter(Article.date == latest_date)
                    .order_by(Article.detail_time.desc())
                    .all()
                )

        print(f"查询到 {len(articles)} 篇今日文章")
        result = []

        # 转换为字典列表
        for article in articles:
            item = {
                "title": article.title,
                "source": article.source,
                "detail_time": (
                    article.date + " " + article.detail_time
                    if article.date and article.detail_time
                    else ""
                ),
                "click_num": article.click_num,
                "url": article.url,
                "fujians": article.fujians,
                "content": article.content,
            }
            result.append(item)

        session.close()
        return jsonify({"data": result, "queryDate": today})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return app.send_static_file("today.html")  # 将今日页面作为首页


@app.route("/archive")
def archive():
    return app.send_static_file("index.html")  # 原始表格页面作为归档


@app.route("/subscribe")
def subscribe_page():
    return app.send_static_file("subscribe.html")  # 新增的订阅页面


if __name__ == "__main__":
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("定时爬取任务已启动，每半小时执行一次")

    app.run(debug=True, host="0.0.0.0", port=5000)
