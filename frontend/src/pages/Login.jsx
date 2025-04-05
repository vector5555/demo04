import React, { useState } from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import axios from '../utils/axios';
import '../styles/Login.css';

function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/login', values);
      console.log('登录响应:', response); // 添加日志查看响应数据结构
      console.log('响应数据:', response.data);
      console.log('响应状态:', response.status);
      console.log('响应数据内容:', response.data);
      
      if (response.status === 'success') {
        const { token, username, user_id, permissions } = response.data;
        console.log('解析的权限信息:', permissions);
        
        // 存储token和用户信息
        Cookies.set('token', token, { 
          expires: 1,
          path: '/',
          sameSite: 'Lax'
        });
        Cookies.set('username', username || values.username);
        localStorage.setItem('user_id', user_id);
        
        // 存储权限信息
        if (permissions) {
          console.log('存储权限信息到localStorage');
          localStorage.setItem('permissions', JSON.stringify(permissions));
        } else {
          console.log('没有权限信息可存储');
        }
        
        // 存储角色信息
        if (response.data.roles) {
          console.log('存储角色信息到localStorage');
          localStorage.setItem('roles', JSON.stringify(response.data.roles));
        } else {
          console.log('没有角色信息可存储');
        }
        
        message.success('登录成功');
        setTimeout(() => {
          navigate('/dashboard', { replace: true });
        }, 100);
      } else {
        throw new Error('登录响应格式错误');
      }
    } catch (error) {
      console.error('登录请求错误:', error);
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Card title="登录" style={{ width: 400 }}>
        <Form onFinish={handleLogin}>
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="用户名" />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="密码" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

export default Login;