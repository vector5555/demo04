import axios from 'axios';
import Cookies from 'js-cookie';
import { message } from 'antd';
import errorHandler from './errorHandler';

// 创建 axios 实例
const instance = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
});

// 请求拦截器
instance.interceptors.request.use(
  config => {
    const token = Cookies.get('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
instance.interceptors.response.use(
  response => response.data,  // 直接返回响应数据
  error => {
    // 特殊处理401错误（未授权）
    if (error.response?.status === 401) {
      Cookies.remove('token');
      message.error('登录已过期，请重新登录');
      setTimeout(() => {
        window.location.href = '/login';
      }, 1500);
      return Promise.reject(error);
    }
    
    // 使用错误处理工具处理其他错误
    errorHandler.handleError(error);
    
    return Promise.reject(error);
  }
);

export default instance;