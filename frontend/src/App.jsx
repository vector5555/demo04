/**
 * 应用程序主入口组件
 * 
 * 功能：
 * - 配置应用程序的路由系统
 * - 实现基础布局和页面组织
 * - 集成权限控制路由保护
 * 
 * 路由结构：
 * - /login: 登录页面
 * - /: 主布局（需要登录）
 *   - /dashboard: 仪表盘
 *   - /admin: 管理模块
 *     - /users: 用户管理
 *     - /roles: 角色管理
 *     - /role-user: 角色用户管理
 *     - /role-permissions: 角色权限列表
 *     - /role-permission/:roleId: 角色权限配置
 *     - /database-config: 数据库配置
 *     - /llm-config: LLM配置
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import BasicLayout from './layouts/BasicLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/admin/Users';
import Roles from './pages/admin/Roles';
import RoleUser from './pages/admin/RoleUser';
import RolePermission from './pages/admin/RolePermission';
import RolePermissionList from './pages/admin/RolePermissionList';
import DatabaseConfig from './pages/admin/DatabaseConfig';
import LLMConfig from './pages/admin/LLMConfig'; // 导入LLM配置组件
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><BasicLayout /></PrivateRoute>}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="admin">
            <Route path="users" element={<Users />} />
            <Route path="roles" element={<Roles />} />
            <Route path="role-user" element={<RoleUser />} />
            <Route path="role-permissions" element={<RolePermissionList />} />
            <Route path="role-permission/:roleId" element={<RolePermission />} />
            <Route path="database-config" element={<DatabaseConfig />} />
            <Route path="llm-config" element={<LLMConfig />} /> {/* 添加LLM配置路由 */}
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;