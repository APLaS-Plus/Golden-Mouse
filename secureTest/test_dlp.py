import requests
import json
import os

# API 地址
API_URL = "http://localhost:58080/api/v1/dlp/mask"


def run_dlp_test():
    # 模拟包含敏感信息的长文本
    sensitive_text = """
    【绝密】2023年度XX项目核心数据报告

    尊敬的张三（身份证号：110101199003071234，手机号：13800138000），您好！

    根据最新的数据库审计，我们发现服务器（IP: 192.168.1.100）的root密码已被泄露，原密码为：P@ssw0rd123!。
    请立即登录后台 http://admin.system.local 使用管理员账号 admin 进行修改。
    
    另外，客户李四的信用卡信息（卡号：4567 8901 2345 6789，CVV：123，有效期：12/25）也需要重点关注。
    
    API访问密钥：sk-abcdef1234567890abcdef1234567890，请勿泄露给第三方。
    
    家庭住址：北京市朝阳区建国门外大街1号国贸大厦A座1001室。
    
    以上信息请严格保密，阅后即焚。
    """

    print("🚀 开始执行智能 DLP 敏感数据脱敏测试...\n")
    print("📄 原始文本内容：")
    print("-" * 50)
    print(sensitive_text.strip())
    print("-" * 50)

    try:
        # 发送请求
        payload = {"text": sensitive_text}
        response = requests.post(
            API_URL, json=payload, timeout=30
        )  # 模型处理可能较慢，设置长超时

        if response.status_code != 200:
            print(f"❌ API 请求失败，状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return

        result = response.json()
        masked_text = result.get("data", {}).get("masked_text", "")
        # 如果 data 层级不同，尝试直接获取
        if not masked_text and "masked_text" in result:
            masked_text = result["masked_text"]

        print("\n🛡️  脱敏后文本内容：")
        print("-" * 50)
        print(masked_text.strip())
        print("-" * 50)

        print("\n✅ 测试完成，请对比上述两段文本确认脱敏效果。")

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")


if __name__ == "__main__":
    run_dlp_test()
