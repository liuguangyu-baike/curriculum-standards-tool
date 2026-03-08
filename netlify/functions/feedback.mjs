// Netlify Function 版本：仅支持 JSON 提交（不含图片附件）
// 图片附件功能需要独立的文件服务，Netlify Functions 暂不支持 multipart

export const handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, body: '' };
  }
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  try {
    const body = JSON.parse(event.body || '{}');
    const { name, email, text } = body;

    if (!text) {
      return { statusCode: 400, body: JSON.stringify({ error: '反馈内容不能为空' }) };
    }

    const smtpHost = process.env.SMTP_HOST || 'smtp.qq.com';
    const smtpUser = process.env.SMTP_USER || '';
    const smtpPass = process.env.SMTP_PASS || '';

    if (!smtpUser || !smtpPass) {
      console.warn('[反馈] SMTP 未配置，反馈内容：', { name, email, text });
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true, message: '反馈已收到（邮件通知暂未配置）' })
      };
    }

    // 使用 fetch 调用 SMTP 需要额外库，这里用 nodemailer 动态 import
    const nodemailer = await import('nodemailer');
    const transporter = nodemailer.default.createTransport({
      host: smtpHost,
      port: Number(process.env.SMTP_PORT || 587),
      secure: Number(process.env.SMTP_PORT) === 465,
      auth: { user: smtpUser, pass: smtpPass }
    });

    await transporter.sendMail({
      from: smtpUser,
      to: process.env.FEEDBACK_TO || 'liuguangyu@kanyun.com',
      subject: `[课标工具反馈] ${name || '匿名用户'} - ${new Date().toLocaleDateString('zh-CN')}`,
      html: `<p><strong>用户：</strong>${name || '匿名'}</p>
             <p><strong>邮箱：</strong>${email || '未提供'}</p>
             <p><strong>内容：</strong></p>
             <pre style="background:#f5f5f5;padding:12px">${text}</pre>`
    });

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: true, message: '反馈已成功提交' })
    };
  } catch (e) {
    console.error('[反馈] 失败:', e);
    return { statusCode: 500, body: JSON.stringify({ error: '提交失败', details: e.message }) };
  }
};
