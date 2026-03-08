function normalizeBaseUrl(baseUrl) {
  let u = String(baseUrl || '').trim();
  if (!u) return '';
  u = u.replace(/\/+$/, '');
  if (u === 'https://api.deepseek.com') u = 'https://api.deepseek.com/v1';
  return u;
}

const SYSTEM_PROMPT = `你是课标匹配专家。用户会描述一个知识点或教学活动，你需要在提供的课标数据库中找到所有相关的课标条目。

要求：
1. 返回JSON格式: {"matches": [{"id": "条目ID", "reason": "匹配理由"}]}
2. 匹配理由需说明该课标与用户描述的关联点
3. 如果用户描述的内容难度超出或低于某课标的年级要求，需在理由中明确指出
4. 按相关度从高到低排序
5. 只返回真正相关的条目，不要为了数量而勉强匹配
6. 如果没有找到相关条目，返回空数组`;

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    const body = req.body || {};
    const { query, standards, baseUrl: userBaseUrl, model: userModel, apiKey: userKey } = body;

    if (!query) return res.status(400).json({ error: 'Missing query' });
    if (!Array.isArray(standards)) return res.status(400).json({ error: 'Missing standards array' });

    const baseUrl = normalizeBaseUrl(userBaseUrl) || normalizeBaseUrl(process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1');
    const model = userModel || process.env.DEEPSEEK_MODEL || 'deepseek-chat';
    const apiKey = String(userKey || '').trim() || process.env.DEEPSEEK_API_KEY || '';

    if (!baseUrl) return res.status(400).json({ error: 'Missing baseUrl' });
    if (!model) return res.status(400).json({ error: 'Missing model' });
    if (!apiKey) return res.status(400).json({ error: 'Missing apiKey' });

    const userPrompt = `用户输入: ${query}

课标数据库摘要：
${standards.map(s => `ID: ${s.id} | 来源: ${s.source} | 年级: ${s.grade_band} | 主题: ${s.topic} | 内容: ${s.text.substring(0, 100)}...`).join('\n')}

请返回匹配结果JSON。`;

    const upstream = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.2,
        response_format: { type: 'json_object' }
      })
    });

    const text = await upstream.text();
    if (!upstream.ok) {
      return res.status(upstream.status).send(text);
    }

    const data = JSON.parse(text);
    const content = data?.choices?.[0]?.message?.content || '{}';
    const result = JSON.parse(content);
    return res.status(200).json(result);
  } catch (e) {
    return res.status(500).json({ error: e?.message || String(e) });
  }
}
