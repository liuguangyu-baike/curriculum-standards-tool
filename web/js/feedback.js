// 反馈页面功能模块

let selectedImages = []; // 存储选中的图片文件

// 初始化反馈页面
function initFeedback() {
  console.log('初始化反馈页面...');

  const form = document.getElementById('feedback-form');
  const fileInput = document.getElementById('feedback-images');
  const imagePreview = document.getElementById('image-preview');

  // 绑定表单提交
  if (form) {
    form.addEventListener('submit', handleFeedbackSubmit);
  }

  // 绑定文件选择
  if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
  }

  // 绑定拖拽上传
  const uploadLabel = document.querySelector('.file-upload-label');
  if (uploadLabel) {
    uploadLabel.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadLabel.style.borderColor = 'var(--accent)';
    });

    uploadLabel.addEventListener('dragleave', () => {
      uploadLabel.style.borderColor = '';
    });

    uploadLabel.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadLabel.style.borderColor = '';
      const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
      handleFiles(files);
    });
  }

  console.log('反馈页面初始化完成');
}

// 处理文件选择
function handleFileSelect(e) {
  const files = Array.from(e.target.files);
  handleFiles(files);
}

// 处理文件
function handleFiles(files) {
  // 限制最多3张图片
  const remainingSlots = 3 - selectedImages.length;
  const filesToAdd = files.slice(0, remainingSlots);

  filesToAdd.forEach(file => {
    if (file.size > 10 * 1024 * 1024) {
      alert('图片大小不能超过 10MB');
      return;
    }

    selectedImages.push(file);

    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
      addImagePreview(e.target.result, selectedImages.length - 1);
    };
    reader.readAsDataURL(file);
  });

  if (files.length > remainingSlots) {
    alert('最多只能上传 3 张图片');
  }
}

// 添加图片预览
function addImagePreview(src, index) {
  const preview = document.getElementById('image-preview');
  if (!preview) return;

  const item = document.createElement('div');
  item.className = 'preview-item';
  item.dataset.index = index;

  item.innerHTML = `
    <img src="${src}" alt="预览">
    <button type="button" class="preview-remove" data-index="${index}">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M3 3L9 9M3 9L9 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
  `;

  // 绑定移除按钮
  const removeBtn = item.querySelector('.preview-remove');
  removeBtn.addEventListener('click', () => {
    removeImage(index);
  });

  preview.appendChild(item);
}

// 移除图片
function removeImage(index) {
  selectedImages.splice(index, 1);

  // 重新渲染预览
  const preview = document.getElementById('image-preview');
  if (preview) {
    preview.innerHTML = '';
    selectedImages.forEach((file, i) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        addImagePreview(e.target.result, i);
      };
      reader.readAsDataURL(file);
    });
  }
}

// 处理表单提交
async function handleFeedbackSubmit(e) {
  e.preventDefault();

  const nameInput = document.getElementById('feedback-name');
  const emailInput = document.getElementById('feedback-email');
  const textInput = document.getElementById('feedback-text');

  const name = nameInput ? nameInput.value.trim() : '';
  const email = emailInput ? emailInput.value.trim() : '';
  const text = textInput ? textInput.value.trim() : '';

  if (!text) {
    alert('请填写反馈内容');
    return;
  }

  // 显示加载状态
  const submitBtn = document.querySelector('.submit-button');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `
    <div style="width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
    提交中...
  `;

  try {
    // 构建 FormData
    const formData = new FormData();
    formData.append('name', name || '匿名用户');
    formData.append('email', email);
    formData.append('text', text);

    // 添加图片
    selectedImages.forEach((file, index) => {
      formData.append('images', file);
    });

    // 发送请求
    const response = await fetch('/api/feedback', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`提交失败: ${response.status}`);
    }

    const result = await response.json();
    console.log('反馈提交成功:', result);

    // 显示成功消息
    showFeedbackMessage('success');

    // 重置表单
    document.getElementById('feedback-form').reset();
    selectedImages = [];
    document.getElementById('image-preview').innerHTML = '';

  } catch (error) {
    console.error('反馈提交失败:', error);
    showFeedbackMessage('error', error.message);
  } finally {
    // 恢复按钮
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M14.5 1.5L6.5 9.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M14.5 1.5L10 14.5L6.5 9.5L1.5 6L14.5 1.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      提交反馈
    `;
  }
}

// 显示反馈消息
function showFeedbackMessage(type, errorText = '') {
  const form = document.getElementById('feedback-form');
  const successMsg = document.getElementById('feedback-success');
  const errorMsg = document.getElementById('feedback-error');

  if (type === 'success') {
    form.style.display = 'none';
    successMsg.classList.add('visible');
    errorMsg.classList.remove('visible');

    // 3秒后恢复表单
    setTimeout(() => {
      form.style.display = 'flex';
      successMsg.classList.remove('visible');
    }, 3000);
  } else {
    errorMsg.classList.add('visible');
    if (errorText) {
      document.getElementById('feedback-error-text').textContent = errorText;
    }

    // 3秒后隐藏错误消息
    setTimeout(() => {
      errorMsg.classList.remove('visible');
    }, 3000);
  }
}

// 导出函数供其他模块使用
if (typeof window !== 'undefined') {
  window.initFeedback = initFeedback;
}

// 监听数据加载完成后初始化
document.addEventListener('dataLoaded', () => {
  initFeedback();
});

// 也在 DOM 加载完成后初始化（以防 dataLoaded 未触发）
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，确保其他脚本已加载
    setTimeout(initFeedback, 100);
  });
} else {
  // DOM 已加载，立即初始化
  setTimeout(initFeedback, 100);
}
