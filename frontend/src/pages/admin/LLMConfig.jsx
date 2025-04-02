import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Button, message, Spin, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import axios from '../../utils/axios';

const LLMConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);

  useEffect(() => {
    // 加载现有配置
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/llm/config');
      console.log('获取LLM配置响应:', response);
      
      if (response && response.status === 'success') {
        console.log('成功获取LLM配置:', response.data);
        // 确保所有字段都正确设置
        const configData = response.data;
        
        // 手动设置每个字段，避免可能的类型转换问题
        form.setFieldsValue({
          api_url: configData.api_url,
          api_key: configData.api_key,
          model_name: configData.model_name,
          temperature: parseFloat(configData.temperature),
          max_tokens: parseInt(configData.max_tokens),
          top_p: parseFloat(configData.top_p),
          timeout: parseInt(configData.timeout)
        });
        
        // 打印设置后的表单值，用于调试
        console.log('表单设置后的值:', form.getFieldsValue());
      } else {
        console.warn('获取LLM配置返回非成功状态:', response.data);
      }
    } catch (error) {
      console.error('获取LLM配置错误:', error);
      if (error.response?.status !== 404) {
        // 404错误是正常的，表示配置文件不存在
        message.error('加载配置失败: ' + (error.response?.data?.detail || error.message));
      } else {
        console.log('配置文件不存在，将使用默认值');
      }
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/llm/config', values);
      console.log('保存配置响应:', response);
      
      if (response && response.status === 'success') {
        message.success('配置保存成功');
      } else {
        // 处理后端返回的错误信息
        message.error(response.message || '保存配置失败');
      }
    } catch (error) {
      console.error('保存配置错误:', error);
      message.error('保存配置失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 修改测试连接函数
  const testConnection = async () => {
    try {
      const values = await form.validateFields();
      setTestLoading(true);
      console.log("发送测试连接请求:", values);
      
      const response = await axios.post('/llm/test-connection', values);
      console.log("测试连接响应:", response);
      
      // 检查响应状态
      if (response && response.status === 'success') {
        message.success('连接测试成功');
      } else {
        // 处理后端返回的错误信息
        message.error(response.message || '连接测试失败');
      }
    } catch (error) {
      console.error('测试连接错误:', error);
      if (error.name === 'ValidationError' || error.errorFields) {
        message.error('请先填写完整的配置信息');
      } else {
        message.error('连接测试失败: ' + (error.response?.data?.message || error.message));
      }
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <Card title="大语言模型API配置" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Spin spinning={loading}>
        <Form
          form={form}
          layout="vertical"
          onFinish={saveConfig}
          initialValues={{
            api_url: 'https://api.deepseek.com/v1/chat/completions',
            model_name: 'deepseek-chat',
            temperature: 0.7,
            max_tokens: 2000,
            top_p: 0.95,
            timeout: 60
          }}
        >
          <Form.Item
            label={
              <span>
                API URL
                <Tooltip title="大语言模型API的URL地址">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="api_url"
            rules={[{ required: true, message: '请输入API URL' }]}
          >
            <Input placeholder="例如: https://api.deepseek.com/v1/chat/completions" />
          </Form.Item>

          <Form.Item
            label={
              <span>
                API Key
                <Tooltip title="访问大语言模型API所需的密钥">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="api_key"
            rules={[{ required: true, message: '请输入API Key' }]}
          >
            <Input.Password placeholder="请输入API Key" />
          </Form.Item>

          <Form.Item
            label={
              <span>
                模型名称
                <Tooltip title="要使用的大语言模型名称">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="model_name"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如: deepseek-chat" />
          </Form.Item>

          <Form.Item
            label={
              <span>
                Temperature
                <Tooltip title="控制生成文本的随机性，值越高随机性越大">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="temperature"
            rules={[{ required: true, message: '请输入temperature值' }]}
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label={
              <span>
                Max Tokens
                <Tooltip title="生成文本的最大长度">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="max_tokens"
            rules={[{ required: true, message: '请输入max_tokens值' }]}
          >
            <InputNumber min={1} max={8000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label={
              <span>
                Top P
                <Tooltip title="控制生成文本的多样性">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="top_p"
            rules={[{ required: true, message: '请输入top_p值' }]}
          >
            <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label={
              <span>
                超时时间(秒)
                <Tooltip title="API请求的超时时间">
                  <QuestionCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              </span>
            }
            name="timeout"
            rules={[{ required: true, message: '请输入超时时间' }]}
          >
            <InputNumber min={1} max={300} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ marginRight: 16 }}>
              保存配置
            </Button>
            <Button onClick={testConnection} loading={testLoading}>
              测试连接
            </Button>
          </Form.Item>
        </Form>
      </Spin>
    </Card>
  );
};

export default LLMConfig;