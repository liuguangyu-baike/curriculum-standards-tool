// AI 面板（OpenAI 兼容接口）：
// - 默认走后端 /api/chat（后端用 .env 的 DeepSeek key）
// - 用户可在前端覆盖 provider/baseUrl/model/apiKey（每次请求带给后端，不落盘到服务器）

(function () {
  const STORAGE_KEY = 'ngss_ai_config_v1';

  const DEFAULTS = {
    provider: 'deepseek', // deepseek | openai | custom | gemini_compat | claude_compat
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    apiKey: ''
  };

  const PROVIDER_PRESETS = {
    deepseek: { baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
    openai: { baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
    gemini_compat: { baseUrl: '', model: 'gemini-2.0-flash' }, // 需要兼容网关
    claude_compat: { baseUrl: '', model: 'claude-3-5-sonnet-latest' }, // 需要兼容网关
    custom: { baseUrl: '', model: '' }
  };

  const state = {
    aiConfig: loadConfig(),
    // 最近一次渲染的“可用上下文”
    ctx: {
      dcisAll: [],
      dcisSelected: [],
      groupsEnabled: false,
      groups: [], // [{key,label,dcis}]
    },
    messages: [] // {role, content}
  };

  function loadConfig() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { ...DEFAULTS };
      const parsed = JSON.parse(raw);
      return { ...DEFAULTS, ...(parsed || {}) };
    } catch {
      return { ...DEFAULTS };
    }
  }

  function saveConfig(cfg) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
  }

  function qs(id) {
    return document.getElementById(id);
  }

  function escapeHtml(text) {
    return String(text ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function setStatus(text, type = 'info') {
    const el = qs('aiStatus');
    if (!el) return;
    el.textContent = text;
    el.className =
      type === 'error'
        ? 'text-[11px] font-extrabold text-rose-600'
        : type === 'ok'
          ? 'text-[11px] font-extrabold text-emerald-600'
          : 'text-[11px] font-extrabold text-slate-500';
  }

  function renderMessages() {
    const box = qs('aiMessages');
    if (!box) return;
    if (state.messages.length === 0) {
      box.innerHTML = `<div class="text-xs text-slate-400 font-medium">暂无对话。你可以先选择上下文，然后提问或点“一键总结”。</div>`;
      return;
    }
    box.innerHTML = state.messages
      .map(m => {
        const isUser = m.role === 'user';
        const bubble = isUser
          ? 'bg-indigo-600 text-white border-indigo-600'
          : 'bg-white text-slate-800 border-slate-200';
        const label = isUser ? '你' : 'AI';
        return `
          <div class="flex ${isUser ? 'justify-end' : 'justify-start'}">
            <div class="max-w-[85%] border rounded-2xl px-4 py-3 shadow-sm ${bubble}">
              <div class="text-[10px] font-black uppercase tracking-widest opacity-80 mb-1">${label}</div>
              <div class="text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(m.content)}</div>
            </div>
          </div>
        `;
      })
      .join('');
    box.scrollTop = box.scrollHeight;
  }

  function setConfigForm(cfg) {
    qs('aiProvider').value = cfg.provider;
    qs('aiBaseUrl').value = cfg.baseUrl;
    qs('aiModel').value = cfg.model;
    qs('aiApiKey').value = cfg.apiKey || '';
  }

  function collectConfigFromForm() {
    return {
      provider: qs('aiProvider').value,
      baseUrl: qs('aiBaseUrl').value.trim(),
      model: qs('aiModel').value.trim(),
      apiKey: qs('aiApiKey').value.trim()
    };
  }

  function applyProviderPreset(provider) {
    const preset = PROVIDER_PRESETS[provider] || PROVIDER_PRESETS.custom;
    const cfg = collectConfigFromForm();
    // 只覆盖 baseUrl/model；key 保留
    qs('aiBaseUrl').value = preset.baseUrl ?? cfg.baseUrl;
    qs('aiModel').value = preset.model ?? cfg.model;
  }

  function updateContextSelect() {
    const sel = qs('aiContext');
    if (!sel) return;
    const opts = [];
    if (state.ctx.dcisSelected.length > 0) {
      opts.push({ key: 'selected:dci', label: `已勾选（DCI）- ${state.ctx.dcisSelected.length} 条` });
    }
    opts.push({ key: 'all:dci', label: `全部（DCI）- ${state.ctx.dcisAll.length} 条` });
    state.ctx.groups.forEach(g => {
      opts.push({ key: `${g.key}:dci`, label: `${g.label}（DCI）- ${g.dcis.length} 条` });
    });

    sel.innerHTML = opts.map(o => `<option value="${escapeHtml(o.key)}">${escapeHtml(o.label)}</option>`).join('');
  }

  function buildContextPayload(contextKey) {
    // 目前仅 DCI 维度，未来可扩展为 pe/sep/ccc
    const [key, dim] = String(contextKey || 'all:dci').split(':');
    if (dim !== 'dci') return { dimension: dim, items: [] };

    let items = [];
    if (key === 'selected') {
      items = state.ctx.dcisSelected;
    } else if (key === 'all') {
      items = state.ctx.dcisAll;
    } else {
      const g = state.ctx.groups.find(x => x.key === key);
      items = g ? g.dcis : [];
    }

    // 结构化上下文（尽量短）
    const compact = items.map(d => ({
      id: d.id,
      domain: d.domain,
      grade: d.grade,
      coreConceptZH: d.coreConceptTitleZH,
      subConceptZH: d.subConceptTitleZH,
      contentZH: d.contentZH
    }));

    return { dimension: 'dci', items: compact };
  }

  function buildComparePayload(groupKeys) {
    const groups = (groupKeys || [])
      .map(k => state.ctx.groups.find(g => g.key === k))
      .filter(Boolean)
      .map(g => ({
        key: g.key,
        label: g.label,
        items: g.dcis.map(d => ({
          id: d.id,
          domain: d.domain,
          grade: d.grade,
          coreConceptZH: d.coreConceptTitleZH,
          subConceptZH: d.subConceptTitleZH,
          contentZH: d.contentZH
        }))
      }));
    return { dimension: 'dci', groups };
  }

  async function callChat(userText, contextKey, { systemHint } = {}) {
    const cfg = collectConfigFromForm();
    state.aiConfig = cfg;
    saveConfig(cfg);

    const ctx = buildContextPayload(contextKey);
    const system = [
      '你是课程标准分析助手。',
      '请只基于我提供的条目进行总结/归纳，不要引入外部知识或臆测。',
      '不要逐条复述每一条条目的具体表述；更关注整体的知识与能力要求的广度与深度。',
      '输出使用中文，条理清晰，尽量用要点列出。',
      systemHint ? `额外要求：${systemHint}` : ''
    ].filter(Boolean).join('\n');

    const messages = [
      { role: 'system', content: system },
      ...state.messages.filter(m => m.role !== 'system'),
      {
        role: 'user',
        content:
          `【上下文维度】${ctx.dimension}\n` +
          `【条目数量】${ctx.items.length}\n` +
          `【条目数据(JSON)】\n${JSON.stringify(ctx.items, null, 2)}\n\n` +
          `【问题】${userText}`
      }
    ];

    setStatus('正在请求模型…');
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: cfg.provider,
        baseUrl: cfg.baseUrl,
        model: cfg.model,
        apiKey: cfg.apiKey || undefined,
        messages
      })
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      throw new Error(`请求失败 (${resp.status}) ${errText}`);
    }
    const data = await resp.json();
    const out = data?.text || '';
    return out;
  }

  async function onSend() {
    const input = qs('aiInput');
    const text = (input?.value || '').trim();
    if (!text) return;
    const ctxKey = qs('aiContext').value;

    state.messages.push({ role: 'user', content: text });
    renderMessages();
    input.value = '';

    try {
      const out = await callChat(text, ctxKey);
      state.messages.push({ role: 'assistant', content: out || '(无输出)' });
      setStatus('完成', 'ok');
      renderMessages();
    } catch (e) {
      setStatus(e.message || '请求失败', 'error');
    }
  }

  async function onSummarize(contextKey) {
    const prompt = [
      '请从“知识要求（概念与主题的覆盖范围）”和“能力要求（思维/探究/建模等要求的层级）”两个维度，概括该组 DCI 的整体要求。',
      '重点关注：广度（覆盖哪些核心概念/子概念/主题块）与深度（理解层次、解释/推理/应用等层级）。',
      '不要逐条复述每条 DCI 的具体内容，而是提炼组内共同的进阶主线与关键门槛。',
      '最后给出：该组可能的“学习进阶路径”（从浅到深 3-5 级）与“课程设计要点”（3-5 条）。'
    ].join('\n');
    state.messages.push({ role: 'user', content: `（一键总结本组DCI）\n${prompt}` });
    renderMessages();
    try {
      const out = await callChat(prompt, contextKey, { systemHint: '请按“知识广度 / 能力与认知深度 / 学习进阶路径 / 课程设计要点”四段输出。' });
      state.messages.push({ role: 'assistant', content: out || '(无输出)' });
      setStatus('完成', 'ok');
      renderMessages();
    } catch (e) {
      setStatus(e.message || '请求失败', 'error');
    }
  }

  async function onCompareAllGroups() {
    const keys = (state.ctx.groups || []).map(g => g.key);
    if (keys.length < 2) {
      setStatus('需要至少2个分组（且启用分组展示）', 'error');
      return;
    }

    const payload = buildComparePayload(keys);
    const prompt = [
      '请对比不同组别在“知识要求广度”和“能力要求深度”上的差异。',
      '要求：',
      '1) 不要逐条复述条目；以组为单位总结。',
      '2) 先分别列出每一组别的知识广度/能力深度/关键门槛/典型进阶特征。',
      '3) 再给“差异解读”：指出不同组别在知识和能力的深度、广度上有哪些明显区别。',
    ].join('\n');

    state.messages.push({ role: 'user', content: `（组别对比）\n${prompt}` });
    renderMessages();

    try {
      const cfg = collectConfigFromForm();
      state.aiConfig = cfg;
      saveConfig(cfg);

      const system = [
        '你是课程标准对比分析助手。',
        '请只基于我提供的组别条目进行对比，不要引入外部知识或臆测。',
        '不要逐条复述每一条条目的具体表述；更关注整体要求在广度与深度上的差异。',
        '输出使用中文，条理清晰，优先使用要点。'
      ].join('\n');

      setStatus('正在请求模型…');
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: cfg.provider,
          baseUrl: cfg.baseUrl,
          model: cfg.model,
          apiKey: cfg.apiKey || undefined,
          messages: [
            { role: 'system', content: system },
            ...state.messages.filter(m => m.role !== 'system'),
            {
              role: 'user',
              content:
                `【对比维度】${payload.dimension}\n` +
                `【组别数量】${payload.groups.length}\n` +
                `【组别数据(JSON)】\n${JSON.stringify(payload.groups, null, 2)}\n\n` +
                `【任务】${prompt}`
            }
          ]
        })
      });

      if (!resp.ok) {
        const errText = await resp.text().catch(() => '');
        throw new Error(`请求失败 (${resp.status}) ${errText}`);
      }
      const data = await resp.json();
      const out = data?.text || '';
      state.messages.push({ role: 'assistant', content: out || '(无输出)' });
      setStatus('完成', 'ok');
      renderMessages();
    } catch (e) {
      setStatus(e.message || '请求失败', 'error');
    }
  }

  function bind() {
    const providerEl = qs('aiProvider');
    providerEl.addEventListener('change', () => {
      applyProviderPreset(providerEl.value);
      const cfg = collectConfigFromForm();
      state.aiConfig = cfg;
      saveConfig(cfg);
    });

    qs('aiSave').addEventListener('click', () => {
      const cfg = collectConfigFromForm();
      state.aiConfig = cfg;
      saveConfig(cfg);
      setStatus('已保存到本机浏览器', 'ok');
    });

    qs('aiClearKey').addEventListener('click', () => {
      qs('aiApiKey').value = '';
      const cfg = collectConfigFromForm();
      state.aiConfig = cfg;
      saveConfig(cfg);
      setStatus('已清除Key（仅本机）', 'ok');
    });

    qs('aiSend').addEventListener('click', onSend);
    qs('aiInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) onSend();
    });

    qs('aiClearChat').addEventListener('click', () => {
      state.messages = [];
      setStatus('已清空对话', 'ok');
      renderMessages();
    });

    // “对比全部分组”按钮在表格右上角（仅启用分组时显示）
    const compareBtn = document.getElementById('compareAllGroupsBtn');
    if (compareBtn) compareBtn.addEventListener('click', onCompareAllGroups);

    // 分组表头上的“一键总结”按钮（事件委托）
    document.addEventListener('click', (e) => {
      const el = e.target;
      if (!(el instanceof HTMLElement)) return;
      if (el.getAttribute('data-ai-action') === 'summarize') {
        const ctxKey = el.getAttribute('data-ai-context') || 'all:dci';
        onSummarize(ctxKey);
      }
    });

    // 监听渲染上下文更新
    document.addEventListener('resultsContextUpdated', (e) => {
      const detail = e.detail || {};
      state.ctx.dcisAll = Array.isArray(detail.dcisAll) ? detail.dcisAll : [];
      state.ctx.groups = Array.isArray(detail.groups) ? detail.groups : [];
      updateContextSelect();
      // toggle compare button
      const btn = document.getElementById('compareAllGroupsBtn');
      if (btn) {
        const ok = state.ctx.groups.length >= 2;
        btn.classList.toggle('hidden', !ok);
      }
      // 初次渲染时给一个状态提示
      if (state.ctx.dcisAll.length > 0) setStatus('就绪：请选择上下文并提问（Ctrl+Enter发送）');
    });

    // 监听勾选的DCI列表更新
    document.addEventListener('selectedDCIsUpdated', (e) => {
      const detail = e.detail || {};
      state.ctx.dcisSelected = Array.isArray(detail.selectedDCIs) ? detail.selectedDCIs : [];
      updateContextSelect();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setConfigForm(state.aiConfig);
    // 如果 provider 是 deepseek/openai 等，补全 preset
    applyProviderPreset(state.aiConfig.provider);
    setConfigForm(state.aiConfig);

    bind();
    renderMessages();
    updateContextSelect();
  });

  window.NGSS_AI = {
    summarize: onSummarize
  };
})();

