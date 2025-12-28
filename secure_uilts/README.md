# Secure Utils (安全组件库)

这是一个基于 Go 语言的安全组件库，旨在提供安全的 API Key 管理和 AI 模型交互能力。本模块采用微服务架构设计思路，未来将支持通过 API 接口与 Python 等其他语言交互。

## 目录结构

```


secure_uilts/
├── cmd/
│   ├── secure_setup/       # 初始化工具：加密 API Key 并生成配置文件
│   ├── check_connectivity/ # 连通性测试工具：测试 DeepSeek API 连接
│   └── verify_components/  # 组件验证工具：演示 DLP、防火墙与摘要功能
├── deepseek_client.go      # DeepSeek API 客户端 (兼容 OpenAI 协议)
├── db_firewall.go          # 智能数据库防火墙
├── smart_dlp.go            # 智能数据防泄漏 (Smart DLP)
├── content_summarizer.go   # 内容摘要与推送助手
├── secure_loader.go        # 核心加载器：负责解密 Key 和路径自动定位
├── setup_windows.ps1       # Windows 一键编译/配置脚本
├── setup_linux.sh          # Linux 一键编译/配置脚本
└── go.mod                  # Go 模块定义
```

## 快速开始

### 1. 环境初始化

在首次使用前，请确保 `apiKey.yaml` 中包含 `origin_api_key`。然后运行初始化脚本：

- **Windows**: 运行 `.\setup_windows.ps1`
- **Linux**: 运行 `./setup_linux.sh`

脚本会自动：

1.  编译 `secure_setup` 工具。
2.  使用本机硬件指纹加密 API Key。
3.  更新 `apiKey.yaml` 并清除原始明文 Key (如果使用了 `-replace` 参数，脚本默认已启用)。

### 2. 连通性测试

编译并运行连通性检查工具，验证能否成功调用 DeepSeek API：

```powershell
go run cmd/check_connectivity/main.go "你好"
```

### 3. 组件功能验证

运行验证工具以测试所有新组件（DLP、防火墙、摘要器）：

```powershell
go run cmd/verify_components/main.go
```

### 4. 启动微服务 API

建议使用一键启动脚本，它会自动编译并运行服务（默认端口 **58080**）：

- **Windows**: 运行 `.\start_server.ps1`
- **Linux**: 运行 `./start_server.sh`

或者手动运行：

```powershell
go run cmd/api_server/main.go
```

启动后可访问 `http://localhost:58080/health` 进行健康检查，或使用 `test_api.py` 进行集成测试。

### 5. 开发指南

#### 引用库

在您的 Go 代码中引入本模块：

```go
import "secure_utils"

func main() {
    // 1. 自动加载并解密 API Key
    apiKey, err := secure_utils.LoadAPIKey()
    if err != nil {
        log.Fatal(err)
    }

    // 2. 初始化 DeepSeek 客户端
    client, err := secure_utils.NewDeepSeekClient(apiKey)
    if err != nil {
        log.Fatal(err)
    }

    // 3. 使用智能组件

    // --- Smart DLP ---
    dlp := secure_utils.NewSmartDLP(client)
    masked, _ := dlp.MaskSensitiveData("我的身份证是 110101199001011234")
    fmt.Println(masked) // -> "我的身份证是 [MASKED: 身份证号]"

    // --- DB Firewall ---
    fw := secure_utils.NewDBFirewall(client)
    isSafe, reason, _ := fw.DetectIntrusion("DROP TABLE users")
    if !isSafe {
        fmt.Printf("拦截 SQL: %s\n", reason)
    }

    // --- Content Summarizer ---
    summarizer := secure_utils.NewContentSummarizer(client)
    res, _ := summarizer.GenerateSummary("这里是一篇很长的文章...")
    fmt.Printf("标题: %s\n摘要: %s\n", res.Title, res.Summary)
}
```

## 未来规划

- [ ] **API Server**: 构建 HTTP 服务 (`cmd/api_server`)，暴露 API 给 Python 调用。
