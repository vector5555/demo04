/**
 * 路由访问控制组件
 * 
 * 功能：
 * - 用于保护需要登录才能访问的路由
 * - 检查用户是否已登录（通过验证 cookie 中的 token）
 * - 未登录用户将被重定向到登录页面
 * - 保存用户尝试访问的原始路径，便于登录后跳转回原页面
 * 
 * 参数说明：
 * @param {ReactNode} children - 需要保护的路由组件
 * 
 * 使用示例：
 * <PrivateRoute>
 *   <ProtectedComponent />
 * </PrivateRoute>
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import Cookies from 'js-cookie';

const PrivateRoute = ({ children }) => {
  const location = useLocation();
  const token = Cookies.get('token');
  
  console.log('PrivateRoute checking token:', token); // 添加调试日志
  
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
};

export default PrivateRoute;