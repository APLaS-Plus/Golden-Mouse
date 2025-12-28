package secure_utils

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"
)

// DeepSeekClient DeepSeek API 客户端 (兼容 OpenAI 格式)
type DeepSeekClient struct {
	apiKey string
}

// NewDeepSeekClient 创建一个新的 DeepSeek 客户端
func NewDeepSeekClient(apiKey string) (*DeepSeekClient, error) {
	if apiKey == "" {
		return nil, errors.New("API Key 不能为空")
	}
	// DeepSeek Key 通常以 sk- 开头，但不做强制强校验，以免未来变更
	return &DeepSeekClient{
		apiKey: apiKey,
	}, nil
}

// Message 代表聊天消息
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest API 请求结构
type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
}

// ChatResponse API 响应结构
type ChatResponse struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string      `json:"message"`
		Type    string      `json:"type"`
		Code    interface{} `json:"code"` // Code 可能是 string 或 int
	} `json:"error,omitempty"`
}

// ChatCompletion 发送同步对话请求
func (c *DeepSeekClient) ChatCompletion(messages []Message) (string, error) {
	reqBody := ChatRequest{
		Model:    "deepseek-chat", // DeepSeek V3
		Messages: messages,
	}
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("序列化请求失败: %v", err)
	}

	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("创建请求失败: %v", err)
	}

	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 60 * time.Second} // DeepSeek 可能会有些慢，增加超时
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("请求发送失败: %v", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("API 错误 (Status %d): %s", resp.StatusCode, string(body))
	}

	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		return "", fmt.Errorf("解析响应失败: %v, body: %s", err, string(body))
	}

	if chatResp.Error != nil {
		return "", fmt.Errorf("API 返回错误: %s", chatResp.Error.Message)
	}

	if len(chatResp.Choices) == 0 {
		return "", errors.New("API 未返回任何选项")
	}

	return chatResp.Choices[0].Message.Content, nil
}

// BalanceInfo 余额详情
type BalanceInfo struct {
	Currency        string `json:"currency"`
	TotalBalance    string `json:"total_balance"`
	GrantedBalance  string `json:"granted_balance"`
	ToppedUpBalance string `json:"topped_up_balance"`
}

// BalanceResult 余额查询结果
type BalanceResult struct {
	IsAvailable  bool          `json:"is_available"`
	BalanceInfos []BalanceInfo `json:"balance_infos"`
}

// GetBalance 查询账户余额
func (c *DeepSeekClient) GetBalance() (*BalanceResult, error) {
	req, err := http.NewRequest("GET", "https://api.deepseek.com/user/balance", nil)
	if err != nil {
		return nil, fmt.Errorf("创建请求失败: %v", err)
	}

	req.Header.Add("Accept", "application/json")
	req.Header.Add("Authorization", "Bearer "+c.apiKey)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("请求发送失败: %v", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("API 错误 (Status %d): %s", resp.StatusCode, string(body))
	}

	var balanceResult BalanceResult
	if err := json.Unmarshal(body, &balanceResult); err != nil {
		return nil, fmt.Errorf("解析响应失败: %v, body: %s", err, string(body))
	}

	return &balanceResult, nil
}
