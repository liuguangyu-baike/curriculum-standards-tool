# NGSS DCI 检索系统

这是一个基于Web的NGSS（Next Generation Science Standards）DCI（Disciplinary Core Ideas）检索与分析工具（第一期仅集成 DCI），支持筛选、分组展示，以及基于查询结果与AI对话/总结。

## 功能特性

- ✅ 按年级筛选（K, 1-5, MS, HS）
- ✅ 按领域筛选（PS, LS, ESS, ETS）
- ✅ 关键词搜索（ID/标题/内容，中英均可）
- ✅ 自定义年级分组（互斥）+ 本地保存（localStorage）
- ✅ 表格视图：中文为主，英文内容可展开
- ✅ AI对话/一键总结（本地Node代理，默认DeepSeek；可切换OpenAI兼容模型并自带Key）

## 文件结构

```
web/
├── index.html          # 主页面
├── css/
│   └── style.css       # 样式文件
├── js/
│   ├── data.js         # 数据加载模块
│   ├── filters.js      # 筛选逻辑模块
│   ├── display.js      # 表格渲染模块
│   ├── groups.js       # 年级分组（互斥+本地保存）
│   └── ai.js           # AI面板（对话/总结）
└── data/
    └── dci_data.json   # 数据文件（由解析脚本生成）
```

## 使用方法

### 1. 生成数据文件

首先运行数据解析脚本生成JSON数据：

```bash
cd scripts
python3 parse_dci.py
```

这将在 `web/data/` 目录下生成 `dci_data.json` 文件。

### 2. 启动Web服务器

由于浏览器安全限制，需要通过HTTP服务器访问。

推荐使用 **Node 本地服务**（包含 `/api/chat` 代理），以避免在前端暴露默认 API Key。

**方式1（推荐）：Node 服务（支持AI）**

```bash
cd web
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
./start_server.sh
```

启动后访问：`http://localhost:8001`

**方式2：仅静态浏览（不含AI）**

```bash
cd web
python3 -m http.server 8001
```

### 3. 访问网站

在浏览器中打开：`http://localhost:8001`

## 使用说明

1. **选择筛选条件**：
   - 年级：可选择多个年级（如K、1、2等）
   - 领域：可选择多个领域（如PS、LS等）
   - 关键词：支持ID/标题/内容关键词搜索（中英均可）

2. **自动筛选**：
   - 勾选/输入后自动更新结果（无需“应用筛选”按钮）

3. **查看详情**：
   - 表格以中文为主；英文内容可展开查看

4. **清除筛选**：
   - 点击"清除筛选"按钮重置所有筛选条件

5. **年级分组（展示用）**：
   - 可新增/删除分组、分配年级（互斥），并启用“按组展示”
   - 分组配置保存在本机浏览器（localStorage）

6. **AI对话/总结**：
   - 可选择上下文（全部/某组），提问或“一键总结本组DCI”
   - 默认使用服务器端 `.env` 的 DeepSeek Key；也可在页面内自带Key/模型（OpenAI兼容）

## 数据结构

### PE (Performance Expectations)
- `id`: PE编码（如 "K-PS2-1"）
- `grade`: 年级
- `domain`: 领域
- `coreConceptTitle`: 核心概念标题
- `content`: 内容
- `clarificationStatement`: 说明
- `assessmentBoundary`: 评价范围

### DCI (Disciplinary Core Ideas)
- `id`: DCI编码（如 "PS2.A-1"）
- `domain`: 领域
- `coreConceptTitle`: 核心概念标题
- `subConceptTitle`: 子概念标题
- `content`: 内容
- `relatedPEs`: 关联的PE列表
- `grades`: 年级列表

### SEP (Science and Engineering Practices)
- `id`: SEP编码（如 "SEP-3-1"）
- `sepNumber`: SEP编号（1-8）
- `sepTitle`: SEP中文标题
- `sepEnglishTitle`: SEP英文标题
- `content`: 内容
- `relatedPEs`: 关联的PE列表
- `grades`: 年级列表

### CCC (Crosscutting Concepts)
- `id`: CCC编码（如 "CCC-2-1"）
- `cccNumber`: CCC编号（1-7）
- `cccTitle`: CCC中文标题
- `cccEnglishTitle`: CCC英文标题
- `content`: 内容
- `relatedPEs`: 关联的PE列表
- `grades`: 年级列表

## 技术栈

- HTML5
- CSS3（响应式设计）
- 原生JavaScript（ES6+）
- JSON数据存储

## 浏览器支持

- Chrome/Edge（推荐）
- Firefox
- Safari
- 移动端浏览器

## 后续扩展计划

- [ ] AI总结功能（基于查询结果生成总结）
- [ ] 导出功能（PDF/Word/Excel）
- [ ] 对比功能（对比不同年级/领域的DCI）
- [ ] 可视化（DCI关系图谱）
- [ ] 中文课标集成

## 许可证

本项目基于NGSS标准文档开发，数据来源于NGSS官方文档。
