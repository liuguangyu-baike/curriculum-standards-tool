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
    const { name, email, text } = body;

    if (!text) return json({ error: '反馈内容不能为空' }, 400);

    // Edge Functions 不支持 nodemailer，记录反馈内容到日志
    console.log('[反馈]', JSON.stringify({ name, email, text, time: new Date().toISOString() }));

    return json({ success: true, message: '反馈已收到' });
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
