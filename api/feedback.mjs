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
    const { name, email, text } = body;

    if (!text) {
      return res.status(400).json({ error: '反馈内容不能为空' });
    }

    const smtpHost = process.env.SMTP_HOST || 'smtp.qq.com';
    const smtpUser = process.env.SMTP_USER || '';
    const smtpPass = process.env.SMTP_PASS || '';

    if (!smtpUser || !smtpPass) {
      console.warn('[反馈] SMTP 未配置，反馈内容：', { name, email, text });
      return res.status(200).json({ success: true, message: '反馈已收到（邮件通知暂未配置）' });
    }

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

    return res.status(200).json({ success: true, message: '反馈已成功提交' });
  } catch (e) {
    console.error('[反馈] 失败:', e);
    return res.status(500).json({ error: '提交失败', details: e.message });
  }
}
