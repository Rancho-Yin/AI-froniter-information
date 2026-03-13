# 🤖 AI 前沿日报 · Daily Digest

每天早上 **07:00（北京时间）** 自动向你的邮箱推送一封 AI 前沿日报，内容涵盖：

- 📊 **今日 AI 发展总览**（由 Claude 实时生成）
- 📄 **最新论文**（arXiv · Hugging Face Papers · Papers With Code）
- 🌍 **国际 AI 资讯**（OpenAI · Anthropic · Google DeepMind · Meta · The Rundown AI · Import AI）
- 🇨🇳 **国内 AI 资讯**（量子位 · 机器之心 · 新智元）
- 💻 **AI 硬件 · 算力动态**（NVIDIA · SemiAnalysis · 半导体行业观察）

---

## 目录结构

```
AI-froniter-information/
├── main.py                          # 主入口
├── config.yaml                      # 信源、邮件、调度配置
├── requirements.txt
├── .env.example                     # 环境变量模板
├── src/
│   ├── collectors/
│   │   ├── arxiv_collector.py       # arXiv 官方 API 采集
│   │   └── rss_collector.py         # RSS/Atom feed 采集
│   ├── summarizer/
│   │   └── ai_summarizer.py         # Claude API 总结生成
│   └── email_sender/
│       ├── html_template.py         # HTML 邮件渲染
│       └── sender.py                # SMTP 发送
└── .github/
    └── workflows/
        └── daily_digest.yml         # GitHub Actions 定时调度
```

---

## 快速开始

### 方式一：GitHub Actions（推荐，无需服务器）

#### 第一步：Fork 本仓库

点击右上角 **Fork**，将项目复制到你自己的 GitHub 账户。

#### 第二步：配置 Repository Secrets

进入你的仓库 → **Settings → Secrets and variables → Actions → New repository secret**，添加以下四个 secret：

| Secret 名称 | 说明 |
|---|---|
| `ANTHROPIC_API_KEY` | 在 [console.anthropic.com](https://console.anthropic.com) 获取 |
| `EMAIL_SENDER` | 发件人 Gmail 地址（如 `yourname@gmail.com`） |
| `EMAIL_PASSWORD` | Gmail **App Password**（见下方说明） |
| `EMAIL_RECIPIENT` | 收件人地址，多个用逗号分隔 |

> **Gmail App Password 获取方式**
> 1. 开启 Google 账号[两步验证](https://myaccount.google.com/security)
> 2. 访问 [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
> 3. 创建一个「邮件」应用的专用密码，将生成的 16 位密码填入 `EMAIL_PASSWORD`

#### 第三步：启用 GitHub Actions

进入仓库 → **Actions** → 找到 `AI Frontier Daily Digest` → 点击 **Enable workflow**。

之后每天 UTC 23:00（北京时间 07:00）自动运行。

#### 手动触发 / 预览测试

在 Actions 页面点击 **Run workflow**：
- `test_mode = false`：立即发送真实邮件
- `test_mode = true`：只渲染 HTML，生成可下载的预览文件（不发送邮件）

---

### 方式二：本地运行

```bash
# 1. 克隆项目
git clone https://github.com/Rancho-Yin/AI-froniter-information.git
cd AI-froniter-information

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY、EMAIL_SENDER 等

# 4. 测试渲染（不发送邮件）
python main.py --test
# 打开 test_output.html 预览效果

# 5. 立即运行并发送
python main.py

# 6. 守护进程模式（每天 07:00 自动执行）
python main.py --daemon
```

---

## 邮件效果预览

```
┌─────────────────────────────────────────────┐
│  🤖 AI 前沿日报                              │
│  2026年03月13日  |  每日 07:00 准时送达      │
├─────────────────────────────────────────────┤
│  🌐 今日 AI 发展总览                         │
│  [由 Claude 实时生成的 300-500 字分析]        │
├─────────────────────────────────────────────┤
│  📄 前沿论文                                 │
│  🏆 Claude 精选三篇                          │
│  [arXiv · Hugging Face · Papers With Code]  │
├─────────────────────────────────────────────┤
│  🌍 国际 AI 资讯                             │
│  [OpenAI · Anthropic · DeepMind · Meta ···] │
├─────────────────────────────────────────────┤
│  🇨🇳 国内 AI 资讯                           │
│  [量子位 · 机器之心 · 新智元]                │
├─────────────────────────────────────────────┤
│  💻 AI 硬件 · 算力动态                       │
│  [NVIDIA · SemiAnalysis · 半导体行业观察]    │
└─────────────────────────────────────────────┘
```

---

## 信源列表

### 论文 & 研究
| 平台 | 说明 |
|---|---|
| **arXiv** (cs.AI/LG/CL/CV/RO) | 论文首发，官方 API |
| **Hugging Face Papers** | 社区精选热门论文 |
| **Papers With Code** | SOTA 追踪 |

### 国际资讯
| 平台 | 说明 |
|---|---|
| **The Rundown AI** | 每日英文 AI 快讯 |
| **Import AI** (Jack Clark) | 前 OpenAI 政策负责人视角 |
| **AI Snake Oil** (Princeton) | 理性分析，避免炒作 |
| **OpenAI / Anthropic / DeepMind / Meta** | 官方博客 |

### 国内资讯
| 平台 | 说明 |
|---|---|
| **量子位** | 最快的 AI 中文资讯 |
| **机器之心** | 深度技术解读 |
| **新智元** | AI 产业动态 |

### 硬件 & 算力
| 平台 | 说明 |
|---|---|
| **NVIDIA AI Blog** | GPU / 算力官方动态 |
| **SemiAnalysis** | 最深度的芯片分析 |
| **半导体行业观察** | 国内算力生态 |

---

## 自定义配置

编辑 `config.yaml` 可以：
- 修改发送时间（`schedule.time`）
- 增删 RSS 信源（`sources.rss_feeds`）
- 调整每个板块的最大条目数（`display.*`）
- 切换 Claude 模型（`claude.model`）

---

## License

MIT
