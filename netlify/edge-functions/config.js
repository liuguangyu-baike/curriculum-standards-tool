const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
};

export default async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  return new Response(JSON.stringify({
    baseUrl: Deno.env.get('DEEPSEEK_BASE_URL') || 'https://api.deepseek.com/v1',
    model: Deno.env.get('DEEPSEEK_MODEL') || 'deepseek-chat',
    apiKey: Deno.env.get('DEEPSEEK_API_KEY') || ''
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
};
