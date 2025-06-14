# 🐭 GoldenMouse - 深圳技术大学公文通

> 让校园信息触手可及

一个集成了网页爬虫、邮件订阅和数据展示的深圳技术大学公文通知系统。

## ✨ 功能特色

- 🕷️ **智能爬虫**: 自动爬取深圳技术大学官方公文通知
- 📧 **个性化邮件订阅**: 支持按平台和频率的个性化推送
- 📱 **响应式Web界面**: 今日通知、历史归档、订阅管理
- ⏰ **定时任务**: 自动定时爬取和推送新通知
- 💾 **数据持久化**: SQLite数据库存储文章和订阅信息

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/GoldenMouse.git
cd GoldenMouse
```

### 2. 环境配置

推荐使用 [uv](https://github.com/astral-sh/uv) 作为包管理器：

```bash
# 安装 uv (如果尚未安装)
pip install uv

# 安装项目依赖
uv sync
```

或者使用传统的pip方式：

```bash
pip install -r requirements.txt
```

### 3. 配置邮件服务

编辑 `config.py` 文件，配置您的SMTP邮件服务。将以下配置替换为您的实际邮件服务信息：

```python
# ========== 邮件配置 ==========
SMTP_SERVER = "smtp.your-email-provider.com"  # 您的SMTP服务器
SMTP_PASSWORD = "your_app_password"            # 您的邮箱应用密码
MY_EMAIL = "your-email@example.com"            # 发送邮件的邮箱地址

# 订阅者邮箱格式限制（可根据需要修改）
SUBSCRIBER_MASK = r"^\d+@stumail\.sztu\.edu\.cn$"  # 深圳技术大学学生邮箱格式
```

**常见邮件服务商配置示例：**

- **QQ邮箱**: 
  - SMTP服务器: `smtp.qq.com`
  - 端口: 587 (TLS) 或 465 (SSL)
  - 需要开启SMTP服务并获取授权码

- **163邮箱**:
  - SMTP服务器: `smtp.163.com` 
  - 端口: 587 或 25
  - 需要开启SMTP服务并获取授权码

- **Gmail**:
  - SMTP服务器: `smtp.gmail.com`
  - 端口: 587
  - 需要开启两步验证并使用应用专用密码

### 4. 运行服务

```bash
# 使用 uv 运行 (推荐)
uv run server.py

# 或者直接使用 Python
python server.py
```

服务启动后，访问 http://localhost:5000 即可使用。

## 📖 使用说明

### Web界面

- **首页** (`/`): 查看今日最新公文通知
- **归档页** (`/archive`): 浏览历史公文，支持分页
- **订阅管理** (`/subscribe`): 管理邮件订阅设置

### 邮件订阅功能

1. **订阅设置**:
   - 支持全部平台或选择特定平台订阅
   - 可设置1-24小时的个性化推送频率
   - 实时推送新公文通知

2. **邮件格式**:
   - 精美的HTML邮件模板
   - 按平台分组显示新通知
   - 包含标题、来源、时间和链接

### API接口

```bash
# 获取文章数据
GET /api/get_data?page=1&per_page=10

# 获取今日文章
GET /api/get_today_data

# 邮件订阅
POST /api/subscribe

# 取消订阅  
POST /api/unsubscribe

# 获取平台列表
GET /api/get_platforms

# 获取统计数据
GET /api/get_stats
```

## 🔧 项目结构

```
GoldenMouse/
├── server.py                    # Flask服务器主文件
├── config.py                    # 项目配置文件
├── pyproject.toml               # uv项目配置
├── requirements.txt             # pip依赖列表
├── LICENSE                      # MIT许可证
├── README.md                    # 项目说明文档
├── static/                      # 静态文件目录
│   ├── today.html              # 今日通知页面
│   ├── index.html              # 归档页面
│   └── subscribe.html          # 订阅管理页面
├── database/                    # 数据库文件目录
│   ├── articles.sqlite3        # 文章数据库
│   └── subscribers.sqlite3     # 订阅者数据库
├── official_document_crawler/   # 爬虫模块
│   ├── __init__.py
│   ├── main_crawler.py         # 主爬虫程序
│   └── crawler/                # 爬虫核心模块
│       ├── __init__.py
│       ├── config.py           # 爬虫配置
│       ├── database.py         # 数据库操作
│       ├── fetcher.py          # 数据抓取
│       ├── parser.py           # 内容解析
│       ├── stats.py            # 统计功能
│       └── utils.py            # 工具函数
└── email_subscriber/            # 邮件订阅模块
    ├── subscriber_manager.py   # 订阅管理服务
    ├── subscriberDB.py         # 订阅数据库
    └── config.py               # 邮件配置
```

## ⚙️ 配置说明

### 数据库配置

系统使用SQLite数据库，配置在 `config.py` 中：

```python
# 文章数据库
ARTICLES_DATABASE_URI = f"sqlite:///{str(DATABASE_DIR)}/articles.sqlite3"

# 订阅者数据库  
SUBSCRIBERS_DATABASE_URI = f"sqlite:///{str(DATABASE_DIR)}/subscribers.sqlite3"
```

### 爬虫配置

可在 `config.py` 中调整爬虫参数：

```python
# 请求重试次数
MAX_RETRIES = 4

# 请求超时时间（秒）
REQUEST_TIMEOUT = 5

# 休眠时间配置（秒）
SLEEP_INTERVAL = {
    "default": 0.5,
    "every_10": 1,
    "every_30": 2,
    "every_50": 2, 
    "every_200": 5,
}
```

### 订阅限制

默认只允许深圳技术大学学生邮箱订阅：

```python
# 订阅者邮箱格式限制
SUBSCRIBER_MASK = r"^\d+@stumail\.sztu\.edu\.cn$"
```

## 🔄 定时任务

系统内置定时爬取功能：

- **爬取频率**: 每30分钟执行一次
- **推送逻辑**: 发现新文章时按用户设定频率推送
- **去重机制**: 避免重复推送相同文章

## 👨‍💻 开发者指南

如果您想将此项目适配到自己的学校，需要进行以下修改：

### 1. 修改爬虫配置

编辑 `config.py` 中的爬虫相关配置：

```python
# ========== 爬虫配置 ==========
# 基础URL - 替换为您学校的公文通网址
BASE_URL = "https://your-school-website.edu.cn"

# 列表页URL模板 - 根据您学校的URL格式调整
LIST_URL_TEMPLATE = f"{BASE_URL}/list.jsp?totalpage=XXX&PAGENUM={{page}}&urltype=tree.TreeTempUrl&wbtreeid=XXXX"

# 详情页URL前缀
INFO_URL_PREFIX = f"{BASE_URL}/info/"

# 请求头 - 可能需要根据目标网站调整
HEADERS = {
    "Referer": "https://your-school-website.edu.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
}
```

### 2. 修改数据解析逻辑

根据您学校网站的HTML结构，修改以下文件：

**a) `official_document_crawler/crawler/fetcher.py`**

调整文章列表解析的正则表达式：

```python
# 根据您学校网站的HTML结构调整这些正则表达式
types = re.findall(r'target="_self">(.*?)</a></div>', html_content)
units = re.findall(r'style="font-size: 14px;">(.*?)</a></div>', html_content)
dates = re.findall(r'style="width:11%;">(.*?)</div>', html_content)
titles = re.findall(r'.htm" title="(.*?)"  target="_blank" style="', html_content)
urls = re.findall(r'"><a href="info/(.*?)" title="', html_content)
```

**b) `official_document_crawler/crawler/parser.py`**

调整文章详情解析逻辑：

```python
# 根据您学校网站的HTML结构调整解析逻辑
def parse_article_details(html_content):
    # 调整内容提取的CSS选择器
    content_form = soup.select('form[name="_newscontent_fromname"]')  # 根据实际结构修改
    
    # 调整时间提取逻辑
    time_span = soup.select_one('span:-soup-contains("发布时间")')  # 根据实际结构修改
    
    # 调整其他字段的提取逻辑...
```

### 3. 修改邮箱验证规则

在 `config.py` 中修改邮箱格式限制：

```python
# 修改为您学校的邮箱格式
SUBSCRIBER_MASK = r"^[a-zA-Z0-9._%+-]+@your-school\.edu\.cn$"
```

### 4. 测试和调试

1. **小范围测试**: 先用小页码范围测试爬虫是否正常工作
2. **检查数据**: 确认抓取的数据格式正确
3. **邮件测试**: 使用测试邮箱验证邮件发送功能

### 5. 重要提示 ⚠️

**合规性警告**：在使用此系统前，请务必：

1. **确认合规性**: 检查您学校的公文通知是否允许对外传播
2. **获得授权**: 如有必要，请获得学校相关部门的使用授权
3. **遵守协议**: 确保遵守学校网站的使用条款和robots.txt规定
4. **控制访问频率**: 避免对目标网站造成过大负载
5. **保护隐私**: 确保不传播包含个人隐私信息的内容

**建议**：
- 在正式使用前联系学校网络中心或相关技术部门
- 考虑与学校合作，获得官方API支持
- 设置合理的爬取间隔，避免影响正常服务

## 🐛 故障排除

### 常见问题

1. **邮件发送失败**
   - 检查SMTP配置是否正确
   - 确认邮箱服务商SMTP服务已开启
   - 验证授权码/应用密码是否正确

2. **数据库连接错误**
   - 确保database目录存在且有写入权限
   - 检查SQLite文件是否损坏

3. **爬虫无法获取数据**
   - 检查网络连接
   - 确认目标网站是否可访问
   - 查看是否需要更新请求头
   - 检查网站结构是否发生变化

### 日志调试

服务运行时会在控制台输出详细日志，包括：
- 🚀 服务启动信息
- 📊 数据库查询结果  
- 📧 邮件发送状态
- ⏰ 定时任务执行情况

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 👥 作者

GoldenMouse Team - 让校园信息触手可及 🐭

---

如有问题，请访问项目主页或提交Issue。
