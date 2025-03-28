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
      // 检查响应数据结构
      if (response?.token) {
        Cookies.set('token', response.token, { 
          expires: 1,
          path: '/',
          sameSite: 'Lax'
        });
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
  }; // 删除这里多余的分号

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