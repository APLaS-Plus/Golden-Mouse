"""
道歉声明邮件发送脚本

用于向所有订阅者发送道歉声明，说明数据库问题并请求重新订阅
"""

import argparse
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import sys

# 导入配置和数据库管理器
from email_subscriber.config import SMTP_SERVER, SMTP_PASSWORD, MY_EMAIL
from email_subscriber.subscriberDB import EmailSubscriberManager


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


def generate_apology_email():
    """生成道歉声明邮件内容"""

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
                <h2>⚠️ 系统维护通知 ⚠️</h2>
            </div>
            <div class="content">
                <p>尊敬的用户：</p>
                <p>非常抱歉！很辜负各位的信赖，由于本人经验不足，导致后台数据库处理时发生了问题。</p>
                
                <div class="highlight">
                    <p>我已经紧急进行系统更新，但需要清除一次数据库。</p>
                    <p>恳请您再次访问我们的网站，重新订阅相关平台通知。</p>
                </div>
                
                <p>感谢您的理解与支持，我们将继续改进系统，为您提供更稳定、更优质的服务。</p>
                <p>如需重新订阅，请访问: <a href="http://10.108.2.217:5000/subscribe">订阅管理页面</a></p>
            </div>
            <div class="footer">
                <p>© 2023 深圳技术大学GoldenMouse - 让校园信息触手可及 🐭</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_content


def send_to_all_subscribers(confirm=False):
    """向所有订阅者发送道歉邮件"""
    db_manager = EmailSubscriberManager()
    subscribers = db_manager.get_all_subscribers()

    if not subscribers:
        print("❌ 数据库中没有订阅者!")
        return

    total = len(subscribers)
    print(f"📊 总共找到 {total} 个订阅者")

    if not confirm:
        response = input(f"确认发送道歉邮件给全部 {total} 位订阅者? (y/n): ")
        if response.lower() != "y":
            print("⚠️ 操作已取消")
            return

    content = generate_apology_email()
    subject = "【重要】公文通订阅系统维护通知"

    success = 0
    failure = 0

    for idx, subscriber in enumerate(subscribers, 1):
        print(f"[{idx}/{total}] 正在处理: {subscriber.email}")

        if send_email(subscriber.email, subject, content):
            success += 1
        else:
            failure += 1

        # 避免发送过于频繁被邮件服务器限制
        if idx < total:
            print("等待1秒...")
            time.sleep(1)

    print("\n📈 发送结果统计:")
    print(f"✅ 成功: {success}")
    print(f"❌ 失败: {failure}")
    print(f"📊 总计: {total}")


def main():
    parser = argparse.ArgumentParser(description="发送道歉声明邮件给所有订阅者")
    parser.add_argument(
        "--force", "-f", action="store_true", help="直接发送邮件而不确认"
    )
    parser.add_argument(
        "--single", "-s", type=str, help="向单个邮箱地址发送测试邮件，而不是所有订阅者"
    )

    args = parser.parse_args()

    if args.single:
        print(f"🚀 开始发送测试道歉声明邮件到: {args.single}")
        content = generate_apology_email()
        send_email(args.single, "【重要】公文通订阅系统维护通知", content)
        print("\n✅ 测试邮件发送完成！请检查您的邮箱。")
    else:
        print("🚀 开始向所有订阅者发送道歉声明邮件")
        send_to_all_subscribers(confirm=args.force)
        print("\n✅ 批量邮件发送任务完成！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)
