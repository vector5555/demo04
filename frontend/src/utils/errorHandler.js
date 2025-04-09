/**
 * 全局错误处理工具
 * 用于统一处理前端错误提示，提供友好的用户体验
 */

import { message, notification } from 'antd';

// 错误类型枚举
export const ErrorType = {
  NETWORK: 'network',    // 网络错误
  AUTH: 'auth',          // 认证错误
  PERMISSION: 'permission', // 权限错误
  VALIDATION: 'validation', // 数据验证错误
  SERVER: 'server',      // 服务器错误
  SQL: 'sql',            // SQL错误
  UNKNOWN: 'unknown'     // 未知错误
};

// 错误码映射表
const errorCodeMap = {
  400: { type: ErrorType.VALIDATION, title: '请求错误' },
  401: { type: ErrorType.AUTH, title: '未授权' },
  403: { type: ErrorType.PERMISSION, title: '权限不足' },
  404: { type: ErrorType.VALIDATION, title: '资源不存在' },
  422: { type: ErrorType.VALIDATION, title: '数据验证失败' },
  500: { type: ErrorType.SERVER, title: '服务器错误' },
  502: { type: ErrorType.NETWORK, title: '网关错误' },
  503: { type: ErrorType.SERVER, title: '服务不可用' },
  504: { type: ErrorType.NETWORK, title: '网关超时' }
};

/**
 * 获取错误类型
 * @param {Error} error - 错误对象
 * @returns {string} 错误类型
 */
const getErrorType = (error) => {
  // 网络错误
  if (error.message === 'Network Error') {
    return ErrorType.NETWORK;
  }

  // 响应错误
  if (error.response) {
    const statusCode = error.response.status;
    return errorCodeMap[statusCode]?.type || ErrorType.UNKNOWN;
  }

  // 请求超时
  if (error.message && error.message.includes('timeout')) {
    return ErrorType.NETWORK;
  }

  // SQL错误
  if (error.response?.data?.detail && 
      (error.response.data.detail.includes('SQL') || 
       error.response.data.detail.includes('query'))) {
    return ErrorType.SQL;
  }

  return ErrorType.UNKNOWN;
};

/**
 * 获取友好的错误消息
 * @param {Error} error - 错误对象
 * @returns {string} 友好的错误消息
 */
const getFriendlyErrorMessage = (error) => {
  // 检查响应中的错误详情
  const responseData = error.response?.data;
  
  // 处理后端返回的详细错误信息
  if (responseData) {
    // 优先使用detail字段
    if (responseData.detail) {
      return responseData.detail;
    }
    
    // 其次使用message字段
    if (responseData.message) {
      return responseData.message;
    }
    
    // 再次使用error字段
    if (responseData.error) {
      return responseData.error;
    }
  }

  // 如果没有详细信息，返回通用错误消息
  return error.message || '发生未知错误，请稍后再试';
};

/**
 * 处理错误并显示适当的提示
 * @param {Error} error - 错误对象
 * @param {Object} options - 配置选项
 * @param {boolean} options.showNotification - 是否显示通知，默认为false
 * @param {Function} options.onAuthError - 授权错误回调
 * @returns {void}
 */
export const handleError = (error, options = {}) => {
  console.error('API错误:', error);
  
  const errorType = getErrorType(error);
  const errorMessage = getFriendlyErrorMessage(error);
  
  // 默认使用message提示
  if (!options.showNotification) {
    message.error(errorMessage);
    return;
  }
  
  // 使用notification提供更详细的错误提示
  const statusCode = error.response?.status;
  const errorInfo = errorCodeMap[statusCode] || { title: '错误' };
  
  notification.error({
    message: errorInfo.title,
    description: errorMessage,
    duration: 4.5,
  });
  
  // 处理授权错误，如登录过期
  if (errorType === ErrorType.AUTH && options.onAuthError) {
    options.onAuthError();
  }
};

/**
 * 处理SQL错误并提供修改建议
 * @param {Error} error - SQL错误对象
 * @returns {Object} 包含错误信息和修改建议
 */
export const handleSqlError = (error) => {
  const errorMessage = getFriendlyErrorMessage(error);
  let suggestion = '';
  
  // 根据错误类型提供建议
  const responseData = error.response?.data;
  const detail = responseData?.detail || '';
  
  if (detail.includes('syntax error')) {
    suggestion = '请检查SQL语法是否正确，特别是关键字、括号和引号的使用';
  } else if (detail.includes('table') && (detail.includes('not found') || detail.includes('not exist'))) {
    suggestion = '请检查表名是否正确，或者您可能没有访问该表的权限';
  } else if (detail.includes('column') && (detail.includes('not found') || detail.includes('not exist'))) {
    suggestion = '请检查字段名是否正确，或者您可能没有访问该字段的权限';
  } else if (detail.includes('permission denied')) {
    suggestion = '您没有执行此操作的权限，请联系管理员申请相应权限';
  }
  
  // 扩展原始错误对象，而不是返回新对象
  error.errorMessage = errorMessage;
  error.suggestion = suggestion || '请检查您的查询语句是否正确';
  
  return error;
};

export default {
  handleError,
  handleSqlError,
  ErrorType
};