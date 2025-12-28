package secure_utils

import (
	"fmt"
	"strings"
)

// SmartDLP 智能数据防泄漏组件
type SmartDLP struct {
	client *DeepSeekClient
}

// NewSmartDLP 创建新的 SmartDLP 实例
func NewSmartDLP(client *DeepSeekClient) *SmartDLP {
	return &SmartDLP{client: client}
}

// MaskSensitiveData 识别并脱敏文本中的敏感数据
// 返回脱敏后的文本
func (dlp *SmartDLP) MaskSensitiveData(text string) (string, error) {
	prompt := fmt.Sprintf(`用户正在提交以下文本，其中可能包含敏感信息（如姓名、身份证号、手机号、API Key、密码、地址等）。
请仔细识别这些敏感信息，并将其替换为 [MASKED: 类型]。保留其他非敏感内容不变。
如果未发现敏感信息，请原样返回文本。
请直接返回处理后的文本，不要包含任何额外的解释或由...包裹。

待处理文本：
%s`, text)

	messages := []Message{
		{Role: "user", Content: prompt},
	}

	result, err := dlp.client.ChatCompletion(messages)
	if err != nil {
		return "", err
	}

	// 清理可能被大模型额外添加的 markdown 代码块标记
	result = strings.TrimPrefix(result, "```")
	result = strings.TrimPrefix(result, "text") // 有时候是 ```text
	result = strings.TrimSuffix(result, "```")
	result = strings.TrimSpace(result)

	return result, nil
}
