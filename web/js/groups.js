// 年级分组（互斥）+ localStorage 持久化
// 约定：分组仅用于展示与AI上下文选择，不影响筛选结果集合

(function () {
  const STORAGE_KEY = 'ngss_grade_groups_v1';
  const STORAGE_KEY_ENABLED = 'ngss_grade_groups_enabled_v1';
  const ALL_GRADES = ['K', '1', '2', '3', '4', '5', 'MS', 'HS'];

  function uid() {
    return 'g_' + Math.random().toString(36).slice(2, 10);
  }

  function loadGroups() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed
        .filter(g => g && typeof g === 'object')
        .map(g => ({
          id: String(g.id || uid()),
          name: String(g.name || '未命名分组'),
          grades: Array.isArray(g.grades) ? g.grades.map(String).filter(x => ALL_GRADES.includes(x)) : []
        }));
    } catch {
      return [];
    }
  }

  function saveGroups(groups) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(groups));
  }

  function loadEnabled() {
    const v = localStorage.getItem(STORAGE_KEY_ENABLED);
    if (v === null) return true;
    return v === '1';
  }

  function saveEnabled(enabled) {
    localStorage.setItem(STORAGE_KEY_ENABLED, enabled ? '1' : '0');
  }

  function buildGradeOwnerMap(groups) {
    const map = new Map();
    groups.forEach(g => {
      g.grades.forEach(gr => map.set(gr, g.id));
    });
    return map;
  }

  function dispatchChanged() {
    document.dispatchEvent(new CustomEvent('groupsChanged'));
  }

  function render() {
    const root = document.getElementById('groupBuilder');
    if (!root) return;

    const enabledEl = document.getElementById('groupEnabled');
    if (enabledEl) enabledEl.checked = state.enabled;

    const gradeOwner = buildGradeOwnerMap(state.groups);

    const groupCards = state.groups.map(g => {
      const gradeButtons = ALL_GRADES.map(gr => {
        const isSelected = g.grades.includes(gr);
        const owner = gradeOwner.get(gr);
        const isLocked = !isSelected && owner && owner !== g.id;
        const ownerName = isLocked ? (state.groups.find(x => x.id === owner)?.name || '其它分组') : '';

        const btnClass = isLocked
          ? 'bg-slate-100 text-slate-300 border-slate-200 cursor-not-allowed'
          : isSelected
            ? 'bg-indigo-600 text-white border-indigo-600'
            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50';

        const title = isLocked ? `已在「${ownerName}」中` : '';

        return `
          <button
            type="button"
            class="text-[11px] py-2 rounded-lg font-extrabold transition-all border text-center ${btnClass}"
            data-action="toggle-grade"
            data-group-id="${g.id}"
            data-grade="${gr}"
            ${isLocked ? 'disabled' : ''}
            title="${title}"
          >${gr}</button>
        `;
      }).join('');

      return `
        <div class="border border-slate-200 rounded-2xl p-4 bg-slate-50">
          <div class="flex items-center justify-between gap-2 mb-3">
            <input
              class="w-full bg-white border border-slate-200 rounded-xl py-2 px-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-400"
              value="${escapeHtml(g.name)}"
              data-action="rename-group"
              data-group-id="${g.id}"
              placeholder="分组名称"
            />
            <button
              type="button"
              class="shrink-0 px-3 py-2 rounded-xl text-xs font-extrabold border border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
              data-action="delete-group"
              data-group-id="${g.id}"
              title="删除分组"
            >删除</button>
          </div>
          <div class="grid grid-cols-4 gap-1.5">
            ${gradeButtons}
          </div>
        </div>
      `;
    }).join('');

    root.innerHTML = groupCards || `
      <div class="text-xs text-slate-400 font-medium">
        暂无分组。点击“新增分组”开始配置。
      </div>
    `;
  }

  function escapeHtml(text) {
    return String(text ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function addGroup() {
    state.groups.push({ id: uid(), name: `分组${state.groups.length + 1}`, grades: [] });
    saveGroups(state.groups);
    render();
    dispatchChanged();
  }

  function clearGroups() {
    state.groups = [];
    saveGroups(state.groups);
    render();
    dispatchChanged();
  }

  function deleteGroup(groupId) {
    state.groups = state.groups.filter(g => g.id !== groupId);
    saveGroups(state.groups);
    render();
    dispatchChanged();
  }

  function renameGroup(groupId, name) {
    const g = state.groups.find(x => x.id === groupId);
    if (!g) return;
    g.name = name || '未命名分组';
    saveGroups(state.groups);
    dispatchChanged();
  }

  function toggleGrade(groupId, grade) {
    const g = state.groups.find(x => x.id === groupId);
    if (!g) return;

    const had = g.grades.includes(grade);
    if (had) {
      g.grades = g.grades.filter(x => x !== grade);
    } else {
      // 互斥：先从其它组移除
      state.groups.forEach(other => {
        if (other.id !== g.id) other.grades = other.grades.filter(x => x !== grade);
      });
      g.grades = [...g.grades, grade];
    }

    // 规范排序
    g.grades = ALL_GRADES.filter(x => g.grades.includes(x));

    saveGroups(state.groups);
    render();
    dispatchChanged();
  }

  function getConfig() {
    return {
      enabled: state.enabled,
      groups: state.groups.map(g => ({ id: g.id, name: g.name, grades: [...g.grades] }))
    };
  }

  const state = {
    enabled: loadEnabled(),
    groups: loadGroups()
  };

  document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('addGroup');
    const clearBtn = document.getElementById('clearGroups');
    const enabledEl = document.getElementById('groupEnabled');

    if (addBtn) addBtn.addEventListener('click', addGroup);
    if (clearBtn) clearBtn.addEventListener('click', clearGroups);

    if (enabledEl) {
      enabledEl.checked = state.enabled;
      enabledEl.addEventListener('change', () => {
        state.enabled = !!enabledEl.checked;
        saveEnabled(state.enabled);
        dispatchChanged();
      });
    }

    // Delegation
    document.addEventListener('click', (e) => {
      const el = e.target;
      if (!(el instanceof HTMLElement)) return;

      const action = el.getAttribute('data-action');
      if (!action) return;

      if (action === 'delete-group') {
        deleteGroup(el.getAttribute('data-group-id'));
      } else if (action === 'toggle-grade') {
        toggleGrade(el.getAttribute('data-group-id'), el.getAttribute('data-grade'));
      }
    });

    document.addEventListener('input', (e) => {
      const el = e.target;
      if (!(el instanceof HTMLElement)) return;
      const action = el.getAttribute('data-action');
      if (action === 'rename-group') {
        renameGroup(el.getAttribute('data-group-id'), el.value);
      }
    });

    render();
  });

  // Expose
  window.NGSS_GROUPS = { getConfig };
})();

