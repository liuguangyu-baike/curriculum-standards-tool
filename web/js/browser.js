// 浏览器状态管理模块

// 全局应用状态
const appState = {
  currentPage: 'browser', // browser | workbench
  browserMode: 'keyword', // keyword | match

  // 筛选条件
  filters: {
    sources: [],
    domains: [],
    grades: [],
    searchQuery: ''
  },

  // 选中的条目
  selectedItems: new Set(), // 使用Set存储ID，方便查找和去重

  // 匹配结果
  matchResults: [], // [{item, reason}]
  matchQuery: '',

  // AI对话历史
  chatHistory: []
};

// 初始化应用
function initApp() {
  console.log('初始化浏览器...');

  // 绑定页面切换事件
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const page = tab.dataset.page;
      switchPage(page);
    });
  });

  // 绑定模式切换事件
  document.querySelectorAll('.mode-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.mode;
      switchMode(mode);
    });
  });

  // 绑定关键词搜索输入事件
  const keywordInput = document.getElementById('keyword-input');
  if (keywordInput) {
    let debounceTimer;
    keywordInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        appState.filters.searchQuery = e.target.value.trim();
        updateResults();
      }, 300); // 300ms防抖
    });
  }

  // 绑定智能匹配按钮事件
  const matchBtn = document.getElementById('match-btn');
  if (matchBtn) {
    matchBtn.addEventListener('click', handleMatch);
  }

  // 绑定"进入工作台"按钮
  const goToWorkbench = document.getElementById('go-to-workbench');
  if (goToWorkbench) {
    goToWorkbench.addEventListener('click', () => {
      if (appState.selectedItems.size > 0) {
        switchPage('workbench');
      }
    });
  }

  // 绑定"添加更多条目"按钮
  const addMoreItems = document.getElementById('add-more-items');
  if (addMoreItems) {
    addMoreItems.addEventListener('click', () => {
      switchPage('browser');
    });
  }

  // 绑定全选按钮
  const selectAllBtn = document.getElementById('select-all-btn');
  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', toggleSelectAll);
  }

  // 绑定表头复选框
  const headerCheckbox = document.getElementById('header-checkbox');
  if (headerCheckbox) {
    headerCheckbox.addEventListener('change', (e) => {
      toggleSelectAll();
    });
  }

  console.log('浏览器初始化完成');
}

// 页面切换
function switchPage(page) {
  console.log('切换到页面:', page);

  appState.currentPage = page;

  // 更新导航标签状态
  document.querySelectorAll('.nav-tab').forEach(tab => {
    if (tab.dataset.page === page) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // 更新页面显示
  document.querySelectorAll('.page').forEach(p => {
    if (p.id === `page-${page}`) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });

  // 如果切换到工作台，更新工作台显示
  if (page === 'workbench') {
    updateWorkbenchContext();
  }

  // 如果切换到反馈页面，初始化反馈功能
  if (page === 'feedback' && typeof initFeedback === 'function') {
    initFeedback();
  }
}

// 模式切换（关键词搜索 <-> 智能匹配）
function switchMode(mode) {
  console.log('切换到模式:', mode);

  appState.browserMode = mode;

  // 更新模式标签状态
  document.querySelectorAll('.mode-tab').forEach(tab => {
    if (tab.dataset.mode === mode) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // 更新搜索区显示
  document.querySelectorAll('.search-mode').forEach(sm => {
    if (sm.id === `search-mode-${mode}`) {
      sm.classList.add('active');
    } else {
      sm.classList.remove('active');
    }
  });

  // 清空输入
  if (mode === 'keyword') {
    document.getElementById('keyword-input').value = '';
    appState.filters.searchQuery = '';
    hideBanner();
  } else {
    document.getElementById('match-input').value = '';
    appState.matchQuery = '';
  }

  // 更新结果显示
  updateResults();
}

// 智能匹配处理
async function handleMatch() {
  const input = document.getElementById('match-input');
  const query = input.value.trim();

  if (!query) {
    alert('请输入知识点或活动描述');
    return;
  }

  console.log('开始智能匹配:', query);
  appState.matchQuery = query;

  // 显示加载状态
  showLoading();
  const matchBtn = document.getElementById('match-btn');
  matchBtn.disabled = true;

  try {
    // 准备课标摘要数据
    const standards = standardsData.allStandards.map(item => ({
      id: item.id,
      source: item.source,
      grade_band: item.grade_band,
      topic: item.topic,
      text: item.text.substring(0, 200) // 只发送前200字符
    }));

    // 调用匹配API
    const response = await fetch('/api/match', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        standards: standards
      })
    });

    if (!response.ok) {
      throw new Error(`匹配失败: ${response.status}`);
    }

    const result = await response.json();
    console.log('匹配结果:', result);

    // 处理匹配结果
    if (result.matches && Array.isArray(result.matches)) {
      appState.matchResults = result.matches.map(match => {
        const item = standardsData.allStandards.find(s => s.id === match.id);
        return {
          item: item,
          reason: match.reason
        };
      }).filter(m => m.item); // 过滤掉找不到的条目

      // 显示匹配横幅
      showBanner(query, appState.matchResults.length);

      // 更新结果显示
      updateResults();
    } else {
      throw new Error('匹配结果格式错误');
    }

  } catch (error) {
    console.error('匹配失败:', error);
    alert('匹配失败: ' + error.message);
  } finally {
    hideLoading();
    matchBtn.disabled = false;
  }
}

// 显示匹配横幅
function showBanner(query, count) {
  const banner = document.getElementById('match-banner');
  const bannerText = document.getElementById('match-banner-text');

  // 截取query前30个字符
  const shortQuery = query.length > 30 ? query.substring(0, 30) + '...' : query;
  bannerText.textContent = `为「${shortQuery}」匹配到 ${count} 条相关课标`;

  banner.classList.add('visible');
}

// 隐藏匹配横幅
function hideBanner() {
  const banner = document.getElementById('match-banner');
  banner.classList.remove('visible');
  appState.matchResults = [];
}

// 更新结果显示
function updateResults() {
  console.log('更新结果显示');

  if (appState.browserMode === 'keyword') {
    // 关键词搜索模式
    displayKeywordResults();
  } else {
    // 智能匹配模式
    displayMatchResults();
  }

  // 更新选中计数
  updateSelectedCount();
}

// 显示关键词搜索结果
function displayKeywordResults() {
  // 应用筛选条件
  const results = filterStandards(appState.filters);

  console.log('关键词搜索结果:', results.length);

  // 调用display.js中的渲染函数
  if (typeof renderResults === 'function') {
    renderResults(results, false); // false表示非匹配模式
  }
}

// 显示智能匹配结果
function displayMatchResults() {
  console.log('智能匹配结果:', appState.matchResults.length);

  // 调用display.js中的渲染函数
  if (typeof renderMatchResults === 'function') {
    renderMatchResults(appState.matchResults);
  }
}

// 切换选中状态
function toggleSelection(itemId) {
  if (appState.selectedItems.has(itemId)) {
    appState.selectedItems.delete(itemId);
    console.log('取消选中:', itemId);
  } else {
    appState.selectedItems.add(itemId);
    console.log('选中:', itemId);
  }

  // 更新选中计数
  updateSelectedCount();

  // 更新复选框状态
  const checkbox = document.querySelector(`input[data-item-id="${itemId}"]`);
  if (checkbox) {
    checkbox.checked = appState.selectedItems.has(itemId);
  }

  // 更新行样式
  const row = document.querySelector(`.result-row[data-item-id="${itemId}"]`);
  if (row) {
    if (appState.selectedItems.has(itemId)) {
      row.classList.add('selected');
    } else {
      row.classList.remove('selected');
    }
  }
}

// 更新选中计数
function updateSelectedCount() {
  const count = appState.selectedItems.size;

  // 更新底部栏徽章
  const badge = document.getElementById('selected-badge');
  if (badge) {
    badge.textContent = count;
  }

  // 更新"进入工作台"按钮状态
  const button = document.getElementById('go-to-workbench');
  if (button) {
    button.disabled = count === 0;
  }

  console.log('当前选中:', count);
}

// 更新工作台上下文
function updateWorkbenchContext() {
  console.log('更新工作台上下文');

  // 更新计数
  const contextCount = document.getElementById('context-count');
  if (contextCount) {
    contextCount.textContent = `${appState.selectedItems.size}条`;
  }

  // 更新意图提示
  const intentHint = document.getElementById('intent-hint');
  if (intentHint) {
    intentHint.textContent = `基于左侧 ${appState.selectedItems.size} 条课标条目`;
  }

  // 渲染条目卡片
  const listContainer = document.getElementById('selected-items-list');
  if (listContainer) {
    listContainer.innerHTML = '';

    if (appState.selectedItems.size === 0) {
      listContainer.innerHTML = '<p style="text-align: center; color: var(--text-tertiary); padding: 24px;">暂无选中条目<br>请返回浏览器选择课标</p>';
      return;
    }

    // 获取选中的条目数据
    const selectedData = Array.from(appState.selectedItems)
      .map(id => standardsData.allStandards.find(item => item.id === id))
      .filter(item => item); // 过滤掉找不到的

    // 渲染卡片
    selectedData.forEach(item => {
      const card = createItemCard(item);
      listContainer.appendChild(card);
    });
  }
}

// 创建条目卡片
function createItemCard(item) {
  const card = document.createElement('div');
  card.className = 'selected-item-card';
  card.dataset.itemId = item.id;

  card.innerHTML = `
    <div class="item-card-header">
      <div class="item-card-meta">
        <span class="item-card-source">${item.source}</span>
        <span class="item-card-grade">${item.grade_band}</span>
      </div>
      <button class="item-card-remove" data-item-id="${item.id}">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M4 4L12 12M4 12L12 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <div class="item-card-topic">${item.topic || '无主题'}</div>
    <div class="item-card-text">${item.text}</div>
  `;

  // 绑定移除按钮事件
  const removeBtn = card.querySelector('.item-card-remove');
  removeBtn.addEventListener('click', () => {
    removeItem(item.id);
  });

  return card;
}

// 从工作台移除条目
function removeItem(itemId) {
  console.log('移除条目:', itemId);

  // 从选中集合中移除
  appState.selectedItems.delete(itemId);

  // 更新工作台显示
  updateWorkbenchContext();

  // 如果在浏览器页面，更新复选框状态
  const checkbox = document.querySelector(`input[data-item-id="${itemId}"]`);
  if (checkbox) {
    checkbox.checked = false;
  }

  // 更新行样式
  const row = document.querySelector(`.result-row[data-item-id="${itemId}"]`);
  if (row) {
    row.classList.remove('selected');
  }

  // 更新底部栏计数
  updateSelectedCount();
}

// 显示加载提示
function showLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.add('visible');
  }
}

// 隐藏加载提示
function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('visible');
  }
}

// 获取选中的条目数据
function getSelectedItems() {
  return Array.from(appState.selectedItems)
    .map(id => standardsData.allStandards.find(item => item.id === id))
    .filter(item => item);
}

// 全选/取消全选
function toggleSelectAll() {
  // 获取当前显示的结果
  let currentResults = [];
  if (appState.browserMode === 'keyword') {
    currentResults = filterStandards(appState.filters);
  } else {
    currentResults = appState.matchResults.map(m => m.item);
  }

  if (currentResults.length === 0) {
    return;
  }

  // 判断当前是否全选
  const currentIds = new Set(currentResults.map(item => item.id));
  const allSelected = Array.from(currentIds).every(id => appState.selectedItems.has(id));

  if (allSelected) {
    // 取消全选
    currentIds.forEach(id => appState.selectedItems.delete(id));
    console.log('取消全选:', currentIds.size, '条');
  } else {
    // 全选
    currentIds.forEach(id => appState.selectedItems.add(id));
    console.log('全选:', currentIds.size, '条');
  }

  // 更新显示
  updateResults();
  updateSelectedCount();

  // 更新表头复选框状态
  updateHeaderCheckbox();
}

// 更新表头复选框状态
function updateHeaderCheckbox() {
  const headerCheckbox = document.getElementById('header-checkbox');
  if (!headerCheckbox) return;

  // 获取当前显示的结果
  let currentResults = [];
  if (appState.browserMode === 'keyword') {
    currentResults = filterStandards(appState.filters);
  } else {
    currentResults = appState.matchResults.map(m => m.item);
  }

  if (currentResults.length === 0) {
    headerCheckbox.checked = false;
    headerCheckbox.indeterminate = false;
    return;
  }

  // 计算选中数量
  const currentIds = currentResults.map(item => item.id);
  const selectedCount = currentIds.filter(id => appState.selectedItems.has(id)).length;

  if (selectedCount === 0) {
    headerCheckbox.checked = false;
    headerCheckbox.indeterminate = false;
  } else if (selectedCount === currentIds.length) {
    headerCheckbox.checked = true;
    headerCheckbox.indeterminate = false;
  } else {
    headerCheckbox.checked = false;
    headerCheckbox.indeterminate = true;
  }
}

// 导出状态和函数供其他模块使用
if (typeof window !== 'undefined') {
  window.appState = appState;
  window.switchPage = switchPage;
  window.switchMode = switchMode;
  window.toggleSelection = toggleSelection;
  window.updateSelectedCount = updateSelectedCount;
  window.updateWorkbenchContext = updateWorkbenchContext;
  window.getSelectedItems = getSelectedItems;
  window.showLoading = showLoading;
  window.hideLoading = hideLoading;
  window.updateResults = updateResults;
  window.toggleSelectAll = toggleSelectAll;
  window.updateHeaderCheckbox = updateHeaderCheckbox;
}

// 监听数据加载完成事件，然后初始化应用
document.addEventListener('dataLoaded', () => {
  console.log('数据已加载，初始化应用');
  initApp();

  // 初始化筛选面板
  if (typeof initFilters === 'function') {
    initFilters();
  }

  // 显示初始结果
  updateResults();
});
