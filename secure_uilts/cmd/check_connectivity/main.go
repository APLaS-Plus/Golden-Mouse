package main

import (
	"fmt"
	"log"

	"os"
	"strings"

	"secure_utils"
)

func main() {
	prompt := "你好，请简单介绍一下你自己"
	if len(os.Args) > 1 {
		prompt = strings.Join(os.Args[1:], " ")
	}

	fmt.Println("正在加载 API Key...")
	apiKey, err := secure_utils.LoadAPIKey()
	if err != nil {
		log.Fatal("无法加载 API Key: ", err)
	}
	fmt.Println("API Key 加载成功 (部分隐藏):", apiKey[:5]+"...")

	client, err := secure_utils.NewDeepSeekClient(apiKey)
	if err != nil {
		log.Fatal("初始化客户端失败: ", err)
	}

	messages := []secure_utils.Message{
		{Role: "user", Content: prompt},
	}

	fmt.Printf("正在发送请求: %s\n", prompt)
	resp, err := client.ChatCompletion(messages)
	if err != nil {
		log.Fatal("请求失败: ", err)
	}

	fmt.Println("--- AI 回复 ---")
	fmt.Println(resp)
	fmt.Println("--- 结束 ---")
}
