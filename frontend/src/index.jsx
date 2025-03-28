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