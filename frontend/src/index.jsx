/**
 * React应用程序入口文件
 * 
 * 功能：
 * - 初始化React应用程序
 * - 配置React严格模式
 * - 将应用程序根组件挂载到DOM
 * 
 * 技术栈：
 * - React 18
 * - ReactDOM
 * - 使用createRoot API进行并发渲染
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
// 修正大小写敏感的导入路径
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);