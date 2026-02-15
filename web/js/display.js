// 结果展示模块

// 渲染关键词搜索结果
function renderResults(results, isMatchMode = false) {
  console.log('渲染结果:', results.length, '条', isMatchMode ? '(匹配模式)' : '');

  const listContainer = document.getElementById('results-list');
  const emptyMessage = document.getElementById('results-empty');
  const countElement = document.getElementById('results-count');

  if (!listContainer) return;

  // 更新计数
  if (countElement) {
    countElement.textContent = `共 ${results.length} 条课标`;
  }

  // 如果没有结果
  if (results.length === 0) {
    listContainer.innerHTML = '';
    if (emptyMessage) {
      emptyMessage.classList.add('visible');
    }
    return;
  }

  // 隐藏空状态
  if (emptyMessage) {
    emptyMessage.classList.remove('visible');
  }

  // 渲染结果行
  listContainer.innerHTML = results.map(item => createResultRow(item, false, null)).join('');

  // 绑定事件
  bindResultEvents();

  // 更新表头复选框
  updateHeaderCheckbox();
}

// 渲染智能匹配结果
function renderMatchResults(matchResults) {
  console.log('渲染匹配结果:', matchResults.length, '条');

  const listContainer = document.getElementById('results-list');
  const emptyMessage = document.getElementById('results-empty');
  const countElement = document.getElementById('results-count');

  if (!listContainer) return;

  // 更新计数
  if (countElement) {
    countElement.textContent = `共 ${matchResults.length} 条匹配课标`;
  }

  // 如果没有结果
  if (matchResults.length === 0) {
    listContainer.innerHTML = '';
    if (emptyMessage) {
      emptyMessage.classList.add('visible');
    }
    return;
  }

  // 隐藏空状态
  if (emptyMessage) {
    emptyMessage.classList.remove('visible');
  }

  // 渲染匹配结果行（带理由）
  listContainer.innerHTML = matchResults.map(match =>
    createResultRow(match.item, true, match.reason)
  ).join('');

  // 绑定事件
  bindResultEvents();
}

// 创建结果行HTML
function createResultRow(item, isMatched, reason) {
  const isSelected = appState.selectedItems.has(item.id);

  // 简化来源显示
  const sourceDisplay = simplifySourceDisplay(item.source);

  // 构建基础行
  let rowHtml = `
    <div class="result-row ${isSelected ? 'selected' : ''} ${isMatched ? 'matched' : ''}"
         data-item-id="${item.id}">
      <div>
        <input
          type="checkbox"
          class="result-checkbox"
          data-item-id="${item.id}"
          ${isSelected ? 'checked' : ''}
        >
      </div>
      <div class="result-source" data-source="${item.source}">${sourceDisplay}</div>
      <div class="result-grade">${item.grade_band || '-'}</div>
      <div class="result-topic">${escapeHtml(item.topic || '无主题')}</div>
      <div class="result-text">
        ${escapeHtml(item.text)}
        ${(item.source === 'NGSS-DCI' || item.source === 'NGSS-PE') && item.text_en ?
          `<a class="show-original-link" data-item-id="${item.id}">显示原文</a>
           <div class="result-text-en" data-item-id="${item.id}">${escapeHtml(item.text_en)}</div>` : ''}
      </div>
  `;

  // 如果是匹配结果，添加匹配理由
  if (isMatched && reason) {
    rowHtml += `
      <div class="result-reason">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style="display: inline-block; margin-right: 4px;">
          <path d="M6 1L6 6L9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        ${escapeHtml(reason)}
      </div>
    `;
  }

  rowHtml += `</div>`;

  return rowHtml;
}

// 绑定结果行事件
function bindResultEvents() {
  // 绑定复选框事件
  document.querySelectorAll('.result-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      e.stopPropagation();
      const itemId = checkbox.dataset.itemId;
      if (typeof toggleSelection === 'function') {
        toggleSelection(itemId);
      }
    });
  });

  // 绑定"显示原文"链接事件
  document.querySelectorAll('.show-original-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.stopPropagation();
      const itemId = link.dataset.itemId;
      const textEn = document.querySelector(`.result-text-en[data-item-id="${itemId}"]`);
      if (textEn) {
        textEn.classList.toggle('visible');
        link.textContent = textEn.classList.contains('visible') ? '隐藏原文' : '显示原文';
      }
    });
  });

  // 绑定行点击事件（点击行也能选中）
  document.querySelectorAll('.result-row').forEach(row => {
    row.addEventListener('click', (e) => {
      // 如果点击的是复选框或显示原文链接，不重复触发
      if (e.target.classList.contains('result-checkbox') ||
          e.target.classList.contains('show-original-link')) {
        return;
      }

      const itemId = row.dataset.itemId;
      if (typeof toggleSelection === 'function') {
        toggleSelection(itemId);
      }
    });
  });
}

// 简化来源显示
function simplifySourceDisplay(source) {
  const displayMap = {
    'NGSS-DCI': 'DCI',
    'NGSS-PE': 'PE',
    'NGSS-SEP': 'SEP',
    'NGSS-CCC': 'CCC',
    '中国义务教育科学课标': '中国义教',
    '中国高中物理课标': '高中物理',
    '中国高中化学课标': '高中化学',
    '中国高中生物课标': '高中生物'
  };

  return displayMap[source] || source;
}

// HTML转义函数
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 导出函数供其他模块使用
if (typeof window !== 'undefined') {
  window.renderResults = renderResults;
  window.renderMatchResults = renderMatchResults;
}
