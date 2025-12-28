package secure_utils

import (
	"encoding/json"
	"fmt"
	"strings"
)

// ContentSummarizer 内容摘要与推送助手
type ContentSummarizer struct {
	client *DeepSeekClient
}

// SummaryResult 摘要结果
type SummaryResult struct {
	Title   string `json:"title"`
	Summary string `json:"summary"`
}

// NewContentSummarizer 创建新的 ContentSummarizer 实例
func NewContentSummarizer(client *DeepSeekClient) *ContentSummarizer {
	return &ContentSummarizer{client: client}
}

// GenerateSummary 生成标题和精简摘要
func (cs *ContentSummarizer) GenerateSummary(content string) (*SummaryResult, error) {
	prompt := fmt.Sprintf(`请阅读以下内容，并为其生成一个吸引人的标题（不超过20字）和一个精简的摘要（不超过100字），用于推送通知。

内容：
%s

请严格按以下 JSON 格式返回（不要Markdown代码块）：
{
    "title": "...",
    "summary": "..."
}
`, content)

	messages := []Message{
		{Role: "user", Content: prompt},
	}

	result, err := cs.client.ChatCompletion(messages)
	if err != nil {
		return nil, err
	}

	cleanJson := strings.TrimSpace(result)
	cleanJson = strings.TrimPrefix(cleanJson, "```json")
	cleanJson = strings.TrimPrefix(cleanJson, "```")
	cleanJson = strings.TrimSuffix(cleanJson, "```")
	cleanJson = strings.TrimSpace(cleanJson)

	var summary SummaryResult
	if err := json.Unmarshal([]byte(cleanJson), &summary); err != nil {
		return nil, fmt.Errorf("解析模型返回结果失败: %v, 原文: %s", err, cleanJson)
	}

	return &summary, nil
}
