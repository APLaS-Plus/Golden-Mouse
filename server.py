from flask import Flask, jsonify, request
import pathlib
import threading
import time
import schedule
from datetime import datetime, date, timedelta

# 使用新的统一配置
from config import ARTICLES_DATABASE_URI as DATABASE_URI

# 直接引用official_document_crawler中的模块
from official_document_crawler.crawler.database import Base, Article, DatabaseManager
from official_document_crawler.main_crawler import main_crawler

# 导入邮件订阅相关模块
from email_subscriber.subscriber_manager import SubscriberService

ROOT_PATH = pathlib.Path(__file__).parent.resolve()
STATIC_FOLDER = str(ROOT_PATH / "static")

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="")

# 使用DatabaseManager而非直接创建引擎和会话
db_manager = DatabaseManager()
# print(db_manager.url)

# 初始化邮件订阅服务
subscriber_service = SubscriberService()

# 简化的全局变量，只保存已发送的URL集合
last_sent_urls = set()


# 重构邮件发送逻辑，使用个性化推送频率
def send_new_articles_email_by_individual_frequency(new_urls):
    global last_sent_urls

    try:
        # 过滤掉已经发送过的URL
        truly_new_urls = [url for url in new_urls if url not in last_sent_urls]

        if not truly_new_urls:
            print(f"[{datetime.now()}] 📭 没有新文章需要发送")
            return

        print(
            f"[{datetime.now()}] 📧 发现 {len(truly_new_urls)} 条新文章，开始个性化推送"
        )

        # 查询新文章的详细信息
        session = db_manager.get_session()
        new_articles = (
            session.query(Article).filter(Article.url.in_(truly_new_urls)).all()
        )

        if not new_articles:
            print("❌ 没有找到对应的文章详情")
            session.close()
            return

        # 按平台分组文章
        articles_by_platform = {}
        for article in new_articles:
            platform = article.source
            if platform not in articles_by_platform:
                articles_by_platform[platform] = []
            articles_by_platform[platform].append(article)

        # 为每个平台的文章发送个性化推送
        total_sent = 0
        for platform, platform_articles in articles_by_platform.items():
            print(
                f"[{datetime.now()}] 📤 处理平台: {platform}, 文章数: {len(platform_articles)}"
            )

            # 构建邮件主题
            if len(platform_articles) == 1:
                email_subject = f"【公文通】{platform_articles[0].title}"
            else:
                email_subject = (
                    f"【公文通】{platform} - {len(platform_articles)}条新通知"
                )

            # 构建HTML邮件内容
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'PingFang SC', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        background-color: #f5f5f5;
                        color: #333;
                        padding: 20px;
                        max-width: 600px;
                        margin: 0 auto;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 20px;
                        padding-bottom: 15px;
                        border-bottom: 2px solid #007bff;
                    }}
                    .summary {{
                        background-color: #e7f3ff;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                        text-align: center;
                    }}
                    .article-card {{
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        padding: 15px;
                        margin-bottom: 15px;
                        border-left: 4px solid #007bff;
                    }}
                    .title {{
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 8px;
                        color: #003366;
                    }}
                    .title a {{
                        color: #003366;
                        text-decoration: none;
                    }}
                    .title a:hover {{
                        text-decoration: underline;
                    }}
                    .meta {{
                        display: flex;
                        justify-content: space-between;
                        color: #666;
                        font-size: 14px;
                        margin-top: 5px;
                    }}
                    .platform {{
                        font-weight: bold;
                        color: #0055a4;
                    }}
                    .date {{
                        color: #777;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 25px;
                        font-size: 12px;
                        color: #888;
                        padding-top: 15px;
                        border-top: 1px solid #eee;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>📝 深圳技术大学公文通更新</h2>
                </div>
                <div class="summary">
                    <h3>📊 本次推送汇总</h3>
                    <p><strong>{platform}</strong> 平台有 <strong>{len(platform_articles)}</strong> 条新通知</p>
                    <p>推送模式：个性化频率推送</p>
                </div>
            """

            for i, article in enumerate(platform_articles, 1):
                date_display = (
                    f"{article.date} {article.detail_time}"
                    if article.detail_time
                    else article.date
                )

                html_content += f"""
                <div class="article-card">
                    <div class="title">
                        <span style="color: #999; font-size: 14px;">#{i}</span>
                        <a href="{article.url}" target="_blank">{article.title}</a>
                    </div>
                    <div class="meta">
                        <span class="platform">📣 {article.source}</span>
                        <span class="date">🕒 {date_display}</span>
                    </div>
                </div>
                """

            html_content += f"""
                <div class="footer">
                    <p>您的邮件根据个人设置的推送频率发送</p>
                    <p>感谢您的订阅！如需调整订阅设置，请访问 <a href="http://localhost:5000/subscribe">订阅页面</a>。</p>
                    <p>© 2023 深圳技术大学GoldenMouse - 让校园信息触手可及 🐭</p>
                </div>
            </body>
            </html>
            """

            # 使用新的个性化推送方法
            success, total = (
                subscriber_service.send_email_to_subscribers_by_individual_frequency(
                    subject=email_subject,
                    content=html_content,
                    html=True,
                    source_platform=platform,
                )
            )

            total_sent += total
            if total > 0:
                print(
                    f"[{datetime.now()}] ✅ 发送 {platform} 平台邮件完成（个性化推送），成功: {success}/{total}"
                )

        # 更新已发送URL集合
        last_sent_urls.update(truly_new_urls)
        # 限制集合大小，避免内存无限增长
        if len(last_sent_urls) > 200:
            last_sent_urls = set(list(last_sent_urls)[-200:])

        session.close()

    except Exception as e:
        print(f"[{datetime.now()}] ❌ 发送新文章邮件失败: {str(e)}")


# 定时任务线程函数
def run_scheduler():
    # 创建定时任务，每小时执行一次
    schedule.every(0.5).hours.do(crawl_task)

    # 服务启动时先执行一次爬取
    print("🚀 服务启动，执行首次爬取...")
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
        print(f"❌ 获取平台列表错误: {str(e)}")
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
        print(f"❌ 获取订阅平台错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


# 邮箱订阅相关API
@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        all_platforms = data.get("all_platforms", True)
        platform_ids = data.get("platform_ids", [])
        send_frequency = data.get("send_frequency", 24)

        print(
            f"📝 收到订阅请求: email={email}, all_platforms={all_platforms}, platform_ids={platform_ids}, send_frequency={send_frequency}"
        )

        if not email:
            return jsonify({"success": False, "message": "邮箱不能为空"}), 400

        # 验证发送频率
        try:
            send_frequency = int(send_frequency)
            if not (1 <= send_frequency <= 24):
                return (
                    jsonify(
                        {"success": False, "message": "发送频率必须在1-24小时之间"}
                    ),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "发送频率格式无效"}), 400

        # 转换平台ID为整数
        if platform_ids and isinstance(platform_ids, list):
            try:
                platform_ids = [int(pid) for pid in platform_ids]
                print(f"转换后的平台ID: {platform_ids}")
            except (ValueError, TypeError) as e:
                print(f"❌ 平台ID转换错误: {str(e)}")
                platform_ids = []

        # 如果没有选择任何平台但选择了"选择特定平台"，返回错误
        if not all_platforms and not platform_ids:
            print("⚠️ 未选择任何平台，但设置了非全部平台订阅")
            return jsonify({"success": False, "message": "请至少选择一个平台"}), 400

        success, message, is_new_subscriber = subscriber_service.add_subscriber(
            email, platform_ids, all_platforms, send_frequency
        )

        if success:
            # 获取平台名称列表（用于发送订阅确认邮件）
            platform_names = []
            if not all_platforms and platform_ids:
                # 查询平台名称
                platform_objects = []
                db_session = subscriber_service.db_manager.get_session()
                try:
                    from email_subscriber.subscriberDB import Platform

                    platform_objects = (
                        db_session.query(Platform)
                        .filter(Platform.id.in_(platform_ids))
                        .all()
                    )
                    platform_names = [p.name for p in platform_objects]
                except Exception as e:
                    print(f"❌ 获取平台名称失败: {str(e)}")
                finally:
                    db_session.close()

            # 只有新订阅者才发送确认邮件
            if is_new_subscriber:
                send_subscription_confirmation(
                    email, all_platforms, platform_names, send_frequency
                )
                print(f"✅ 新用户 {email} 订阅成功")
            else:
                print(f"✅ 用户 {email} 更新订阅设置成功")

        return jsonify({"success": success, "message": message})

    except Exception as e:
        print(f"❌ 订阅处理错误: {str(e)}")
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
        print(f"❌ 退订处理错误: {str(e)}")
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

        print(f"📊 查询到 {len(articles)} 篇文章")
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
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/get_today_data")
def get_today_data():
    try:
        # 获取今天的日期
        today = date.today().strftime("%Y-%m-%d")
        print(f"📅 当前日期: {today}, 正在查询此日期的文章")

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
        print(f"🗓️ 数据库中的所有日期: {all_dates}")

        # 如果没有找到文章，尝试查找最近的文章
        if not articles:
            print(f"⚠️ 未找到今日({today})文章，尝试查找最新文章")
            articles = (
                session.query(Article)
                .order_by(Article.date.desc(), Article.detail_time.desc())
                .limit(10)
                .all()
            )
            if articles:
                latest_date = articles[0].date
                print(f"📝 使用最新日期: {latest_date} 的文章")
                articles = (
                    session.query(Article)
                    .filter(Article.date == latest_date)
                    .order_by(Article.detail_time.desc())
                    .all()
                )

        print(f"📄 查询到 {len(articles)} 篇今日文章")
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
        print(f"❌ Error: {str(e)}")
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


# 新增API - 获取统计数据
@app.route("/api/get_stats", methods=["GET"])
def get_stats():
    try:
        stats = subscriber_service.get_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        print(f"❌ 获取统计数据错误: {str(e)}")
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


# 发送订阅成功确认邮件
def send_subscription_confirmation(
    email, all_platforms, platform_names=None, send_frequency=1
):
    try:
        # 确定订阅的平台类型描述
        if all_platforms:
            platform_description = "全部平台"
        else:
            platform_description = (
                f"以下平台：{', '.join(platform_names)}"
                if platform_names
                else "您选择的平台"
            )

        # 构建HTML邮件内容
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'PingFang SC', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    background-color: #f5f5f5;
                    color: #333;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 25px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eee;
                }}
                .content {{
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                .highlight {{
                    background-color: #f0f7ff;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #888;
                    padding-top: 15px;
                    border-top: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎉 订阅成功 🎉</h2>
                </div>
                <div class="content">
                    <p>您好！</p>
                    <p>感谢您订阅深圳技术大学公文通更新通知。您已成功订阅来自<b>{platform_description}</b>的最新公告。</p>
                    
                    <div class="highlight">
                        <p>📧 订阅邮箱：{email}</p>
                        <p>🔄 推送频率：每{send_frequency}小时推送一次</p>
                    </div>
                    
                    <p>从现在开始，您将按照设定的频率收到所有符合您订阅要求的最新公文通通知。</p>
                    <p>如需调整订阅设置或取消订阅，请随时访问我们的 <a href="http://localhost:5000/subscribe">订阅管理页面</a>。</p>
                </div>
                <div class="footer">
                    <p>© 2023 深圳技术大学GoldenMouse - 让校园信息触手可及 🐭</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 发送确认邮件
        subscriber_service._send_batch_email(
            subject="【公文通】✅ 订阅成功确认",
            content=html_content,
            receivers=[email],
            is_html=True,
        )
        print(f"[{datetime.now()}] ✅ 订阅确认邮件已发送至: {email}")
        return True

    except Exception as e:
        print(f"[{datetime.now()}] ❌ 发送订阅确认邮件失败: {str(e)}")
        return False


# 更新爬虫任务函数，使用新的推送方法
def crawl_task():
    print(f"[{datetime.now()}] ⏰ 开始执行定时爬取任务...")
    try:
        new_urls = main_crawler(start_page=0, end_page=2, mode="all")
        print(
            f"[{datetime.now()}] ✅ 爬取完成，发现 {len(new_urls) if new_urls else 0} 条新内容"
        )
        # 如果有新内容，使用个性化推送
        if new_urls and len(new_urls) > 0:
            send_new_articles_email_by_individual_frequency(new_urls)
        return new_urls
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 爬取任务执行失败: {str(e)}")
        return []


# 保留旧的函数名以保持兼容性
def send_new_articles_email_by_frequency(new_urls):
    """兼容性函数，调用新的个性化推送函数"""
    send_new_articles_email_by_individual_frequency(new_urls)


def send_new_articles_email(new_urls):
    """兼容性函数，调用新的个性化推送函数"""
    send_new_articles_email_by_individual_frequency(new_urls)


def main():
    """主函数，用于 uv run 命令调用"""
    # 启动时显示兼容性信息
    print("🔄 检查数据库兼容性...")

    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("🕒 定时爬取任务已启动，每半小时执行一次")
    print("📧 邮件推送已升级为个性化频率推送，兼容版本升级前的用户")

    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
