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

export default async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405, headers: corsHeaders });
  }

  try {
    const body = await request.json();
    const userBaseUrl = normalizeBaseUrl(body.baseUrl);
    const userModel = String(body.model || '').trim();
    const userKey = String(body.apiKey || '').trim();
    const messages = Array.isArray(body.messages) ? body.messages : [];

    const baseUrl = userBaseUrl || normalizeBaseUrl(Deno.env.get('DEEPSEEK_BASE_URL') || 'https://api.deepseek.com/v1');
    const model = userModel || Deno.env.get('DEEPSEEK_MODEL') || 'deepseek-chat';
    const apiKey = userKey || Deno.env.get('DEEPSEEK_API_KEY') || '';

    if (!baseUrl) return json({ error: 'Missing baseUrl' }, 400);
    if (!model) return json({ error: 'Missing model' }, 400);
    if (!apiKey) return json({ error: 'Missing apiKey' }, 400);
    if (messages.length === 0) return json({ error: 'Missing messages' }, 400);

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
      return new Response(text, { status: upstream.status, headers: corsHeaders });
    }

    const data = JSON.parse(text);
    const out = data?.choices?.[0]?.message?.content ?? '';
    return json({ text: out, raw: data });
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
