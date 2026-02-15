// 智能匹配功能模块

// 注意：智能匹配的主要逻辑已在browser.js的handleMatch函数中实现
// 本文件提供一些辅助函数和配置

// 匹配配置
const matchConfig = {
  // 每次匹配发送的课标摘要最大长度
  maxSummaryLength: 200,

  // 匹配超时时间（毫秒）
  timeout: 30000,

  // 是否显示详细日志
  verbose: true
};

// 准备课标摘要数据
function prepareStandardsSummary() {
  if (!standardsData || !standardsData.allStandards) {
    console.error('课标数据未加载');
    return [];
  }

  return standardsData.allStandards.map(item => ({
    id: item.id,
    source: item.source,
    grade_band: item.grade_band,
    topic: item.topic,
    text: item.text.substring(0, matchConfig.maxSummaryLength)
  }));
}

// 验证匹配查询
function validateMatchQuery(query) {
  if (!query || typeof query !== 'string') {
    return {
      valid: false,
      error: '请输入查询内容'
    };
  }

  const trimmedQuery = query.trim();

  if (trimmedQuery.length === 0) {
    return {
      valid: false,
      error: '查询内容不能为空'
    };
  }

  if (trimmedQuery.length < 5) {
    return {
      valid: false,
      error: '查询内容过短，请至少输入5个字符'
    };
  }

  if (trimmedQuery.length > 1000) {
    return {
      valid: false,
      error: '查询内容过长，请控制在1000字符以内'
    };
  }

  return {
    valid: true,
    query: trimmedQuery
  };
}

// 处理匹配结果
function processMatchResults(apiResponse, allStandards) {
  if (!apiResponse || !apiResponse.matches) {
    console.error('API响应格式错误');
    return [];
  }

  const matches = apiResponse.matches;

  if (!Array.isArray(matches)) {
    console.error('匹配结果不是数组');
    return [];
  }

  // 将匹配结果与完整课标数据关联
  const processedMatches = matches
    .map(match => {
      if (!match.id) {
        console.warn('匹配结果缺少ID:', match);
        return null;
      }

      const item = allStandards.find(s => s.id === match.id);

      if (!item) {
        console.warn('未找到课标条目:', match.id);
        return null;
      }

      return {
        item: item,
        reason: match.reason || '(无匹配理由)'
      };
    })
    .filter(match => match !== null);

  if (matchConfig.verbose) {
    console.log('处理后的匹配结果:', processedMatches.length, '条');
  }

  return processedMatches;
}

// 格式化匹配理由（可选：添加一些格式化逻辑）
function formatMatchReason(reason) {
  if (!reason) return '(无匹配理由)';

  // 移除多余空格
  let formatted = reason.trim().replace(/\s+/g, ' ');

  // 确保以句号结尾（如果还没有标点）
  if (!/[。！？.!?]$/.test(formatted)) {
    formatted += '。';
  }

  return formatted;
}

// 获取匹配统计信息
function getMatchStatistics(matchResults) {
  if (!matchResults || matchResults.length === 0) {
    return {
      total: 0,
      bySource: {},
      byGrade: {},
      byDomain: {}
    };
  }

  const stats = {
    total: matchResults.length,
    bySource: {},
    byGrade: {},
    byDomain: {}
  };

  matchResults.forEach(match => {
    const item = match.item;

    // 按来源统计
    if (item.source) {
      stats.bySource[item.source] = (stats.bySource[item.source] || 0) + 1;
    }

    // 按年级统计
    if (item.grade_band) {
      stats.byGrade[item.grade_band] = (stats.byGrade[item.grade_band] || 0) + 1;
    }

    // 按领域统计
    if (item.domain) {
      stats.byDomain[item.domain] = (stats.byDomain[item.domain] || 0) + 1;
    }
  });

  return stats;
}

// 匹配结果排序（按相关度、年级等）
function sortMatchResults(matchResults, sortBy = 'default') {
  if (!matchResults || matchResults.length === 0) {
    return [];
  }

  const sorted = [...matchResults];

  switch (sortBy) {
    case 'grade':
      // 按年级排序
      const gradeOrder = ['K', '1-2', '3-4', '5-6', 'MS', 'HS'];
      sorted.sort((a, b) => {
        const indexA = gradeOrder.indexOf(a.item.grade_band);
        const indexB = gradeOrder.indexOf(b.item.grade_band);
        return indexA - indexB;
      });
      break;

    case 'source':
      // 按来源排序
      sorted.sort((a, b) => a.item.source.localeCompare(b.item.source));
      break;

    case 'default':
    default:
      // 默认保持API返回的顺序（已按相关度排序）
      break;
  }

  return sorted;
}

// 导出函数供其他模块使用
if (typeof window !== 'undefined') {
  window.matchConfig = matchConfig;
  window.prepareStandardsSummary = prepareStandardsSummary;
  window.validateMatchQuery = validateMatchQuery;
  window.processMatchResults = processMatchResults;
  window.formatMatchReason = formatMatchReason;
  window.getMatchStatistics = getMatchStatistics;
  window.sortMatchResults = sortMatchResults;
}
