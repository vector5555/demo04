import React from 'react';
import { Layout, Menu } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';  // 添加 Cookies 导入
import {
  UserOutlined,
  TeamOutlined,
  DashboardOutlined,
  LogoutOutlined,
  DatabaseOutlined, // 添加数据库图标
  ApiOutlined, // 添加API图标用于LLM配置
} from '@ant-design/icons';

const { Header, Content, Sider } = Layout;

const BasicLayout = () => {
  const navigate = useNavigate();
  const username = Cookies.get('username') || '未登录';  // 从 Cookies 获取用户名

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '查询面板',
      onClick: () => navigate('/dashboard')
    },
    {
      key: 'admin',
      icon: <TeamOutlined />,
      label: '系统管理',
      children: [
        {
          key: 'users',
          icon: <UserOutlined />,
          label: '用户管理',
          onClick: () => navigate('/admin/users')
        },
        {
          key: 'roles',
          icon: <TeamOutlined />,
          label: '角色管理',
          onClick: () => navigate('/admin/roles')
        },
        {
          key: 'role-user',
          icon: <TeamOutlined />,
          label: '用户角色分配',
          onClick: () => navigate('/admin/role-user')
        },
        {
          key: 'role-permissions',
          icon: <TeamOutlined />,
          label: '权限配置',
          onClick: () => navigate('/admin/role-permissions')
        },
        // 添加数据库配置菜单项
        {
          key: 'database-config',
          icon: <DatabaseOutlined />,
          label: '数据库配置',
          onClick: () => navigate('/admin/database-config')
        },
        // 添加LLM配置菜单项
        {
          key: 'llm-config',
          icon: <ApiOutlined />,
          label: 'LLM配置',
          onClick: () => navigate('/admin/llm-config')
        }
      ]
    }
  ];

  const handleLogout = () => {
    Cookies.remove('token');
    Cookies.remove('username');  // 退出时同时清除用户名
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: '20px' }}>自然语言查询系统</div>
        <div style={{ display: 'flex', alignItems: 'center', color: 'white' }}>
          <span style={{ marginRight: '20px' }}>当前用户: {username}</span>
          <div onClick={handleLogout} style={{ cursor: 'pointer' }}>
            <LogoutOutlined /> 退出
          </div>
        </div>
      </Header>
      <Layout>
        <Sider width={200}>
          <Menu
            mode="inline"
            defaultSelectedKeys={['dashboard']}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 280 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default BasicLayout;