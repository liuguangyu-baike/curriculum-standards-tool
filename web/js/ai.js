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
      box.innerHTML = `<div class="text-xs text-slate-400 font-medium">\u6682\u65e0\u5bf9\u8bdd\u3002\u4f60\u53ef\u4ee5\u5148\u9009\u62e9\u4e0a\u4e0b\u6587\uff0c\u7136\u540e\u63d0\u95ee\u6216\u70b9\u201c\u4e00\u952e\u603b\u7ed3\u201d\u3002</div>`;
      return;
    }
    box.innerHTML = state.messages
      .map(m => {
        const isUser = m.role === 'user';
        const bubble = isUser
          ? 'bg-indigo-600 text-white border-indigo-600'
          : 'bg-white text-slate-800 border-slate-200';
        const label = isUser ? '\u4f60' : 'AI';
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
    qs('aiBaseUrl').value = preset.baseUrl ?? cfg.baseUrl;
    qs('aiModel').value = preset.model ?? cfg.model;
  }

  function updateContextSelect() {
    const sel = qs('aiContext');
    if (!sel) return;
    const opts = [];
    if (state.ctx.dcisSelected.length > 0) {
      opts.push({ key: 'selected:dci', label: `\u5df2\u52fe\u9009\uff08DCI\uff09- ${state.ctx.dcisSelected.length} \u6761` });
    }
    opts.push({ key: 'all:dci', label: `\u5168\u90e8\uff08DCI\uff09- ${state.ctx.dcisAll.length} \u6761` });
    state.ctx.groups.forEach(g => {
      opts.push({ key: `${g.key}:dci`, label: `${g.label}\uff08DCI\uff09- ${g.dcis.length} \u6761` });
    });

    sel.innerHTML = opts.map(o => `<option value="${escapeHtml(o.key)}">${escapeHtml(o.label)}</option>`).join('');
  }

  function buildContextPayload(contextKey) {
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

  // ---- 流式 SSE 读取 ----

  async function readSSEStream(resp) {
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let result = '';
    let buffer = '';

    const msgIndex = state.messages.length;
    state.messages.push({ role: 'assistant', content: '' });
    renderMessages();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;
        const payload = trimmed.slice(5).trim();
        if (payload === '[DONE]') continue;
        try {
          const chunk = JSON.parse(payload);
          const delta = chunk?.choices?.[0]?.delta?.content || '';
          if (delta) {
            result += delta;
            state.messages[msgIndex].content = result;
            renderMessages();
          }
        } catch {}
      }
    }

    return result || '(\u65e0\u8f93\u51fa)';
  }

  // ---- 服务端配置缓存 ----
  let _srvCfg = null;
  async function ensureServerConfig() {
    if (_srvCfg) return _srvCfg;
    try {
      const r = await fetch('/api/config');
      if (r.ok) _srvCfg = await r.json();
    } catch {}
    return _srvCfg;
  }

  // ---- 通用请求：发 stream=true，拿到 SSE 流式回复 ----

  async function streamChat(requestMessages) {
    const cfg = collectConfigFromForm();
    state.aiConfig = cfg;
    saveConfig(cfg);

    setStatus('\u6b63\u5728\u8bf7\u6c42\u6a21\u578b\u2026');

    const apiKey = cfg.apiKey || (await ensureServerConfig())?.apiKey || '';
    const baseUrl = (cfg.baseUrl || _srvCfg?.baseUrl || 'https://api.deepseek.com/v1').replace(/\/+$/, '');
    const model = cfg.model || _srvCfg?.model || 'deepseek-chat';

    let resp;
    if (apiKey) {
      resp = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
        body: JSON.stringify({ model, messages: requestMessages, stream: true, temperature: 0.2 })
      });
    } else {
      resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: cfg.provider, baseUrl: cfg.baseUrl, model: cfg.model,
          stream: true, messages: requestMessages
        })
      });
    }

    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      throw new Error(`\u8bf7\u6c42\u5931\u8d25 (${resp.status}) ${errText}`);
    }

    const contentType = resp.headers.get('content-type') || '';
    if (contentType.includes('text/event-stream')) {
      return await readSSEStream(resp);
    }
    const raw = await resp.text();
    if (raw.trimStart().startsWith('data:')) {
      const fakeResp = new Response(raw, { headers: { 'content-type': 'text/event-stream' } });
      return await readSSEStream(fakeResp);
    }
    const data = JSON.parse(raw);
    return data?.choices?.[0]?.message?.content || data?.text || '';
  }

  // ---- callChat: 构建含 DCI 上下文的消息 ----

  async function callChat(userText, contextKey, { systemHint } = {}) {
    const ctx = buildContextPayload(contextKey);

    const ctxSection = ctx.items.length > 0
      ? `\n\n\u5f53\u524d\u8bfe\u6807\u6570\u636e\uff08${ctx.dimension}\u7ef4\u5ea6\uff0c\u5171${ctx.items.length}\u6761\uff09\uff1a\n${JSON.stringify(ctx.items)}`
      : '';
    const system = [
      '\u4f60\u662f\u8bfe\u7a0b\u6807\u51c6\u5206\u6790\u52a9\u624b\u3002',
      '\u8bf7\u53ea\u57fa\u4e8e\u6211\u63d0\u4f9b\u7684\u6761\u76ee\u8fdb\u884c\u603b\u7ed3/\u5f52\u7eb3\uff0c\u4e0d\u8981\u5f15\u5165\u5916\u90e8\u77e5\u8bc6\u6216\u81c6\u6d4b\u3002',
      '\u4e0d\u8981\u9010\u6761\u590d\u8ff0\u6bcf\u4e00\u6761\u6761\u76ee\u7684\u5177\u4f53\u8868\u8ff0\uff1b\u66f4\u5173\u6ce8\u6574\u4f53\u7684\u77e5\u8bc6\u4e0e\u80fd\u529b\u8981\u6c42\u7684\u5e7f\u5ea6\u4e0e\u6df1\u5ea6\u3002',
      '\u8f93\u51fa\u4f7f\u7528\u4e2d\u6587\uff0c\u6761\u7406\u6e05\u6670\uff0c\u5c3d\u91cf\u7528\u8981\u70b9\u5217\u51fa\u3002',
      systemHint ? `\u989d\u5916\u8981\u6c42\uff1a${systemHint}` : ''
    ].filter(Boolean).join('\n') + ctxSection;

    const messages = [
      { role: 'system', content: system },
      ...state.messages.filter(m => m.role !== 'system'),
      { role: 'user', content: userText }
    ];

    return await streamChat(messages);
  }

  // ---- UI 交互 ----

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
      const lastMsg = state.messages[state.messages.length - 1];
      if (lastMsg?.role !== 'assistant') {
        state.messages.push({ role: 'assistant', content: out || '(\u65e0\u8f93\u51fa)' });
      }
      setStatus('\u5b8c\u6210', 'ok');
      renderMessages();
    } catch (e) {
      setStatus(e.message || '\u8bf7\u6c42\u5931\u8d25', 'error');
    }
  }

  async function onSummarize(contextKey) {
    const prompt = [
      '\u8bf7\u4ece\u201c\u77e5\u8bc6\u8981\u6c42\uff08\u6982\u5ff5\u4e0e\u4e3b\u9898\u7684\u8986\u76d6\u8303\u56f4\uff09\u201d\u548c\u201c\u80fd\u529b\u8981\u6c42\uff08\u601d\u7ef4/\u63a2\u7a76/\u5efa\u6a21\u7b49\u8981\u6c42\u7684\u5c42\u7ea7\uff09\u201d\u4e24\u4e2a\u7ef4\u5ea6\uff0c\u6982\u62ec\u8be5\u7ec4 DCI \u7684\u6574\u4f53\u8981\u6c42\u3002',
      '\u91cd\u70b9\u5173\u6ce8\uff1a\u5e7f\u5ea6\uff08\u8986\u76d6\u54ea\u4e9b\u6838\u5fc3\u6982\u5ff5/\u5b50\u6982\u5ff5/\u4e3b\u9898\u5757\uff09\u4e0e\u6df1\u5ea6\uff08\u7406\u89e3\u5c42\u6b21\u3001\u89e3\u91ca/\u63a8\u7406/\u5e94\u7528\u7b49\u5c42\u7ea7\uff09\u3002',
      '\u4e0d\u8981\u9010\u6761\u590d\u8ff0\u6bcf\u6761 DCI \u7684\u5177\u4f53\u5185\u5bb9\uff0c\u800c\u662f\u63d0\u70bc\u7ec4\u5185\u5171\u540c\u7684\u8fdb\u9636\u4e3b\u7ebf\u4e0e\u5173\u952e\u95e8\u69db\u3002',
      '\u6700\u540e\u7ed9\u51fa\uff1a\u8be5\u7ec4\u53ef\u80fd\u7684\u201c\u5b66\u4e60\u8fdb\u9636\u8def\u5f84\u201d\uff08\u4ece\u6d45\u5230\u6df1 3-5 \u7ea7\uff09\u4e0e\u201c\u8bfe\u7a0b\u8bbe\u8ba1\u8981\u70b9\u201d\uff083-5 \u6761\uff09\u3002'
    ].join('\n');
    state.messages.push({ role: 'user', content: `\uff08\u4e00\u952e\u603b\u7ed3\u672c\u7ec4DCI\uff09\n${prompt}` });
    renderMessages();
    try {
      const out = await callChat(prompt, contextKey, { systemHint: '\u8bf7\u6309\u201c\u77e5\u8bc6\u5e7f\u5ea6 / \u80fd\u529b\u4e0e\u8ba4\u77e5\u6df1\u5ea6 / \u5b66\u4e60\u8fdb\u9636\u8def\u5f84 / \u8bfe\u7a0b\u8bbe\u8ba1\u8981\u70b9\u201d\u56db\u6bb5\u8f93\u51fa\u3002' });
      const lastMsg = state.messages[state.messages.length - 1];
      if (lastMsg?.role !== 'assistant') {
        state.messages.push({ role: 'assistant', content: out || '(\u65e0\u8f93\u51fa)' });
      }
      setStatus('\u5b8c\u6210', 'ok');
      renderMessages();
    } catch (e) {
      setStatus(e.message || '\u8bf7\u6c42\u5931\u8d25', 'error');
    }
  }

  async function onCompareAllGroups() {
    const keys = (state.ctx.groups || []).map(g => g.key);
    if (keys.length < 2) {
      setStatus('\u9700\u8981\u81f3\u5c112\u4e2a\u5206\u7ec4\uff08\u4e14\u542f\u7528\u5206\u7ec4\u5c55\u793a\uff09', 'error');
      return;
    }

    const payload = buildComparePayload(keys);
    const prompt = [
      '\u8bf7\u5bf9\u6bd4\u4e0d\u540c\u7ec4\u522b\u5728\u201c\u77e5\u8bc6\u8981\u6c42\u5e7f\u5ea6\u201d\u548c\u201c\u80fd\u529b\u8981\u6c42\u6df1\u5ea6\u201d\u4e0a\u7684\u5dee\u5f02\u3002',
      '\u8981\u6c42\uff1a',
      '1) \u4e0d\u8981\u9010\u6761\u590d\u8ff0\u6761\u76ee\uff1b\u4ee5\u7ec4\u4e3a\u5355\u4f4d\u603b\u7ed3\u3002',
      '2) \u5148\u5206\u522b\u5217\u51fa\u6bcf\u4e00\u7ec4\u522b\u7684\u77e5\u8bc6\u5e7f\u5ea6/\u80fd\u529b\u6df1\u5ea6/\u5173\u952e\u95e8\u69db/\u5178\u578b\u8fdb\u9636\u7279\u5f81\u3002',
      '3) \u518d\u7ed9\u201c\u5dee\u5f02\u89e3\u8bfb\u201d\uff1a\u6307\u51fa\u4e0d\u540c\u7ec4\u522b\u5728\u77e5\u8bc6\u548c\u80fd\u529b\u7684\u6df1\u5ea6\u3001\u5e7f\u5ea6\u4e0a\u6709\u54ea\u4e9b\u660e\u663e\u533a\u522b\u3002',
    ].join('\n');

    state.messages.push({ role: 'user', content: `\uff08\u7ec4\u522b\u5bf9\u6bd4\uff09\n${prompt}` });
    renderMessages();

    try {
      const system = [
        '\u4f60\u662f\u8bfe\u7a0b\u6807\u51c6\u5bf9\u6bd4\u5206\u6790\u52a9\u624b\u3002',
        '\u8bf7\u53ea\u57fa\u4e8e\u6211\u63d0\u4f9b\u7684\u7ec4\u522b\u6761\u76ee\u8fdb\u884c\u5bf9\u6bd4\uff0c\u4e0d\u8981\u5f15\u5165\u5916\u90e8\u77e5\u8bc6\u6216\u81c6\u6d4b\u3002',
        '\u4e0d\u8981\u9010\u6761\u590d\u8ff0\u6bcf\u4e00\u6761\u6761\u76ee\u7684\u5177\u4f53\u8868\u8ff0\uff1b\u66f4\u5173\u6ce8\u6574\u4f53\u8981\u6c42\u5728\u5e7f\u5ea6\u4e0e\u6df1\u5ea6\u4e0a\u7684\u5dee\u5f02\u3002',
        '\u8f93\u51fa\u4f7f\u7528\u4e2d\u6587\uff0c\u6761\u7406\u6e05\u6670\uff0c\u4f18\u5148\u4f7f\u7528\u8981\u70b9\u3002',
        `\n\u5bf9\u6bd4\u6570\u636e\uff08${payload.dimension}\u7ef4\u5ea6\uff0c\u5171${payload.groups.length}\u7ec4\uff09\uff1a\n${JSON.stringify(payload.groups)}`
      ].join('\n');

      const messages = [
        { role: 'system', content: system },
        ...state.messages.filter(m => m.role !== 'system'),
        { role: 'user', content: prompt }
      ];

      const out = await streamChat(messages);
      const lastMsg = state.messages[state.messages.length - 1];
      if (lastMsg?.role !== 'assistant') {
        state.messages.push({ role: 'assistant', content: out || '(\u65e0\u8f93\u51fa)' });
      }
      setStatus('\u5b8c\u6210', 'ok');
      renderMessages();
    } catch (e) {
      setStatus(e.message || '\u8bf7\u6c42\u5931\u8d25', 'error');
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
      setStatus('\u5df2\u4fdd\u5b58\u5230\u672c\u673a\u6d4f\u89c8\u5668', 'ok');
    });

    qs('aiClearKey').addEventListener('click', () => {
      qs('aiApiKey').value = '';
      const cfg = collectConfigFromForm();
      state.aiConfig = cfg;
      saveConfig(cfg);
      setStatus('\u5df2\u6e05\u9664Key\uff08\u4ec5\u672c\u673a\uff09', 'ok');
    });

    qs('aiSend').addEventListener('click', onSend);
    qs('aiInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) onSend();
    });

    qs('aiClearChat').addEventListener('click', () => {
      state.messages = [];
      setStatus('\u5df2\u6e05\u7a7a\u5bf9\u8bdd', 'ok');
      renderMessages();
    });

    const compareBtn = document.getElementById('compareAllGroupsBtn');
    if (compareBtn) compareBtn.addEventListener('click', onCompareAllGroups);

    document.addEventListener('click', (e) => {
      const el = e.target;
      if (!(el instanceof HTMLElement)) return;
      if (el.getAttribute('data-ai-action') === 'summarize') {
        const ctxKey = el.getAttribute('data-ai-context') || 'all:dci';
        onSummarize(ctxKey);
      }
    });

    document.addEventListener('resultsContextUpdated', (e) => {
      const detail = e.detail || {};
      state.ctx.dcisAll = Array.isArray(detail.dcisAll) ? detail.dcisAll : [];
      state.ctx.groups = Array.isArray(detail.groups) ? detail.groups : [];
      updateContextSelect();
      const btn = document.getElementById('compareAllGroupsBtn');
      if (btn) {
        const ok = state.ctx.groups.length >= 2;
        btn.classList.toggle('hidden', !ok);
      }
      if (state.ctx.dcisAll.length > 0) setStatus('\u5c31\u7eea\uff1a\u8bf7\u9009\u62e9\u4e0a\u4e0b\u6587\u5e76\u63d0\u95ee\uff08Ctrl+Enter\u53d1\u9001\uff09');
    });

    document.addEventListener('selectedDCIsUpdated', (e) => {
      const detail = e.detail || {};
      state.ctx.dcisSelected = Array.isArray(detail.selectedDCIs) ? detail.selectedDCIs : [];
      updateContextSelect();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setConfigForm(state.aiConfig);
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
