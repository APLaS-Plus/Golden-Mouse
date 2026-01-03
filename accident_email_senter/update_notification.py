"""
系统更新通知邮件发送脚本

用于向所有订阅者发送系统更新通知，说明功能更新和安全升级内容
"""

import argparse
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import sys

# 导入配置和数据库管理器
# 假设 email_subscriber 包在 Python 路径中可用，或者在父目录中
try:
    from email_subscriber.config import SMTP_SERVER, SMTP_PASSWORD, MY_EMAIL
    from email_subscriber.subscriberDB import EmailSubscriberManager
except ImportError:
    # 尝试添加父目录到路径（如果作为脚本直接运行）
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


def generate_update_email():
    """生成更新通知邮件内容"""

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
                color: #007bff;
            }}
            .content {{
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            .section-title {{
                font-weight: bold;
                font-size: 18px;
                color: #333;
                margin-top: 20px;
                margin-bottom: 10px;
                border-left: 4px solid #007bff;
                padding-left: 10px;
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 8px;
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
                <h2>【GM】🚀系统更新</h2>
            </div>
            <div class="content">
                <p>尊敬的用户：</p>
                <p>今天是1月3日，先祝各位用户新年快乐，事业有成。GoldenMouse 公文通系统已完成最新一轮的功能更新与安全升级。</p>
                
                <div class="section-title">✨ 内容体验相关</div>
                <ul>
                    <li><strong>修改了邮件标题显示</strong>：取消了重复显示文章标题，界面更加简洁。</li>
                    <li><strong>添加了AI内容总结功能</strong>：自动总结各个平台的文章内容，并与原文链接一起推送，助您快速获取核心信息。</li>
                    <li><strong>网页添加暗黑模式</strong>：支持由于系统设置或手动切换的暗黑模式，夜间浏览更舒适。</li>
                </ul>
                
                <div class="section-title">🛡️ 安全相关</div>
                <ul>
                    <li><strong>更新了网页部分数据库防注入功能</strong>：进一步增强系统安全性，保护数据安全。</li>
                    <li><strong>更新了收录文章敏感信息隐蔽功能</strong>：优化了敏感信息处理机制。</li>
                </ul>
                
                <p>感谢您一直以来的支持！我们将持续改进，为您提供更好的校园信息服务。</p>
            </div>
            <div class="footer">
                <p>© 2023 深圳技术大学GoldenMouse - 让校园信息触手可及 🐭</p>
                <p><a href="http://10.108.2.217:5000/subscribe" style="color: #007bff; text-decoration: none;">管理我的订阅</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_content


def send_to_all_subscribers(confirm=False):
    """向所有订阅者发送更新通知邮件"""
    db_manager = EmailSubscriberManager()
    subscribers = db_manager.get_all_subscribers()

    if not subscribers:
        print("❌ 数据库中没有订阅者!")
        return

    total = len(subscribers)
    print(f"📊 总共找到 {total} 个订阅者")

    if not confirm:
        response = input(f"确认发送更新通知邮件给全部 {total} 位订阅者? (y/n): ")
        if response.lower() != "y":
            print("⚠️ 操作已取消")
            return

    content = generate_update_email()
    subject = "【更新通知】GoldenMouse 功能更新与安全升级"

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
    parser = argparse.ArgumentParser(description="发送更新通知邮件给所有订阅者")
    parser.add_argument(
        "--force", "-f", action="store_true", help="直接发送邮件而不确认"
    )
    parser.add_argument(
        "--single", "-s", type=str, help="向单个邮箱地址发送测试邮件，而不是所有订阅者"
    )

    args = parser.parse_args()

    if args.single:
        print(f"🚀 开始发送测试更新通知邮件到: {args.single}")
        content = generate_update_email()
        subject = "【测试】GoldenMouse 功能更新与安全升级"
        send_email(args.single, subject, content)
        print("\n✅ 测试邮件发送完成！请检查您的邮箱。")
    else:
        print("🚀 开始向所有订阅者发送更新通知邮件")
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
