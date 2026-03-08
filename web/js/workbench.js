// AI工作台功能模块

// 意图prompt模板
const intentPrompts = {
  compare: `请对比分析这些课标条目，重点关注：
1. 共性：这些条目共同强调什么核心概念或能力？
2. 差异：不同来源/年级的条目在难度、侧重点上有什么区别？
3. 进阶关系：从低年级到高年级，学习目标如何递进？

请用结构化的方式呈现分析结果。`,

  extract: `请提炼这些课标条目的核心要素：
1. 上位概念：这些条目指向什么更抽象的科学大概念？
2. 能力进阶线索：从这些条目中能看出什么能力培养的递进路径？
3. 关键术语：哪些科学术语是核心的、必须掌握的？

请用清晰的层级结构呈现。`,

  knowledge: `基于这些课标条目，请推荐相关的科学知识内容：
1. 核心知识点：需要讲解哪些基础概念和原理？
2. 趣味事实：有什么有趣的科学现象或历史故事可以引入？
3. 生活联系：如何将这些知识与学生的日常经验联系起来？
4. 拓展阅读：推荐相关的科普材料或资源。

请提供具体、可操作的建议。`,

  activity: `基于这些课标条目，请设计教学活动：
1. 实验探究：推荐什么实验或探究活动？包括材料、步骤概要。
2. 观察记录：设计什么观察任务或数据收集活动？
3. 讨论思考：提出什么问题引导学生思考？
4. 动手制作：有什么工程设计或制作项目适合？

请考虑活动的可行性和安全性。`
};

// 初始化工作台
function initWorkbench() {
  console.log('初始化AI工作台...');

  // 绑定意图按钮
  document.querySelectorAll('.intent-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const intent = btn.dataset.intent;
      handleIntentClick(intent);
    });
  });

  // 绑定发送按钮
  const sendBtn = document.getElementById('chat-send');
  const chatInput = document.getElementById('chat-input');

  if (sendBtn && chatInput) {
    sendBtn.addEventListener('click', () => {
      sendMessage();
    });

    // 支持回车发送
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  console.log('AI工作台初始化完成');
}

// 处理意图按钮点击
function handleIntentClick(intent) {
  console.log('用户点击意图:', intent);

  // 检查是否有选中的条目
  if (appState.selectedItems.size === 0) {
    alert('请先在浏览器中选择课标条目');
    return;
  }

  // 获取对应的prompt
  const prompt = intentPrompts[intent];
  if (!prompt) {
    console.error('未找到意图prompt:', intent);
    return;
  }

  // 发送消息
  sendMessageWithContext(prompt);
}

// 发送消息（不带上下文）
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();

  if (!message) {
    return;
  }

  // 清空输入框
  input.value = '';

  // 发送消息（带上下文）
  await sendMessageWithContext(message);
}

// 发送消息（带课标上下文）
async function sendMessageWithContext(userMessage) {
  // 检查是否有选中的条目
  if (appState.selectedItems.size === 0) {
    alert('请先在浏览器中选择课标条目');
    return;
  }

  // 显示用户消息
  addChatMessage('user', userMessage);

  // 显示加载状态
  showChatLoading();
  disableChatInput(true);

  try {
    // 构建包含课标上下文的完整prompt
    const contextPrompt = buildContextPrompt(userMessage);

    // 调用AI API
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'system',
            content: '你是一个课程标准分析专家。请基于提供的课标条目进行分析，回答要结构化、具体、有深度。'
          },
          {
            role: 'user',
            content: contextPrompt
          }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`);
    }

    const data = await response.json();
    const assistantMessage = data.text || '抱歉，未能获取回复';

    // 显示AI回复
    addChatMessage('assistant', assistantMessage);

    // 保存到对话历史
    appState.chatHistory.push(
      { role: 'user', content: userMessage },
      { role: 'assistant', content: assistantMessage }
    );

  } catch (error) {
    console.error('发送消息失败:', error);
    addChatMessage('assistant', `发生错误: ${error.message}`);
  } finally {
    hideChatLoading();
    disableChatInput(false);
  }
}

// 构建包含课标上下文的prompt
function buildContextPrompt(userMessage) {
  const selectedItems = getSelectedItems();

  if (selectedItems.length === 0) {
    return userMessage;
  }

  // 构建课标上下文
  const contextLines = selectedItems.map((item, index) => {
    return `【课标${index + 1}】
ID: ${item.id}
来源: ${item.source}
年级: ${item.grade_band}
主题: ${item.topic}
内容: ${item.text}`;
  });

  const fullPrompt = `${contextLines.join('\n\n')}

---

【用户指令】
${userMessage}`;

  return fullPrompt;
}

// 添加聊天消息
function addChatMessage(role, content) {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  // 移除欢迎消息
  const welcome = messagesContainer.querySelector('.chat-welcome');
  if (welcome) {
    welcome.remove();
  }

  // 创建消息元素
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${role}`;

  // 处理换行和格式
  const formattedContent = formatMessageContent(content);
  messageDiv.innerHTML = formattedContent;

  messagesContainer.appendChild(messageDiv);

  // 滚动到底部
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 格式化消息内容（支持基础Markdown）
function formatMessageContent(content) {
  // 简单的Markdown渲染
  let formatted = content;

  // 转义HTML
  const div = document.createElement('div');
  div.textContent = formatted;
  formatted = div.innerHTML;

  // 换行
  formatted = formatted.replace(/\n/g, '<br>');

  // 粗体 **text**
  formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // 列表
  formatted = formatted.replace(/^- (.+)$/gm, '• $1');

  return formatted;
}

// 禁用/启用聊天输入
function disableChatInput(disabled) {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');

  if (input) input.disabled = disabled;
  if (sendBtn) sendBtn.disabled = disabled;
}

// 清空对话
function clearChat() {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  messagesContainer.innerHTML = `
    <div class="chat-welcome">
      <p>👋 欢迎使用AI工作台</p>
      <p>选择意图按钮或直接输入问题，我将基于您选中的课标条目提供分析</p>
    </div>
  `;

  appState.chatHistory = [];
}

// 显示打字指示器（追加到对话底部）
function showChatLoading() {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  // 避免重复添加
  if (messagesContainer.querySelector('.chat-typing-indicator')) return;

  const indicator = document.createElement('div');
  indicator.className = 'chat-message assistant chat-typing-indicator';
  indicator.innerHTML = '<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>';
  messagesContainer.appendChild(indicator);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 隐藏打字指示器
function hideChatLoading() {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  const indicator = messagesContainer.querySelector('.chat-typing-indicator');
  if (indicator) indicator.remove();
}

// 导出函数供其他模块使用
if (typeof window !== 'undefined') {
  window.initWorkbench = initWorkbench;
  window.clearChat = clearChat;
  window.addChatMessage = addChatMessage;
}

// 监听数据加载完成后初始化
document.addEventListener('dataLoaded', () => {
  initWorkbench();
});
