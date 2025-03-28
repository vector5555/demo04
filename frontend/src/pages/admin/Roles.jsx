import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import axios from '../../utils/axios';

const Roles = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editingRole, setEditingRole] = useState(null);

  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/roles');
      console.log('角色数据响应:', response);
      // 直接使用 response.data，不再检查 data.data
      setRoles(response.data || []);
    } catch (error) {
      console.error('获取角色列表失败:', error);
      message.error('获取角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const roleData = {
        role_name: values.name,        // 修改这里，使用 role_name 而不是 name
        description: values.description || ''
      };

      console.log('提交的数据:', roleData); // 添加日志查看提交的数据

      if (editingRole) {
        await axios.put(`/roles/${editingRole.id}`, roleData);
        message.success('角色更新成功');
      } else {
        await axios.post('/roles', roleData);
        message.success('角色创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      fetchRoles();
    } catch (error) {
      console.error('操作失败:', error.response?.data || error); // 修改错误日志，显示更详细的错误信息
      message.error('操作失败：' + (error.response?.data?.message || error.message));
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/roles/${id}`);
      message.success('角色删除成功');
      fetchRoles();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',  // 修改这里匹配后端返回的字段名
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingRole(record);
              form.setFieldsValue(record);
              setModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个角色吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingRole(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          新建角色
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={roles}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingRole ? "编辑角色" : "新建角色"}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="name"  // 修改这里匹配后端接收的字段名
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Roles;