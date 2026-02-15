# 快速开始 - Phase 1 验证

## 1. 启动服务器

```bash
cd "/Users/liuguangyu/Desktop/A-工作/05.1-技能开发/2602 | 课标可视化工具/web"
node server.js
```

看到以下输出表示启动成功：
```
[info] serving static from /Users/liuguangyu/Desktop/A-工作/05.1-技能开发/2602 | 课标可视化工具/web
NGSS DCI Explorer server running on http://localhost:8001
```

## 2. 访问测试页面

打开浏览器访问：**http://localhost:8001/test.html**

## 3. 执行验证测试

### 测试1：查看数据加载统计
页面加载后，自动显示：
- 总条目数
- DCI条目数
- PE条目数
- CN条目数
- 搜索索引状态

### 测试2：验证Grade映射
点击 **"运行Grade映射测试"** 按钮

期望结果：所有测试通过 ✓
- NGSS: 1→1-2, 2→1-2, 3→3-4, 5→5-6
- CN: LP→1-2, MP→3-4, HP→5-6

### 测试3：测试搜索功能
1. 在搜索框输入关键词，例如：**物质**
2. 点击 **"搜索"** 按钮
3. 查看搜索结果

期望结果：返回相关课标条目，包含ID、来源、年级、主题、内容

### 测试4：查看数据样本
点击 **"显示各数据源样本"** 按钮

期望结果：显示DCI、PE、CN三个数据源的样本数据，包含所有统一字段

## 4. 控制台验证（可选）

按F12打开浏览器开发者工具，在Console中执行：

```javascript
// 查看数据统计
console.log('总条目数:', standardsData.allStandards.length);
console.log('可用领域:', getAvailableDomains());
console.log('可用年级:', getAvailableGrades());
console.log('数据源:', getAvailableSources());

// 验证Grade映射
const testGrade = standardsData.allStandards.find(s =>
  s.source === 'NGSS-DCI' && s._raw.grade === '1'
);
console.log('Grade 1 映射结果:', testGrade?.grade_band); // 应显示 "1-2"

// 测试搜索
const results = searchStandards('物质');
console.log('搜索"物质"结果:', results.length);
console.table(results.slice(0, 3));
```

## 5. API接口测试（可选）

测试智能匹配接口：

```bash
cd "/Users/liuguangyu/Desktop/A-工作/05.1-技能开发/2602 | 课标可视化工具"
./test_api.sh
```

**注意**: 需要在 `web/.env` 中配置 `DEEPSEEK_API_KEY`

## 验证成功标准

✅ 数据加载无错误
✅ 三个数据源条目数都大于0
✅ Grade映射测试全部通过
✅ 搜索功能返回正确结果
✅ 控制台无报错信息

## 常见问题

### Q: 数据加载失败怎么办？
A: 检查以下几点：
1. 确认 `web/data/` 目录下存在三个JSON文件
2. 查看浏览器控制台错误信息
3. 确认服务器正在运行（8001端口）

### Q: 搜索索引未创建？
A: 检查：
1. Fuse.js CDN是否加载成功（查看Network面板）
2. 控制台是否有报错

### Q: Grade映射测试失败？
A: 检查：
1. 数据文件是否是最新版本
2. 查看具体失败的映射规则
3. 检查 `data.js` 中的 `mapGrade()` 函数

---

**当前状态**: Phase 1 数据层改造已完成 ✅
**下一步**: Phase 2 浏览器界面开发
