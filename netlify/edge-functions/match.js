function normalizeBaseUrl(baseUrl) {
  let u = String(baseUrl || '').trim().replace(/\/+$/, '');
  if (u === 'https://api.deepseek.com') u = 'https://api.deepseek.com/v1';
  return u;
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

const SYSTEM_PROMPT = `你是课标匹配专家。用户会描述一个知识点或教学活动，你需要在提供的课标数据库中找到所有相关的课标条目。

要求：
1. 返回JSON格式: {"matches": [{"id": "条目ID", "reason": "匹配理由"}]}
2. 匹配理由需说明该课标与用户描述的关联点
3. 如果用户描述的内容难度超出或低于某课标的年级要求，需在理由中明确指出
4. 按相关度从高到低排序
5. 只返回真正相关的条目，不要为了数量而勉强匹配
6. 如果没有找到相关条目，返回空数组`;

export default async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405, headers: corsHeaders });
  }

  try {
    const body = await request.json();
    const { query, standards, baseUrl: userBaseUrl, model: userModel, apiKey: userKey } = body;

    if (!query) return json({ error: 'Missing query' }, 400);
    if (!Array.isArray(standards)) return json({ error: 'Missing standards array' }, 400);

    const baseUrl = normalizeBaseUrl(userBaseUrl) || normalizeBaseUrl(Deno.env.get('DEEPSEEK_BASE_URL') || 'https://api.deepseek.com/v1');
    const model = userModel || Deno.env.get('DEEPSEEK_MODEL') || 'deepseek-chat';
    const apiKey = String(userKey || '').trim() || Deno.env.get('DEEPSEEK_API_KEY') || '';

    if (!baseUrl) return json({ error: 'Missing baseUrl' }, 400);
    if (!model) return json({ error: 'Missing model' }, 400);
    if (!apiKey) return json({ error: 'Missing apiKey' }, 400);

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
      return new Response(text, { status: upstream.status, headers: corsHeaders });
    }

    const data = JSON.parse(text);
    const content = data?.choices?.[0]?.message?.content || '{}';
    const result = JSON.parse(content);
    return json(result);
  } catch (e) {
    return json({ error: e?.message || String(e) }, 500);
  }
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}
