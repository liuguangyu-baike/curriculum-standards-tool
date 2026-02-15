// 筛选逻辑模块

// 初始化筛选面板
function initFilters() {
  console.log('初始化筛选面板...');

  // 生成数据源筛选
  renderSourceFilters();

  // 生成领域筛选
  renderDomainFilters();

  // 生成年级段筛选
  renderGradeFilters();

  // 绑定清除筛选按钮
  const clearBtn = document.getElementById('clear-filters');
  if (clearBtn) {
    clearBtn.addEventListener('click', clearAllFilters);
  }

  console.log('筛选面板初始化完成');
}

// 渲染数据源筛选
function renderSourceFilters() {
  const container = document.getElementById('filter-sources');
  if (!container) return;

  const sources = getAvailableSources();

  container.innerHTML = sources.map(source => {
    // 简化数据源名称用于显示
    const displayName = simplifySourceName(source);

    return `
      <div class="filter-option">
        <input
          type="checkbox"
          id="source-${encodeURIComponent(source)}"
          value="${source}"
          data-filter-type="source"
        >
        <label for="source-${encodeURIComponent(source)}">${displayName}</label>
      </div>
    `;
  }).join('');

  // 绑定事件
  container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', handleFilterChange);
  });
}

// 渲染领域筛选
function renderDomainFilters() {
  const container = document.getElementById('filter-domains');
  if (!container) return;

  const domains = getAvailableDomains();

  container.innerHTML = domains.map(domain => {
    // 翻译领域名称
    const displayName = translateDomain(domain);

    return `
      <div class="filter-option">
        <input
          type="checkbox"
          id="domain-${domain}"
          value="${domain}"
          data-filter-type="domain"
        >
        <label for="domain-${domain}">${displayName}</label>
      </div>
    `;
  }).join('');

  // 绑定事件
  container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', handleFilterChange);
  });
}

// 渲染年级段筛选
function renderGradeFilters() {
  const container = document.getElementById('filter-grades');
  if (!container) return;

  const grades = getAvailableGrades();

  container.innerHTML = grades.map(grade => {
    return `
      <div class="filter-option">
        <input
          type="checkbox"
          id="grade-${grade}"
          value="${grade}"
          data-filter-type="grade"
        >
        <label for="grade-${grade}">${grade}</label>
      </div>
    `;
  }).join('');

  // 绑定事件
  container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', handleFilterChange);
  });
}

// 处理筛选变化
function handleFilterChange(event) {
  const checkbox = event.target;
  const filterType = checkbox.dataset.filterType;
  const value = checkbox.value;
  const checked = checkbox.checked;

  console.log('筛选变化:', filterType, value, checked);

  // 更新appState中的筛选条件
  if (filterType === 'source') {
    if (checked) {
      if (!appState.filters.sources.includes(value)) {
        appState.filters.sources.push(value);
      }
    } else {
      appState.filters.sources = appState.filters.sources.filter(s => s !== value);
    }
  } else if (filterType === 'domain') {
    if (checked) {
      if (!appState.filters.domains.includes(value)) {
        appState.filters.domains.push(value);
      }
    } else {
      appState.filters.domains = appState.filters.domains.filter(d => d !== value);
    }
  } else if (filterType === 'grade') {
    if (checked) {
      if (!appState.filters.grades.includes(value)) {
        appState.filters.grades.push(value);
      }
    } else {
      appState.filters.grades = appState.filters.grades.filter(g => g !== value);
    }
  }

  console.log('当前筛选条件:', appState.filters);

  // 更新结果显示
  if (typeof updateResults === 'function') {
    updateResults();
  }
}

// 清除所有筛选
function clearAllFilters() {
  console.log('清除所有筛选');

  // 清空筛选条件
  appState.filters.sources = [];
  appState.filters.domains = [];
  appState.filters.grades = [];
  appState.filters.searchQuery = '';

  // 取消所有复选框
  document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(checkbox => {
    checkbox.checked = false;
  });

  // 清空搜索框
  const keywordInput = document.getElementById('keyword-input');
  if (keywordInput) {
    keywordInput.value = '';
  }

  // 更新结果显示
  if (typeof updateResults === 'function') {
    updateResults();
  }
}

// 简化数据源名称
function simplifySourceName(source) {
  const nameMap = {
    'NGSS-DCI': 'NGSS DCI',
    'NGSS-PE': 'NGSS PE',
    'NGSS-SEP': 'NGSS SEP',
    'NGSS-CCC': 'NGSS CCC',
    '中国义务教育科学课标': '中国义教科学',
    '中国高中物理课标': '中国高中物理',
    '中国高中化学课标': '中国高中化学',
    '中国高中生物课标': '中国高中生物'
  };

  return nameMap[source] || source;
}

// 翻译领域名称
function translateDomain(domain) {
  const domainMap = {
    'PS': '物理科学 (PS)',
    'LS': '生命科学 (LS)',
    'ESS': '地球空间 (ESS)',
    'ETS': '工程技术 (ETS)',
    '物质科学': '物质科学',
    '生命科学': '生命科学',
    '地球与宇宙': '地球与宇宙',
    '技术与工程': '技术与工程'
  };

  return domainMap[domain] || domain;
}

// 导出函数供其他模块使用
if (typeof window !== 'undefined') {
  window.initFilters = initFilters;
  window.clearAllFilters = clearAllFilters;
}
