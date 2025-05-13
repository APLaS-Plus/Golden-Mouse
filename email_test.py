"""
邮件测试脚本

用于测试订阅确认和文章更新的邮件模板效果
可以模拟发送各种类型的邮件到指定邮箱
"""

import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import sys
import time
from datetime import datetime

# 导入配置
from email_subscriber.config import SMTP_SERVER, SMTP_PASSWORD, MY_EMAIL


def send_email(receiver_email, subject, content, is_html=True):
    """发送单封邮件"""
    print(f"📧 正在发送邮件到: {receiver_email}")

    try:
        # 创建邮件
        message = MIMEMultipart()
        message["From"] = MY_EMAIL
        message["To"] = receiver_email
        message["Subject"] = Header(subject, "utf-8")

        # 邮件正文
        content_type = "html" if is_html else "plain"
        message.attach(MIMEText(content, content_type, "utf-8"))

        # 连接SMTP服务器
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.starttls()
        server.login(MY_EMAIL, SMTP_PASSWORD)

        # 发送邮件
        server.sendmail(MY_EMAIL, [receiver_email], message.as_string())
        print(f"✅ 邮件已成功发送到: {receiver_email}")

        # 关闭连接
        server.quit()
        return True

    except smtplib.SMTPException as e:
        print(f"❌ 发送邮件失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 发送邮件时遇到未知错误: {str(e)}")
        return False


def generate_subscription_email(email, all_platforms=True, platform_names=None):
    """生成订阅确认邮件内容"""

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
                    <p>🔄 更新频率：每篇新文章发布后自动推送</p>
                </div>
                
                <p>从现在开始，您将收到所有符合您订阅要求的最新公文通通知。</p>
                <p>如需调整订阅设置或取消订阅，请随时访问我们的 <a href="http://localhost:5000/subscribe">订阅管理页面</a>。</p>
            </div>
            <div class="footer">
                <p>© 2023 深圳技术大学GoldenMouse - 让校园信息触手可及 🐭</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_content


def generate_update_email(platform, articles):
    """生成文章更新邮件内容"""

    # 构建邮件主题，使用文章标题组合
    article_titles = [article["title"] for article in articles]
    if len(article_titles) > 3:
        # 如果标题太多，只显示前3个，然后用"等"代替
        email_subject = (
            f"【公文通】{article_titles[0]}、{article_titles[1]}、{article_titles[2]}等"
        )
    else:
        email_subject = f"【公文通】{'、'.join(article_titles)}"

    # 构建HTML邮件内容 - 使用卡片式布局
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
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }}
            .article-card {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 15px;
                margin-bottom: 15px;
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
                margin-top: 20px;
                font-size: 12px;
                color: #888;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>📝 深圳技术大学公文通更新 </h2>
            <p>以下是来自<b>{platform}</b>的最新通知：</p>
        </div>
    """

    for article in articles:
        date_display = article.get("date_display", "2023-11-30 14:30:00")

        html_content += f"""
        <div class="article-card">
            <div class="title">
                <a href="{article.get('url', '#')}" target="_blank">{article.get('title', '无标题')}</a>
            </div>
            <div class="meta">
                <span class="platform">📣 {article.get('source', platform)}</span>
                <span class="date">🕒 {date_display}</span>
            </div>
        </div>
        """

    html_content += """
        <div class="footer">
            <p>感谢您的订阅！如需调整订阅设置，请访问 <a href="http://localhost:5000/subscribe">订阅页面</a>。</p>
            <p>© 2023 深圳技术大学GoldenMouse - 让校园信息触手可及 🐭</p>
        </div>
    </body>
    </html>
    """

    return email_subject, html_content


def main():
    parser = argparse.ArgumentParser(description="测试邮件发送功能")
    parser.add_argument("email", help="接收邮件的邮箱地址")
    parser.add_argument(
        "--type",
        choices=["subscription", "update", "both"],
        default="both",
        help="邮件类型：订阅确认(subscription)、文章更新(update)或两者都发(both)",
    )

    args = parser.parse_args()

    print(f"🚀 开始测试邮件发送到: {args.email}")

    if args.type in ["subscription", "both"]:
        print("\n📩 正在发送订阅确认邮件...")
        # 测试全平台订阅
        content = generate_subscription_email(args.email)
        send_email(args.email, "【公文通】✅ 订阅成功确认", content)

        time.sleep(1)  # 避免发送过快

        # 测试特定平台订阅
        platform_names = ["计划财务部", "人力资源部", "教务部"]
        content = generate_subscription_email(args.email, False, platform_names)
        send_email(args.email, "【公文通】✅ 订阅成功确认(指定平台)", content)

    if args.type in ["update", "both"]:
        print("\n📩 正在发送文章更新邮件...")
        # 测试少量文章更新
        platform = "教务部"
        articles = [
            {
                "title": "关于2023-2024学年第一学期期末考试安排的通知",
                "url": "https://nbw.sztu.edu.cn/info/1028/18642.htm",
                "source": "教务部",
                "date_display": "2023-11-30 10:15",
            },
            {
                "title": "关于做好期末学生评教工作的通知",
                "url": "https://nbw.sztu.edu.cn/info/1028/18641.htm",
                "source": "教务部",
                "date_display": "2023-11-30 09:30",
            },
        ]
        subject, content = generate_update_email(platform, articles)
        send_email(args.email, subject, content)

        time.sleep(1)  # 避免发送过快

        # 测试多篇文章更新
        platform = "学生部"
        articles = [
            {
                "title": "关于开展2023年冬季学生心理健康调研的通知",
                "url": "https://nbw.sztu.edu.cn/info/1028/18638.htm",
                "source": "学生部",
                "date_display": "2023-11-29 16:45",
            },
            {
                "title": "关于开展学生资助政策宣传月活动的通知",
                "url": "https://nbw.sztu.edu.cn/info/1028/18637.htm",
                "source": "学生部",
                "date_display": "2023-11-29 15:30",
            },
            {
                "title": "关于评选2023年度优秀学生干部的通知",
                "url": "https://nbw.sztu.edu.cn/info/1028/18636.htm",
                "source": "学生部",
                "date_display": "2023-11-29 14:20",
            },
            {
                "title": "关于做好2023年寒假前后学生工作的通知",
                "url": "https://nbw.sztu.edu.cn/info/1028/18635.htm",
                "source": "学生部",
                "date_display": "2023-11-29 11:10",
            },
        ]
        subject, content = generate_update_email(platform, articles)
        send_email(args.email, subject, content)

    print("\n✅ 测试完成！请检查您的邮箱。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)
