import React from 'react';
import { Layout, Menu } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import {
  UserOutlined,
  TeamOutlined,
  DashboardOutlined,
  LogoutOutlined,
} from '@ant-design/icons';

const { Header, Content, Sider } = Layout;

const BasicLayout = () => {
  const navigate = useNavigate();

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
        }
      ]
    }
  ];

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: '20px' }}>自然语言查询系统</div>
        <div onClick={handleLogout} style={{ color: 'white', cursor: 'pointer' }}>
          <LogoutOutlined /> 退出
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