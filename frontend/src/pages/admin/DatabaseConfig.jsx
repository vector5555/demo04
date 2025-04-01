import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, message, Alert } from 'antd';
import axios from '../../utils/axios';

const DatabaseConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testSuccess, setTestSuccess] = useState(false);
  const [configExists, setConfigExists] = useState(false);

  // 获取现有配置
  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/database/config');
      
      if (response.status === 'success' && response.data) {
        const config = response.data;
        form.setFieldsValue({
          host: config.host || '',
          port: config.port || 3306,
          username: config.username || '',
          password: config.password || ''
        });
        setConfigExists(true);
        message.success('已加载现有数据库配置');
      }
    } catch (error) {
      console.error('获取数据库配置失败:', error);
      // 如果是404错误，说明配置不存在，这是正常的
      if (error.response?.status !== 404) {
        message.error('获取数据库配置失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 测试连接
  const handleTestConnection = async () => {
    try {
      // 先验证表单
      await form.validateFields();
      
      const values = form.getFieldsValue();
      setLoading(true);
      
      const response = await axios.post('/database/test-connection', values);
      
      if (response.status === 'success') {
        message.success('数据库连接测试成功');
        setTestSuccess(true);
      } else {
        message.error('数据库连接测试失败');
        setTestSuccess(false);
      }
    } catch (error) {
      console.error('测试连接失败:', error);
      message.error('测试连接失败: ' + (error.response?.data?.detail || error.message));
      setTestSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  // 保存配置
  const handleSaveConfig = async () => {
    try {
      // 先验证表单
      await form.validateFields();
      
      if (!testSuccess) {
        message.warning('请先测试连接成功后再保存');
        return;
      }
      
      const values = form.getFieldsValue();
      setLoading(true);
      
      const response = await axios.post('/database/config', values);
      
      if (response.status === 'success') {
        message.success('数据库配置保存成功');
        setConfigExists(true);
      } else {
        message.error('数据库配置保存失败');
      }
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('保存配置失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取现有配置
  useEffect(() => {
    fetchConfig();
  }, []);

  return (
    <Card title="全局数据库连接配置">
      {configExists && (
        <Alert
          message="已存在数据库配置"
          description="修改配置可能会影响现有的数据权限设置，请谨慎操作。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          host: 'localhost',
          port: 3306,
          username: 'root',
          password: ''
        }}
      >
        <Form.Item
          label="主机地址"
          name="host"
          rules={[{ required: true, message: '请输入主机地址' }]}
        >
          <Input placeholder="localhost" />
        </Form.Item>
        
        <Form.Item
          label="端口"
          name="port"
          rules={[{ required: true, message: '请输入端口号' }]}
        >
          <Input type="number" placeholder="3306" />
        </Form.Item>
        
        <Form.Item
          label="用户名"
          name="username"
          rules={[{ required: true, message: '请输入用户名' }]}
        >
          <Input placeholder="root" />
        </Form.Item>
        
        <Form.Item
          label="密码"
          name="password"
          rules={[{ required: true, message: '请输入密码' }]}
        >
          <Input.Password />
        </Form.Item>
        
        <Form.Item>
          <Button 
            type="primary" 
            onClick={handleTestConnection} 
            loading={loading}
            style={{ marginRight: 8 }}
          >
            测试连接
          </Button>
          
          <Button 
            type="primary" 
            onClick={handleSaveConfig} 
            loading={loading}
            disabled={!testSuccess}
          >
            保存配置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default DatabaseConfig;