# 课标可视化工具 v2.0

> NGSS和中国课标的智能匹配与AI分析工具

## 🎯 项目概述

这是一个帮助课程设计团队快速查找、匹配和分析课程标准的工具。支持：
- **NGSS课标**: DCI（学科核心概念）、PE（表现期望）
- **中国义教科学课标**: 物质科学、生命科学、地球与宇宙科学等

## 📊 当前状态

### ✅ Phase 1: 数据层改造（已完成 2026-02-14）
- [x] 三个数据源统一加载（DCI/PE/CN）
- [x] Grade映射（NGSS 1-5 → 1-2/3-4/5-6, CN LP/MP/HP → 1-2/3-4/5-6）
- [x] Fuse.js全文搜索索引
- [x] `/api/match` 智能匹配接口

### 🚧 Phase 2: 浏览器界面（待开始）
- [ ] 双页面结构（浏览器 + AI工作台）
- [ ] 关键词搜索模式
- [ ] 智能匹配模式
- [ ] UI方案4样式

### 📅 Phase 3: AI工作台（计划中）
- [ ] 条目面板
- [ ] AI对话区
- [ ] 4个意图按钮（比较、提炼、找知识、找活动）

### 📅 Phase 4: 测试优化（计划中）
- [ ] 端到端测试
- [ ] 样式微调
- [ ] 响应式适配

## 🚀 快速开始

### 1. 启动服务器
```bash
cd web
node server.js
```

### 2. 访问应用
- **主应用**: http://localhost:8001/
- **测试页面**: http://localhost:8001/test.html

### 3. 配置环境变量
在 `web/.env` 中配置：
```env
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your_api_key_here
```

## 📚 文档

- **[QUICKSTART.md](./QUICKSTART.md)** - 快速验证Phase 1功能
- **[Phase1-完成总结.md](./Phase1-完成总结.md)** - Phase 1实现详情
- **[Phase1-验证报告.md](./Phase1-验证报告.md)** - 完整验证清单
- **[PRD-课标工具-v2.md](./PRD-课标工具-v2.md)** - 产品需求文档
- **[UI设计说明-课标工具-v2.md](./UI设计说明-课标工具-v2.md)** - UI设计方案

## 🛠 技术栈

- **后端**: Express.js (Node.js)
- **前端**: 原生JavaScript + Tailwind CSS
- **搜索**: Fuse.js (CDN)
- **AI**: DeepSeek API (OpenAI兼容)

## 📦 数据源

### NGSS课标
- `web/data/dci_data.json` - 学科核心概念（DCI）
- `web/data/pe_data.json` - 表现期望（PE）

### 中国课标
- `web/data/cn_compulsory_science_knowledge.json` - 义务教育科学课标

## 🧪 测试

### 交互式测试
访问 http://localhost:8001/test.html 进行：
- 数据加载验证
- Grade映射测试
- 搜索功能测试
- 数据样本查看

### API测试
```bash
./test_api.sh
```

### 浏览器控制台测试
```javascript
// 查看数据统计
console.log('总条目:', standardsData.allStandards.length);

// 测试搜索
const results = searchStandards('物质');
console.log('搜索结果:', results.length);

// 查看可用年级
console.log('可用年级:', getAvailableGrades());
```

## 📖 API接口

### POST /api/chat
标准AI对话接口

### POST /api/match
智能匹配课标条目

**请求**:
```json
{
  "query": "学习用弹簧秤测量重力",
  "standards": [...课标摘要数组],
  "apiKey": "可选"
}
```

**响应**:
```json
{
  "matches": [
    {
      "id": "条目ID",
      "reason": "匹配理由"
    }
  ]
}
```

## 🎨 UI设计

采用UI方案4的蓝灰学术风格：
- **背景**: 浅灰 (#f0f2f5) / 暖灰 (#f7f6f3)
- **强调色**: 蓝色 (#3b6fc0)
- **匹配色**: 绿色 (#276749)

## 🔧 开发指南

### 项目结构
```
├── web/
│   ├── data/           # 课标数据文件
│   ├── js/             # JavaScript模块
│   │   ├── data.js     # 数据加载（✅已完成）
│   │   ├── ai.js       # AI功能
│   │   ├── filters.js  # 筛选逻辑
│   │   ├── display.js  # 结果展示
│   │   └── groups.js   # 分组逻辑
│   ├── css/            # 样式文件
│   ├── index.html      # 主页面
│   ├── test.html       # 测试页面
│   └── server.js       # Express服务器（✅已完成）
├── scripts/            # 数据提取脚本
└── source-documents/   # 原始课标文档
```

### 添加新数据源
1. 在 `web/data/` 添加JSON文件
2. 在 `data.js` 中添加transform函数
3. 更新 `loadData()` 函数加载新数据源
4. 在测试页面验证

## 🐛 已知问题

无重大问题。

## 📝 更新日志

### v2.0.0-phase1 (2026-02-14)
- ✅ 完成数据层改造
- ✅ 统一三个数据源（DCI/PE/CN）
- ✅ Grade映射规则实现
- ✅ Fuse.js搜索索引
- ✅ `/api/match` 智能匹配接口
- ✅ 完整的测试页面和文档

### v1.0.0 (2026-02-08)
- 初始版本
- DCI数据浏览
- 基础筛选和分组
- 简单AI对话

## 📄 工具用途（历史参考）

从课程标准文档（NGSS + 中国课标）提取结构化数据，并通过Web界面可视化展示。

功能包括：
- 提取NGSS的核心概念（DCI）、科学实践（SEP）、跨学科概念（CCC）
- 提取中国义务教育科学课程标准的知识点
- 通过Web界面可视化展示和检索

### 数据提取（可选）
如需重新提取数据：
- 运行scripts/中的Python脚本
- 从source-documents/提取数据 → 生成JSON到web/data/

---

**最后更新**: 2026-02-14
**当前版本**: v2.0.0-phase1
**下一步**: Phase 2 浏览器界面开发
