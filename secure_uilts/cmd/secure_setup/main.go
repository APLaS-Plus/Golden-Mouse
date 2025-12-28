package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"gopkg.in/yaml.v3"

	"secure_utils"
)

func main() {
	// 解析命令行参数
	replacePtr := flag.Bool("replace", false, "设置为 true 以在加密后从配置文件的 origin_api_key 字段中删除原始 API Key")
	flag.Parse()

	configPath, err := secure_utils.GetConfigPath()
	if err != nil {
		log.Fatal("无法定位 apiKey.yaml: ", err)
	}
	fmt.Println("发现配置文件:", configPath)

	data, err := os.ReadFile(configPath)
	if err != nil {
		log.Fatal("读取配置文件失败: ", err)
	}

	var config secure_utils.APIKeyConfig
	// 简单的 Unmarshal，因为我们有数据
	if err := yaml.Unmarshal(data, &config); err != nil {
		log.Fatal("解析配置失败: ", err)
	}

	// ---------------------------------------------------------
	// 一次性初始化逻辑
	// ---------------------------------------------------------
	if config.OriginApiKey != "" {
		fmt.Println("检测到 'OriginApiKey'，正在生成加密...")

		// 调用库进行加密
		encrypted, err := secure_utils.EncryptKey(config.OriginApiKey)
		if err != nil {
			log.Fatal("加密失败: ", err)
		}

		// 更新配置
		config.EncryptedApiKey = encrypted

		if *replacePtr {
			config.OriginApiKey = ""
			fmt.Println("-replace 参数已设置。正在从配置中移除 'OriginApiKey'。")
		} else {
			fmt.Println("-replace 参数未设置。将在配置中保留 'OriginApiKey'。")
		}

		// 压缩/序列化回 YAML
		newData, err := yaml.Marshal(&config)
		if err != nil {
			log.Fatal("序列化配置失败: ", err)
		}

		// 写回文件
		if err := os.WriteFile(configPath, newData, 0644); err != nil {
			log.Fatal("写入配置文件失败: ", err)
		}

		fmt.Println("成功: 'EncryptedApiKey' 已生成并保存至 apiKey.yaml")
	} else {
		fmt.Println("未找到 'OriginApiKey'，跳过加密生成。")
	}

	// ---------------------------------------------------------
	// 验证 / 正常使用示例
	// ---------------------------------------------------------
	fmt.Println("\n--- 验证 ---")

	decrypted, err := secure_utils.LoadAPIKey()

	if err != nil {
		fmt.Printf("解密/加载失败: %v\n", err)
	} else {
		fmt.Println("解密成功!")
		fmt.Println("还原的 API Key:", decrypted)
	}
}
