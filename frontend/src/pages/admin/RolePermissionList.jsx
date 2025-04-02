import React, { useState, useEffect } from 'react';
import { Table, Button, Space, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from '../../utils/axios';

const RolePermissionList = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/roles');
      console.log('获取角色响应:', response); // 添加日志查看响应数据
      
      // 修正这里，确保正确处理后端返回的数据结构
      if (response && response.status === 'success' && response.data) {
        setRoles(response.data);
      } else {
        setRoles(response.data || []);
      }
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

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
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
        <Button 
          type="primary"
          onClick={() => navigate(`/admin/role-permission/${record.id}`)}
        >
          配置权限
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h2>角色权限配置</h2>
      <Table 
        columns={columns} 
        dataSource={roles}
        rowKey="id"
        loading={loading}
      />
    </div>
  );
};

export default RolePermissionList;