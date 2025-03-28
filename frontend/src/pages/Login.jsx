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
      const { token } = response.data;
      // 确保 token 被正确设置
      Cookies.set('token', token, { 
        expires: 1,
        path: '/',
        sameSite: 'Lax'
      });
      message.success('登录成功');
      // 添加一个小延时确保 cookie 已被设置
      setTimeout(() => {
        navigate('/dashboard', { replace: true });
      }, 100);
    } catch (error) {
      console.error('登录请求错误:', error);
      message.error(error.response?.data?.message || '登录失败');
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