package secure_utils

import (
	"encoding/json"
	"fmt"
	"strings"
)

// DBFirewall 智能数据库防火墙
type DBFirewall struct {
	client *DeepSeekClient
}

// NewDBFirewall 创建新的 DBFirewall 实例
func NewDBFirewall(client *DeepSeekClient) *DBFirewall {
	return &DBFirewall{client: client}
}

// AnalysisResult 模型分析结果结构体
type AnalysisResult struct {
	IsSafe    bool   `json:"is_safe"`
	RiskLevel string `json:"risk_level"`
	Reason    string `json:"reason"`
}

// DetectIntrusion 检测 SQL 语句是否包含恶意注入意图
// 返回: (isSafe bool, reason string, err error)
func (fw *DBFirewall) DetectIntrusion(sqlQuery string) (bool, string, error) {
	prompt := fmt.Sprintf(`作为智能数据库防火墙，请分析以下 SQL 语句是否存在 SQL 注入攻击、恶意删除/修改数据、权限绕过或其他安全风险。

待分析 SQL：
%s

请严格按以下 JSON 格式返回分析结果（不要使用 Markdown 格式，只返回 JSON）：
{
    "is_safe": true/false,
    "risk_level": "None" / "Low" / "High",
    "reason": "简短的安全分析结论"
}
`, sqlQuery)

	messages := []Message{
		{Role: "user", Content: prompt},
	}

	result, err := fw.client.ChatCompletion(messages)
	if err != nil {
		return false, "", err
	}

	cleanJson := strings.TrimSpace(result)
	cleanJson = strings.TrimPrefix(cleanJson, "```json")
	cleanJson = strings.TrimPrefix(cleanJson, "```")
	cleanJson = strings.TrimSuffix(cleanJson, "```")
	cleanJson = strings.TrimSpace(cleanJson)

	var analysis AnalysisResult
	if err := json.Unmarshal([]byte(cleanJson), &analysis); err != nil {
		return false, "", fmt.Errorf("解析模型返回结果失败: %v, 原文: %s", err, cleanJson)
	}

	return analysis.IsSafe, analysis.Reason, nil
}
