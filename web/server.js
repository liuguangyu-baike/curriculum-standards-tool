import 'dotenv/config';
import express from 'express';
import path from 'node:path';
import fs from 'node:fs';
import nodemailer from 'nodemailer';
import multer from 'multer';

const app = express();
app.use(express.json({ limit: '2mb' }));

// 配置文件上传
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('只支持图片格式'));
    }
  }
});

// 配置邮件发送器
const smtpPort = Number(process.env.SMTP_PORT || 587);
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.qq.com',
  port: smtpPort,
  secure: smtpPort === 465, // 465端口使用SSL，587端口使用TLS
  auth: {
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || ''
  }
});

const PORT = Number(process.env.PORT || 8001);

function getDefaultConfig() {
  return {
    baseUrl: process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1',
    model: process.env.DEEPSEEK_MODEL || 'deepseek-chat',
    apiKey: process.env.DEEPSEEK_API_KEY || ''
  };
}

function normalizeBaseUrl(baseUrl) {
  let u = String(baseUrl || '').trim();
  if (!u) return '';
  // remove trailing slash
  u = u.replace(/\/+$/, '');
  // ensure /v1 for OpenAI-compatible if user provides https://api.deepseek.com
  if (u === 'https://api.deepseek.com') u = 'https://api.deepseek.com/v1';
  return u;
}

app.post('/api/chat', async (req, res) => {
  try {
    const body = req.body || {};
    const userBaseUrl = normalizeBaseUrl(body.baseUrl);
    const userModel = String(body.model || '').trim();
    const userKey = String(body.apiKey || '').trim();
    const messages = Array.isArray(body.messages) ? body.messages : [];

    const def = getDefaultConfig();
    const baseUrl = userBaseUrl || normalizeBaseUrl(def.baseUrl);
    const model = userModel || def.model;
    const apiKey = userKey || def.apiKey;

    if (!baseUrl) return res.status(400).json({ error: 'Missing baseUrl' });
    if (!model) return res.status(400).json({ error: 'Missing model' });
    if (!apiKey) return res.status(400).json({ error: 'Missing apiKey (and server default is empty)' });
    if (messages.length === 0) return res.status(400).json({ error: 'Missing messages' });

    const useStream = body.stream === true;
    const url = `${baseUrl}/chat/completions`;
    const upstream = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        messages,
        stream: useStream,
        temperature: 0.2
      })
    });

    if (!upstream.ok) {
      const text = await upstream.text();
      return res.status(upstream.status).send(text);
    }

    if (useStream) {
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      const reader = upstream.body.getReader();
      const push = async () => {
        while (true) {
          const { done, value } = await reader.read();
          if (done) { res.end(); return; }
          res.write(Buffer.from(value));
        }
      };
      return push();
    }

    const text = await upstream.text();
    const data = JSON.parse(text);
    const out = data?.choices?.[0]?.message?.content ?? '';
    return res.json({ text: out, raw: data });
  } catch (e) {
    return res.status(500).json({ error: e?.message || String(e) });
  }
});

// 智能匹配接口
app.post('/api/match', async (req, res) => {
  try {
    const body = req.body || {};
    const { query, standards, baseUrl: userBaseUrl, model: userModel, apiKey: userKey } = body;

    if (!query) return res.status(400).json({ error: 'Missing query' });
    if (!Array.isArray(standards)) return res.status(400).json({ error: 'Missing standards array' });

    const def = getDefaultConfig();
    const finalBaseUrl = normalizeBaseUrl(userBaseUrl) || normalizeBaseUrl(def.baseUrl);
    const finalModel = userModel || def.model;
    const finalKey = userKey || def.apiKey;

    if (!finalBaseUrl) return res.status(400).json({ error: 'Missing baseUrl' });
    if (!finalModel) return res.status(400).json({ error: 'Missing model' });
    if (!finalKey) return res.status(400).json({ error: 'Missing apiKey (and server default is empty)' });

    // 构建匹配prompt
    const systemPrompt = `你是课标匹配专家。用户会描述一个知识点或教学活动,你需要在提供的课标数据库中找到所有相关的课标条目。

要求:
1. 返回JSON格式: {"matches": [{"id": "条目ID", "reason": "匹配理由"}]}
2. 匹配理由需说明该课标与用户描述的关联点
3. 如果用户描述的内容难度超出或低于某课标的年级要求,需在理由中明确指出
4. 按相关度从高到低排序
5. 只返回真正相关的条目,不要为了数量而勉强匹配
6. 如果没有找到相关条目,返回空数组`;

    const userPrompt = `用户输入: ${query}

课标数据库摘要:
${standards.map(s => `ID: ${s.id} | 来源: ${s.source} | 年级: ${s.grade_band} | 主题: ${s.topic} | 内容: ${s.text.substring(0, 100)}...`).join('\n')}

请返回匹配结果JSON。`;

    const url = `${finalBaseUrl}/chat/completions`;
    const upstream = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${finalKey}`
      },
      body: JSON.stringify({
        model: finalModel,
        messages: [
          { role: 'system', content: systemPrompt },
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

    return res.json(result);
  } catch (e) {
    return res.status(500).json({ error: e?.message || String(e) });
  }
});

// 反馈提交接口
app.post('/api/feedback', upload.array('images', 3), async (req, res) => {
  try {
    const { name, email, text } = req.body;
    const images = req.files || [];

    if (!text) {
      return res.status(400).json({ error: '反馈内容不能为空' });
    }

    console.log('[反馈] 收到反馈:', { name, email, textLength: text.length, imageCount: images.length });

    // 构建邮件内容
    const htmlContent = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #3b6fc0; border-bottom: 2px solid #3b6fc0; padding-bottom: 10px;">
          课标工具 - 用户反馈
        </h2>

        <div style="margin: 20px 0;">
          <p><strong>用户称呼：</strong>${name || '匿名用户'}</p>
          <p><strong>联系邮箱：</strong>${email || '未提供'}</p>
          <p><strong>提交时间：</strong>${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}</p>
        </div>

        <div style="background: #f7f6f3; padding: 15px; border-radius: 8px; margin: 20px 0;">
          <h3 style="margin-top: 0; color: #1e2a3a;">反馈内容：</h3>
          <p style="white-space: pre-wrap; line-height: 1.6;">${text}</p>
        </div>

        ${images.length > 0 ? `
          <div style="margin: 20px 0;">
            <h3 style="color: #1e2a3a;">附件图片：</h3>
            <p>本邮件包含 ${images.length} 张图片附件</p>
          </div>
        ` : ''}

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e1e4e8; color: #8892a0; font-size: 12px;">
          <p>此邮件由课标工具反馈系统自动发送</p>
        </div>
      </div>
    `;

    // 准备附件
    const attachments = images.map((file, index) => ({
      filename: `screenshot-${index + 1}.${file.mimetype.split('/')[1]}`,
      content: file.buffer
    }));

    // 发送邮件
    const mailOptions = {
      from: process.env.SMTP_USER || '',
      to: 'liuguangyu@kanyun.com',
      subject: `[课标工具反馈] ${name || '匿名用户'} - ${new Date().toLocaleDateString('zh-CN')}`,
      html: htmlContent,
      attachments: attachments
    };

    await transporter.sendMail(mailOptions);

    console.log('[反馈] 邮件发送成功');
    return res.json({ success: true, message: '反馈已成功提交' });

  } catch (error) {
    console.error('[反馈] 邮件发送失败:', error);
    return res.status(500).json({ error: '提交失败，请稍后重试', details: error.message });
  }
});

// 静态托管：以启动时 cwd 为准（start_server.sh 会 cd 到 web/）
const staticDir = process.cwd();
const indexPath = path.join(staticDir, 'index.html');
if (!fs.existsSync(indexPath)) {
  console.warn('[warn] index.html not found at', indexPath);
} else {
  console.log('[info] serving static from', staticDir);
}
app.use(express.static(staticDir, { index: 'index.html' }));

app.listen(PORT, () => {
  console.log(`NGSS DCI Explorer server running on http://localhost:${PORT}`);
});

