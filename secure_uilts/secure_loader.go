package secure_utils

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/think0rcode/machineid"
	"gopkg.in/yaml.v3"
)

// APIKeyConfig 定义了 yaml 文件的结构
type APIKeyConfig struct {
	EncryptedApiKey string `yaml:"encrypted_api_key"` // 加密后的 API Key
	OriginApiKey    string `yaml:"origin_api_key"`    // 原始 API Key (初始化后可选删除)
}

// GetConfigPath 尝试定位 apiKey.yaml 文件
// 通过基于可执行文件位置的查找，确保无论脚本在哪里运行都能找到配置文件
func GetConfigPath() (string, error) {
	ex, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("无法获取可执行文件路径: %v", err)
	}
	exPath := filepath.Dir(ex)

	// 假设标准结构中，二进制文件在 bin 目录或 secure_utils 根目录
	// 而 apiKey.yaml 可能在当前层或上一层
	// 优先级 1: ../apiKey.yaml (如果构建在 cmd/secure_setup 等子目录下)
	candidates := []string{
		filepath.Join(exPath, "../apiKey.yaml"),
		filepath.Join(exPath, "apiKey.yaml"),
		filepath.Join(exPath, "../../apiKey.yaml"),    // 如果目录结构更深
		filepath.Join(exPath, "../../../apiKey.yaml"), // 如果构建在 dist/ 下且项目结构较深
	}

	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}

	// 如果基于可执行文件的路径都找不到（常见于 go run 模式），尝试基于当前工作目录
	wd, err := os.Getwd()
	if err == nil {
		wdCandidates := []string{
			filepath.Join(wd, "apiKey.yaml"),
			filepath.Join(wd, "../apiKey.yaml"),
			filepath.Join(wd, "../../apiKey.yaml"),
		}
		for _, p := range wdCandidates {
			if _, err := os.Stat(p); err == nil {
				return p, nil
			}
		}
	}

	return "", fmt.Errorf("在候选路径中未找到 apiKey.yaml (Executable: %v, CWD: %v)", candidates, wd)
}

// LoadAPIKey 加载配置，解密 Key 并返回
func LoadAPIKey() (string, error) {
	configPath, err := GetConfigPath()
	if err != nil {
		return "", err
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return "", fmt.Errorf("读取配置文件失败: %v", err)
	}

	var config APIKeyConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return "", fmt.Errorf("解析 yaml 失败: %v", err)
	}

	if config.EncryptedApiKey == "" {
		return "", fmt.Errorf("配置文件中 encrypted_api_key 为空")
	}

	machineID, err := machineid.ID()
	if err != nil {
		return "", fmt.Errorf("获取机器码失败: %v", err)
	}

	return decryptKey(config.EncryptedApiKey, machineID)
}

// EncryptKey 使用机器码作为密钥加密明文
func EncryptKey(plaintext string) (string, error) {
	machineID, err := machineid.ID()
	if err != nil {
		return "", fmt.Errorf("获取机器码失败: %v", err)
	}
	return encryptKeyInternal(plaintext, machineID)
}

// encryptKeyInternal 内部加密函数的实现
func encryptKeyInternal(plaintext string, machineID string) (string, error) {
	if plaintext == "" {
		return "", fmt.Errorf("待加密的明文为空")
	}

	// 1. 准备 Key
	if len(machineID) < 32 {
		// 如果机器码不足32位，进行补位
		padded := fmt.Sprintf("%-32s", machineID)
		machineID = padded
	}
	key := []byte(machineID)[:32] // AES-256 需要 32 字节

	// 2. 准备 Block
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}

	// 3. 创建 Nonce
	nonce := make([]byte, gcm.NonceSize())
	if _, err = io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}

	// 4. 加密
	ciphertext := gcm.Seal(nonce, nonce, []byte(plaintext), nil)

	// 5. 转为 Base64
	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

func decryptKey(encryptedStr string, machineID string) (string, error) {
	if encryptedStr == "" {
		return "", fmt.Errorf("encrypted_api_key 为空")
	}
	// 1. 准备 Key (必须与加密逻辑一致)
	if len(machineID) < 32 {
		padded := fmt.Sprintf("%-32s", machineID)
		machineID = padded
	}
	key := []byte(machineID)[:32]

	ciphertext, err := base64.StdEncoding.DecodeString(encryptedStr)
	if err != nil {
		return "", fmt.Errorf("base64 解码失败: %v", err)
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("创建 cipher 失败: %v", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("创建 gcm 失败: %v", err)
	}

	nonceSize := gcm.NonceSize()
	if len(ciphertext) < nonceSize {
		return "", fmt.Errorf("密文长度不足")
	}
	nonce, actualCiphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]

	// 2. 解密
	plaintext, err := gcm.Open(nil, nonce, actualCiphertext, nil)
	if err != nil {
		return "", fmt.Errorf("gcm 解密失败: %v", err)
	}
	return string(plaintext), nil
}
