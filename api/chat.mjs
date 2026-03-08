function normalizeBaseUrl(baseUrl) {
  let u = String(baseUrl || '').trim();
  if (!u) return '';
  u = u.replace(/\/+$/, '');
  if (u === 'https://api.deepseek.com') u = 'https://api.deepseek.com/v1';
  return u;
}

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
    const userBaseUrl = normalizeBaseUrl(body.baseUrl);
    const userModel = String(body.model || '').trim();
    const userKey = String(body.apiKey || '').trim();
    const messages = Array.isArray(body.messages) ? body.messages : [];

    const baseUrl = userBaseUrl || normalizeBaseUrl(process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1');
    const model = userModel || process.env.DEEPSEEK_MODEL || 'deepseek-chat';
    const apiKey = userKey || process.env.DEEPSEEK_API_KEY || '';

    if (!baseUrl) return res.status(400).json({ error: 'Missing baseUrl' });
    if (!model) return res.status(400).json({ error: 'Missing model' });
    if (!apiKey) return res.status(400).json({ error: 'Missing apiKey' });
    if (messages.length === 0) return res.status(400).json({ error: 'Missing messages' });

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
      return res.status(upstream.status).send(text);
    }

    const data = JSON.parse(text);
    const out = data?.choices?.[0]?.message?.content ?? '';
    return res.status(200).json({ text: out, raw: data });
  } catch (e) {
    return res.status(500).json({ error: e?.message || String(e) });
  }
}
