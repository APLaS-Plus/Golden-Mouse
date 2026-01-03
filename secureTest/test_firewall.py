import yaml
import requests
import sys
import os

# 配置 API 地址
API_URL = "http://localhost:58080/api/v1/firewall/detect"


def load_test_cases(filename):
    """加载 YAML 测试用例"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 无法读取测试用例文件 {filename}: {e}")
        sys.exit(1)


def run_tests(test_cases):
    """执行测试"""
    print(f"🚀 开始执行 SQL 注入防火墙测试，共 {len(test_cases)} 个用例...\n")

    passed_count = 0
    failed_count = 0

    for idx, case in enumerate(test_cases):
        name = case.get("name", f"Case {idx+1}")
        sql_query = case.get("sql")
        should_be_safe = case.get("should_be_safe")

        print(f"🔹 测试用例 [{idx+1}/{len(test_cases)}]: {name}")
        print(f"   Payload: {sql_query}")

        try:
            # 发送请求
            payload = {"sql": sql_query}
            response = requests.post(API_URL, json=payload, timeout=10)

            if response.status_code != 200:
                print(f"   ⚠️  API 请求失败，状态码: {response.status_code}")
                failed_count += 1
                continue

            result = response.json()
            # 兼容 API 返回格式，有些可能直接返回 data，有些可能是 {success: true, data: ...}
            # firewall/detect 返回格式通常为 {code: 200, msg: "success", data: {...}}
            # 或者直接是 firewall.go 中的结构，但经过 secure_api_server 包装

            # 假设直接返回的是 AnalysisResult 或者在 data 字段中
            data = result.get("data", result)
            if "is_safe" not in data:
                # 尝试直接解析
                data = result

            is_safe = data.get("is_safe")
            risk_level = data.get("risk_level", "Unknown")
            reason = data.get("reason", "No reason provided")

            # 验证结果
            if is_safe == should_be_safe:
                print(
                    f"   ✅ [通过] 预期: {'安全' if should_be_safe else '不安全'},以此实际: {'安全' if is_safe else '不安全'} (风险等级: {risk_level})"
                )
                passed_count += 1
            else:
                print(
                    f"   ❌ [失败] 预期: {'安全' if should_be_safe else '不安全'}, 实际: {'安全' if is_safe else '不安全'}"
                )
                print(f"      原因: {reason}")
                failed_count += 1

        except Exception as e:
            print(f"   ⚠️  执行出错: {e}")
            failed_count += 1

        print("-" * 50)

    print(f"\n📊 测试完成")
    print(f"✅ 通过: {passed_count}")
    print(f"❌ 失败: {failed_count}")

    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "test_cases.yaml")

    cases = load_test_cases(yaml_path)
    run_tests(cases)
