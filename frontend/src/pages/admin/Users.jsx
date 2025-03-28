import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, KeyOutlined } from '@ant-design/icons';
import axios from '../../utils/axios';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState('新增用户');
  const [form] = Form.useForm();
  const [currentUser, setCurrentUser] = useState(null);
  const [resetPasswordVisible, setResetPasswordVisible] = useState(false);

  // 获取用户列表
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('获取用户列表失败:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<KeyOutlined />}
            onClick={() => showResetPassword(record)}
          >
            重置密码
          </Button>
          <Button 
            type="link" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // 显示新增用户模态框
  const showAddModal = () => {
    setModalTitle('新增用户');
    setCurrentUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 显示重置密码模态框
  const showResetPassword = (user) => {
    setCurrentUser(user);
    form.resetFields();
    setResetPasswordVisible(true);
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await axios.post('/users', values);
      message.success('用户创建成功');
      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      console.error('创建用户失败:', error);
    }
  };

  // 处理重置密码
  const handleResetPassword = async () => {
    try {
      const values = await form.validateFields();
      await axios.put(`/users/${currentUser.id}/password`, { password: values.password });
      message.success('密码重置成功');
      setResetPasswordVisible(false);
    } catch (error) {
      console.error('重置密码失败:', error);
    }
  };

  // 处理删除用户
  const handleDelete = async (userId) => {
    try {
      await axios.delete(`/users/${userId}`);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      console.error('删除用户失败:', error);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={showAddModal}>
          新增用户
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
      />

      {/* 新增用户模态框 */}
      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置密码模态框 */}
      <Modal
        title="重置密码"
        open={resetPasswordVisible}
        onOk={handleResetPassword}
        onCancel={() => setResetPasswordVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="password"
            label="新密码"
            rules={[{ required: true, message: '请输入新密码' }]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users;