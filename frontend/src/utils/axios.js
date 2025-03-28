import axios from 'axios';
import Cookies from 'js-cookie';
import { message } from 'antd';

// 创建 axios 实例
const instance = axios.create({
  baseURL: 'http://localhost:8000'
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
  response => response,
  error => {
    if (error.response?.status === 401) {
      Cookies.remove('token');
      window.location.href = '/login';
      message.error('登录已过期，请重新登录');
    }
    return Promise.reject(error);
  }
);

export default instance;