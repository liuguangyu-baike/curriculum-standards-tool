function normalizeBaseUrl(baseUrl) {
  let u = String(baseUrl || '').trim();
  if (!u) return '';
  u = u.replace(/\/+$/, '');
  if (u === 'https://api.deepseek.com') u = 'https://api.deepseek.com/v1';
  return u;
}

export const handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, body: '' };
  }
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  try {
    const body = JSON.parse(event.body || '{}');
    const userBaseUrl = normalizeBaseUrl(body.baseUrl);
    const userModel = String(body.model || '').trim();
    const userKey = String(body.apiKey || '').trim();
    const messages = Array.isArray(body.messages) ? body.messages : [];

    const baseUrl = userBaseUrl || normalizeBaseUrl(process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1');
    const model = userModel || process.env.DEEPSEEK_MODEL || 'deepseek-chat';
    const apiKey = userKey || process.env.DEEPSEEK_API_KEY || '';

    if (!baseUrl) return { statusCode: 400, body: JSON.stringify({ error: 'Missing baseUrl' }) };
    if (!model) return { statusCode: 400, body: JSON.stringify({ error: 'Missing model' }) };
    if (!apiKey) return { statusCode: 400, body: JSON.stringify({ error: 'Missing apiKey' }) };
    if (messages.length === 0) return { statusCode: 400, body: JSON.stringify({ error: 'Missing messages' }) };

    const upstream = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({ model, messages, stream: false, temperature: 0.2 })
    });

    const text = await upstream.text();
    if (!upstream.ok) {
      return { statusCode: upstream.status, body: text };
    }

    const data = JSON.parse(text);
    const out = data?.choices?.[0]?.message?.content ?? '';
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: out, raw: data })
    };
  } catch (e) {
    return { statusCode: 500, body: JSON.stringify({ error: e?.message || String(e) }) };
  }
};
