import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Select, Space, message } from 'antd';
import { TeamOutlined } from '@ant-design/icons';
import axios from '../../utils/axios';

const RoleUser = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);

  // 获取用户列表
  // 修改获取用户列表的函数，确保获取到用户的角色信息
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/users');
      console.log(response);
      // 确保 response.data 是数组
      const userData = Array.isArray(response.data) ? response.data : response.data || [];
      
      // 获取每个用户的角色信息
      const usersWithRoles = await Promise.all(userData.map(async (user) => {
        try {
          const roleResponse = await axios.get(`/users/${user.id}/roles`);
          console.log("roleResponse:",roleResponse)
          const roleData = Array.isArray(roleResponse) 
            ? roleResponse 
            : roleResponse || [];
          console.log("roleData:",roleData)
          return {
            ...user,
            roles: roleData
          };
        } catch (error) {
          console.error(`获取用户 ${user.id} 的角色失败:`, error);
          return {
            ...user,
            roles: []
          };
        }
      }));
      
      setUsers(usersWithRoles);
    } catch (error) {
      console.error('获取用户列表失败:', error);
      message.error('获取用户列表失败');
    }
    setLoading(false);
  };

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      const response = await axios.get('/roles');
      // 确保 response.data 是数组
      const roleData = Array.isArray(response.data) ? response.data : response.data || [];
      setRoles(roleData);
    } catch (error) {
      console.error('获取角色列表失败:', error);
      message.error('获取角色列表失败');
    }
  };

  // 获取用户的角色
  const fetchUserRoles = async (userId) => {
    try {
      const response = await axios.get(`/users/${userId}/roles`);
      // 确保 response.data 是数组
      const roleData = Array.isArray(response) ? response : response || [];
      //alert(roleData);
      setSelectedRoles(roleData.map(role => role.id));
    } catch (error) {
      console.error('获取用户角色失败:', error);
      message.error('获取用户角色失败');
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  // 显示角色分配对话框
  const showRoleModal = async (user) => {
    setCurrentUser(user);
    await fetchUserRoles(user.id);
    setModalVisible(true);
  };

  // 保存角色分配
  const handleRoleSave = async () => {
    try {
      const requestData = selectedRoles.map(id => Number(id));  // 直接提交 ID 数组
      console.log('提交的数据:', requestData);

      await axios.post(`/users/${currentUser.id}/roles`, requestData);
      message.success('角色分配成功');
      setModalVisible(false);
      // 重新获取用户列表，包括角色信息
      fetchUsers();
    } catch (error) {
      console.error('角色分配失败:', error.response?.data || error);
      message.error('角色分配失败: ' + (error.response?.data?.message || error.message));
    }
  };

  // 修改表格列定义中的当前角色列
  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '当前角色',
      key: 'roles',
      render: (_, record) => {
        // 检查角色数据是否存在
        console.log(record)
        if (!record.roles || !Array.isArray(record.roles) || record.roles.length === 0) {
          return '无';
        }
        
        // 显示角色名称
        return record.roles.map(role => role.name).join(', ');
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="link"
          icon={<TeamOutlined />}
          onClick={() => showRoleModal(record)}
        >
          分配角色
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Table 
        columns={columns} 
        dataSource={users}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="分配角色"
        open={modalVisible}
        onOk={handleRoleSave}
        onCancel={() => setModalVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label={`为用户 "${currentUser?.username}" 分配角色`}>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="请选择角色"
              value={selectedRoles}
              onChange={setSelectedRoles}
              options={roles.map(role => ({
                label: role.name,
                value: role.id
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RoleUser;