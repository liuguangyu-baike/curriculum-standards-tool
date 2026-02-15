// 导入Fuse.js (通过CDN，因为这是前端文件)
// 注意：需要在HTML中引入Fuse.js的CDN

// 统一的数据存储
let standardsData = {
  allStandards: [],  // 统一格式后的所有条目
  searchIndex: null,  // Fuse.js搜索索引
  rawData: {         // 保存原始数据供其他模块使用
    dci: null,
    pe: null,
    cn: null
  }
};

// Grade映射函数
function mapGrade(grade, source) {
  if (source.includes('CN')) {
    // 中国课标映射
    const cnMapping = { 'LP': '1-2', 'MP': '3-4', 'HP': '5-6', 'MS': 'MS' };
    return cnMapping[grade] || grade;
  }
  // NGSS映射
  const ngssMapping = {
    'K': 'K',
    '1': '1-2',
    '2': '1-2',
    '3': '3-4',
    '4': '3-4',
    '5': '5-6',
    'MS': 'MS',
    'HS': 'HS'
  };
  return ngssMapping[grade] || grade;
}

// DCI数据转换
function transformDCI(dci) {
  return {
    id: dci.id,
    source: 'NGSS-DCI',
    document: 'DCI',
    domain: dci.domain,
    grade_band: mapGrade(dci.grade, 'NGSS'),
    text: dci.contentZH || dci.content,  // 优先使用中文内容
    text_en: dci.content,                 // 英文原文
    core_concept_title: dci.coreConceptTitle,
    core_concept_title_cn: dci.coreConceptTitleZH || dci.coreConceptTitle,
    sub_concept_title: dci.subConceptTitle,
    sub_concept_title_cn: dci.subConceptTitleZH || dci.subConceptTitle,
    topic: dci.subConceptTitleZH || dci.subConceptTitle,
    // 保留原始数据供详情展示
    _raw: dci
  };
}

// PE数据转换
function transformPE(pe) {
  return {
    id: pe.id,
    source: 'NGSS-PE',
    document: 'PE',
    domain: pe.domain,
    grade_band: mapGrade(pe.grade, 'NGSS'),
    text: pe.content,
    text_en: pe.content,
    core_concept_title: pe.coreConceptTitle,
    core_concept_title_cn: pe.coreConceptTitle,  // PE暂无中文翻译
    topic: pe.coreConceptTitle,
    // 保留原始数据供详情展示
    _raw: pe
  };
}

// CN数据转换
function transformCN(cn) {
  return {
    id: cn.id,
    source: '中国义务教育科学课标',
    document: '义教科学课标',
    domain: cn.domainCode || cn.domain,
    grade_band: mapGrade(cn.gradeBand, 'CN'),
    text: cn.requirement,
    core_concept_title_cn: cn.coreConcept,
    sub_concept_title_cn: cn.topic,
    topic: cn.topic,
    // 保留原始数据供详情展示
    _raw: cn
  };
}

// 加载所有数据
async function loadData() {
  try {
    console.log('开始加载课标数据...');

    // 并行加载三个数据文件
    const [dciRes, peRes, cnRes] = await Promise.all([
      fetch('data/dci_data.json'),
      fetch('data/pe_data.json'),
      fetch('data/cn_compulsory_science_knowledge.json')
    ]);

    // 检查响应状态
    if (!dciRes.ok || !peRes.ok || !cnRes.ok) {
      throw new Error('数据文件加载失败');
    }

    const dciData = await dciRes.json();
    const peData = await peRes.json();
    const cnData = await cnRes.json();

    // 保存原始数据
    standardsData.rawData.dci = dciData;
    standardsData.rawData.pe = peData;
    standardsData.rawData.cn = cnData;

    // 转换并合并数据
    const dciItems = (dciData.dcis || []).map(transformDCI);
    const peItems = (peData.pes || []).map(transformPE);
    const cnItems = (cnData.cnCompulsoryScienceKnowledge || []).map(transformCN);

    standardsData.allStandards = [...dciItems, ...peItems, ...cnItems];

    console.log('数据加载成功:', {
      DCI: dciItems.length,
      PE: peItems.length,
      CN: cnItems.length,
      Total: standardsData.allStandards.length
    });

    // 创建搜索索引 (优先搜索中文字段)
    // 检查Fuse是否已加载
    if (typeof Fuse !== 'undefined') {
      standardsData.searchIndex = new Fuse(standardsData.allStandards, {
        keys: [
          { name: 'text', weight: 2 },           // 中文内容最高权重
          { name: 'topic', weight: 1.5 },        // 主题/话题
          { name: 'core_concept_title_cn', weight: 1.2 },
          { name: 'sub_concept_title_cn', weight: 1.2 },
          { name: 'text_en', weight: 0.8 },      // 英文内容较低权重
          { name: 'id', weight: 0.5 }
        ],
        threshold: 0.3,
        includeScore: true
      });
      console.log('搜索索引创建成功');
    } else {
      console.warn('Fuse.js未加载，搜索功能将不可用');
    }

    // 触发数据加载完成事件
    document.dispatchEvent(new CustomEvent('dataLoaded', { detail: standardsData }));
    return standardsData;
  } catch (error) {
    console.error('数据加载失败:', error);
    const resultsElement = document.getElementById('results');
    if (resultsElement) {
      resultsElement.innerHTML =
        '<p class="empty-message" style="color: red;">数据加载失败，请检查数据文件是否存在</p>';
    }
    return null;
  }
}

// 获取所有可用的领域（去重）
function getAvailableDomains() {
  const domains = new Set();
  standardsData.allStandards.forEach(item => {
    if (item.domain) domains.add(item.domain);
  });
  return Array.from(domains).sort();
}

// 获取所有可用的年级段（去重）
function getAvailableGrades() {
  const grades = new Set();
  standardsData.allStandards.forEach(item => {
    if (item.grade_band) grades.add(item.grade_band);
  });
  // 按预定义顺序排序
  const gradeOrder = ['K', '1-2', '3-4', '5-6', 'MS', 'HS'];
  return Array.from(grades).sort((a, b) => {
    const indexA = gradeOrder.indexOf(a);
    const indexB = gradeOrder.indexOf(b);
    return indexA - indexB;
  });
}

// 获取所有可用的数据源（去重）
function getAvailableSources() {
  const sources = new Set();
  standardsData.allStandards.forEach(item => {
    if (item.source) sources.add(item.source);
  });
  return Array.from(sources).sort();
}

// 执行搜索
function searchStandards(query) {
  if (!query || !standardsData.searchIndex) {
    return standardsData.allStandards;
  }
  const results = standardsData.searchIndex.search(query);
  return results.map(result => result.item);
}

// 应用筛选条件
function filterStandards(filters) {
  let results = standardsData.allStandards;

  // 按来源筛选
  if (filters.sources && filters.sources.length > 0) {
    results = results.filter(item => filters.sources.includes(item.source));
  }

  // 按领域筛选
  if (filters.domains && filters.domains.length > 0) {
    results = results.filter(item => filters.domains.includes(item.domain));
  }

  // 按年级段筛选
  if (filters.grades && filters.grades.length > 0) {
    results = results.filter(item => filters.grades.includes(item.grade_band));
  }

  // 关键词搜索
  if (filters.searchQuery) {
    const searchResults = searchStandards(filters.searchQuery);
    const searchIds = new Set(searchResults.map(item => item.id));
    results = results.filter(item => searchIds.has(item.id));
  }

  return results;
}

// 页面加载时初始化数据
document.addEventListener('DOMContentLoaded', () => {
  loadData();
});

// 导出API（如果需要在其他模块中使用）
if (typeof window !== 'undefined') {
  window.standardsData = standardsData;
  window.loadData = loadData;
  window.searchStandards = searchStandards;
  window.filterStandards = filterStandards;
  window.getAvailableDomains = getAvailableDomains;
  window.getAvailableGrades = getAvailableGrades;
  window.getAvailableSources = getAvailableSources;
}
