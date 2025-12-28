package main

import (
	"fmt"
	"log"
	"secure_utils"
)

func main() {
	fmt.Println("=== Secure Utils 组件功能验证工具 ===")

	// 1. 加载 API Key
	apiKey, err := secure_utils.LoadAPIKey()
	if err != nil {
		log.Fatalf("无法加载 API Key: %v\n请确保已运行 setup 脚本或配置了 apiKey.yaml", err)
	}
	fmt.Println(" [x] API Key 加载成功")

	// 2. 初始化 DeepSeek 客户端
	client, err := secure_utils.NewDeepSeekClient(apiKey)
	if err != nil {
		log.Fatalf("无法初始化客户端: %v", err)
	}
	fmt.Println(" [x] DeepSeek 客户端初始化成功")
	fmt.Println("-------------------------------------------")

	// 3. 测试 Smart DLP
	fmt.Println("\n>>> 测试 1: Smart DLP (智能脱敏)")
	dlp := secure_utils.NewSmartDLP(client)

	sensitiveText := "用户张三，身份证号 110101199003071234，住在北京市朝阳区，手机号 13800001234，AWS Key: AKIAIOSFODNN7EXAMPLE。"
	fmt.Printf("原文: %s\n", sensitiveText)
	fmt.Println("正在处理...")

	maskedText, err := dlp.MaskSensitiveData(sensitiveText)
	if err != nil {
		fmt.Printf("ERROR: DLP 处理失败: %v\n", err)
	} else {
		fmt.Printf("脱敏结果: %s\n", maskedText)
	}
	fmt.Println("-------------------------------------------")

	// 4. 测试 DB Firewall
	fmt.Println("\n>>> 测试 2: DB Firewall (数据库防火墙)")
	firewall := secure_utils.NewDBFirewall(client)

	sqlCases := []string{
		"SELECT * FROM products WHERE id = 101",
		"SELECT * FROM users WHERE id = 1 OR 1=1; --",
		"DROP TABLE users;",
	}

	for _, sql := range sqlCases {
		fmt.Printf("分析 SQL: %s\n", sql)
		isSafe, reason, err := firewall.DetectIntrusion(sql)
		if err != nil {
			fmt.Printf("ERROR: 防火墙检查失败: %v\n", err)
		} else {
			status := "安全"
			if !isSafe {
				status = "拦截 (不安全)"
			}
			fmt.Printf("结论: [%s] 原因: %s\n", status, reason)
		}
		fmt.Println("-")
	}
	fmt.Println("-------------------------------------------")

	// 5. 测试 Content Summarizer
	fmt.Println("\n>>> 测试 3: Content Summarizer (内容摘要)")
	summarizer := secure_utils.NewContentSummarizer(client)

	longContent := `通常，大型语言模型（LLM）的训练分为两个阶段：预训练和后训练。
预训练阶段使用海量互联网文本数据，让模型学习语言规律和世界知识。
后训练阶段（Post-training）则侧重于让模型更好地遵循指令、符合人类价值观。
在后训练中，强化学习（RL）发挥着重要作用。
最近，OpenAI 的 o1 模型展示了在推理时的强化学习（Test-Time Compute）也能显著提升模型解决复杂数学和编程问题的能力。
这一发现为 AI 的发展开辟了新的方向，即不仅仅在训练时优化，也可以在推理时通过思考链（CoT）进行搜索和自我博弈。`

	fmt.Println("原文片段: 通常，大型语言模型（LLM）的训练分为两个阶段...")
	fmt.Println("正在生成摘要...")

	summary, err := summarizer.GenerateSummary(longContent)
	if err != nil {
		fmt.Printf("ERROR: 摘要生成失败: %v\n", err)
	} else {
		fmt.Printf("生成的标题: %s\n", summary.Title)
		fmt.Printf("生成的摘要: %s\n", summary.Summary)
	}

	fmt.Println("\n=== 验证结束 ===")
}
