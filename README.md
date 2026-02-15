# Curriculum Standards Tool

> 课标工具 - 智能课程标准浏览与分析系统

一个集成了 NGSS（美国新一代科学标准）和中国课程标准的智能浏览与分析工具，支持关键词搜索、AI 智能匹配和基于选中课标的深度分析。

## ✨ 主要功能

### 📚 课标浏览器
- **关键词搜索**: 支持全文搜索，实时过滤课标条目
- **结构化筛选**: 按数据源、领域、年级段筛选
- **智能匹配**: 基于 AI 的语义匹配，输入知识点或活动描述自动匹配相关课标
- **批量选择**: 支持全选、多选，跨模式保持选中状态

### 🤖 AI 工作台
- **基于上下文的分析**: 选中多条课标后进行深度分析
- **四大分析意图**:
  - **比较**: 对比不同来源/年级课标的共性与差异
  - **提炼**: 提炼核心概念和能力进阶路径
  - **找知识**: 推荐相关科学知识和教学内容
  - **找活动**: 推荐实验设计和探究活动
- **对话式交互**: 支持自由提问和多轮对话

### 💬 使用反馈
- 用户可以提交文字反馈和截图
- 反馈自动通过邮件发送给开发者
- 支持拖拽上传图片（最多3张）

## 🚀 快速开始

### 环境要求
- Node.js 16+
- npm 或 yarn

### 安装

```bash
# 克隆仓库
git clone https://github.com/liuguangyu-baike/curriculum-standards-tool.git
cd curriculum-standards-tool/web

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

### 配置

编辑 `web/.env` 文件:

```env
# DeepSeek API 配置（用于 AI 功能）
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 服务器端口
PORT=8001

# SMTP 配置（用于反馈功能）
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your-email@163.com
SMTP_PASS=your-smtp-password
```

### 运行

```bash
# 启动开发服务器
npm run dev

# 或使用启动脚本
./start_server.sh
```

访问 http://localhost:8001

## 📊 数据源

项目整合了以下课程标准：

- **NGSS DCI** (Disciplinary Core Ideas) - 学科核心概念
- **NGSS PE** (Performance Expectations) - 表现期望
- **中国义务教育科学课标** - 1-9年级科学课程标准

## 🛠️ 技术栈

### 前端
- 原生 JavaScript (ES6+)
- CSS Grid + Flexbox
- Fuse.js (全文搜索)

### 后端
- Express.js
- Nodemailer (邮件发送)
- Multer (文件上传)

### AI 集成
- DeepSeek API (OpenAI 兼容接口)
- 支持智能匹配和对话分析

## 📁 项目结构

```
curriculum-standards-tool/
├── web/                    # Web 应用主目录
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript 模块
│   │   ├── data.js        # 数据加载和处理
│   │   ├── browser.js     # 浏览器状态管理
│   │   ├── filters.js     # 筛选逻辑
│   │   ├── display.js     # 结果展示
│   │   ├── match.js       # 智能匹配
│   │   ├── workbench.js   # AI 工作台
│   │   └── feedback.js    # 反馈功能
│   ├── data/              # 课标数据文件
│   ├── index.html         # 主页面
│   ├── server.js          # Express 服务器
│   └── package.json       # 依赖配置
├── scripts/               # 数据处理脚本
├── source-documents/      # 原始课标文档
├── docs/                  # 项目文档
│   ├── design/           # 设计文档（PRD、UI）
│   ├── development/      # 开发文档
│   └── 反馈功能配置说明.md
├── QUICKSTART.md          # 快速开始指南
└── README.md             # 本文件
```

## 🎨 UI 特性

- **蓝灰学术风格**: 专业、简洁的设计语言
- **冻结表头**: 滚动时表头始终可见
- **来源色块标识**: 不同数据源用不同颜色区分
  - DCI: 蓝色
  - PE: 紫色
  - 中国课标: 橙色
- **显示英文原文**: DCI/PE 支持查看英文原文
- **响应式设计**: 适配不同屏幕尺寸

## 📖 使用指南

详细使用说明请参考 [QUICKSTART.md](QUICKSTART.md)

### 基本工作流程

1. **浏览和筛选**
   - 使用筛选面板选择数据源、领域、年级
   - 或输入关键词搜索

2. **智能匹配**（可选）
   - 切换到"智能匹配"模式
   - 输入你的知识点或活动描述
   - AI 自动匹配相关课标并给出理由

3. **选中课标**
   - 勾选感兴趣的课标条目
   - 支持全选和跨模式选择

4. **AI 分析**
   - 点击"进入工作台"
   - 选择分析意图或自由提问
   - 获得基于选中课标的深度分析

## 🔧 配置说明

### SMTP 邮箱配置

反馈功能需要配置 SMTP 服务器。推荐使用：

- **163 邮箱**: 稳定、免费
- **QQ 邮箱**: 需要生成授权码
- **Gmail**: 需要应用专用密码

详细配置步骤请参考 [docs/反馈功能配置说明.md](docs/反馈功能配置说明.md)

### DeepSeek API

获取 API Key:
1. 访问 https://platform.deepseek.com/
2. 注册并获取 API Key
3. 填入 `.env` 文件的 `DEEPSEEK_API_KEY`

## 🚢 部署

### Netlify 部署

1. 将项目推送到 GitHub
2. 在 Netlify 导入项目
3. 配置构建设置:
   - Base directory: `web`
   - Publish directory: `.`
4. 添加环境变量（与 .env 相同）
5. 部署

即使 GitHub 仓库是私有的，Netlify 部署后的网站仍然可以公开访问。

## 📝 开发文档

- [PRD - 产品需求文档](docs/design/PRD-课标工具-v2.md)
- [UI 设计说明](docs/design/UI设计说明-课标工具-v2.md)
- [数据格式说明](docs/development/课标格式转换需求.md)
- [反馈功能配置](docs/反馈功能配置说明.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

Private Project

## 👤 作者

刘广宇 (liuguangyu@kanyun.com)

## 🙏 致谢

- NGSS（Next Generation Science Standards）
- 中华人民共和国教育部课程标准
- DeepSeek AI
- Claude Opus 4.6

---

**Co-Developed with**: Claude Opus 4.6
