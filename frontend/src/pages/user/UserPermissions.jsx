import React, { useState, useEffect } from 'react';
import { Card, Tabs, Table, List, Tag, Collapse, Spin, Typography, Alert, Divider } from 'antd';
import { DatabaseOutlined, TableOutlined, FieldBinaryOutlined, FilterOutlined } from '@ant-design/icons';
import axios from '../../utils/axios';

const { TabPane } = Tabs;
const { Title, Text } = Typography;
const { Panel } = Collapse;

const UserPermissions = () => {
  const [loading, setLoading] = useState(true);
  const [permissions, setPermissions] = useState([]);
  const [tablePermissions, setTablePermissions] = useState([]);
  const [fieldPermissions, setFieldPermissions] = useState({});
  const [filterConditions, setFilterConditions] = useState({});
  const [userInfo, setUserInfo] = useState({});

  useEffect(() => {
    fetchUserPermissions();
  }, []);

  const fetchUserPermissions = async () => {
    try {
      setLoading(true);
      // 从登录响应中获取的权限信息
      const storedPermissions = localStorage.getItem('permissions');
      
      if (storedPermissions) {
        const permissionsData = JSON.parse(storedPermissions);
        processPermissions(permissionsData);
      } else {
        // 如果本地存储中没有，则从会话中获取
        const response = await axios.get('/api/user/session');
        if (response.data && response.data.permissions) {
          processPermissions(response.data.permissions);
          // 存储到本地以便下次使用
          localStorage.setItem('permissions', JSON.stringify(response.data.permissions));
        }
      }
    } catch (error) {
      console.error('获取权限信息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const processPermissions = (permissionsData) => {
    setPermissions(permissionsData);
    
    // 处理表级权限
    const tables = [];
    const fields = {};
    const filters = {};
    
    // 用户信息
    const username = localStorage.getItem('username') || '未知用户';
    const roles = JSON.parse(localStorage.getItem('roles') || '[]');
    setUserInfo({
      username,
      roles: roles.map(r => r.name || r)
    });
    
    // 处理权限数据
    permissionsData.forEach(perm => {
      // 表级权限
      if (perm.table_name && !tables.some(t => t.table_name === perm.table_name)) {
        tables.push({
          table_name: perm.table_name,
          display_name: perm.display_name || perm.table_name,
          permission_type: perm.permission_type || 'read',
          description: perm.description || ''
        });
      }
      
      // 字段级权限
      if (perm.field_list) {
        if (!fields[perm.table_name]) {
          fields[perm.table_name] = [];
        }
        
        let fieldList = [];
        if (typeof perm.field_list === 'string') {
          fieldList = perm.field_list.split(',').map(f => f.trim()).filter(f => f);
        } else if (Array.isArray(perm.field_list)) {
          fieldList = perm.field_list;
        }
        
        fieldList.forEach(field => {
          if (!fields[perm.table_name].some(f => f.field_name === field)) {
            fields[perm.table_name].push({
              field_name: field,
              display_name: field,
              data_type: '未知',
              description: ''
            });
          }
        });
      }
      
      // 过滤条件
      if (perm.where_clause) {
        if (!filters[perm.table_name]) {
          filters[perm.table_name] = [];
        }
        
        filters[perm.table_name].push({
          condition: perm.where_clause,
          description: '数据过滤条件'
        });
      }
    });
    
    setTablePermissions(tables);
    setFieldPermissions(fields);
    setFilterConditions(filters);
  };

  // 表格权限展示
  const tableColumns = [
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: '权限类型',
      dataIndex: 'permission_type',
      key: 'permission_type',
      render: (type) => (
        <Tag color={type === 'read' ? 'blue' : 'green'}>
          {type === 'read' ? '只读' : '读写'}
        </Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    }
  ];

  // 字段权限展示
  const renderFieldPermissions = (tableName) => {
    const fields = fieldPermissions[tableName] || [];
    return (
      <Table 
        dataSource={fields}
        columns={[
          {
            title: '字段名',
            dataIndex: 'field_name',
            key: 'field_name',
          },
          {
            title: '显示名称',
            dataIndex: 'display_name',
            key: 'display_name',
          },
          {
            title: '数据类型',
            dataIndex: 'data_type',
            key: 'data_type',
          },
          {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
          }
        ]}
        pagination={false}
        size="small"
        rowKey="field_name"
      />
    );
  };

  // 过滤条件展示
  const renderFilterConditions = (tableName) => {
    const conditions = filterConditions[tableName] || [];
    if (conditions.length === 0) {
      return <Text type="secondary">无数据过滤条件</Text>;
    }
    
    return (
      <List
        size="small"
        dataSource={conditions}
        renderItem={item => (
          <List.Item>
            <Text code>{item.condition}</Text>
            {item.description && <Text type="secondary"> ({item.description})</Text>}
          </List.Item>
        )}
      />
    );
  };

  return (
    <div className="user-permissions-container">
      <Card loading={loading}>
        <Title level={4}>
          <DatabaseOutlined /> 我的数据权限
        </Title>
        
        {!loading && (
          <>
            <Alert
              message={`当前用户: ${userInfo.username}`}
              description={`角色: ${userInfo.roles?.join(', ') || '无角色'} | 可访问表数量: ${tablePermissions.length}`}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Tabs defaultActiveKey="tables">
              <TabPane 
                tab={<span><TableOutlined /> 表级权限</span>}
                key="tables"
              >
                <Table 
                  dataSource={tablePermissions}
                  columns={tableColumns}
                  rowKey="table_name"
                />
              </TabPane>
              
              <TabPane 
                tab={<span><FieldBinaryOutlined /> 字段级权限</span>}
                key="fields"
              >
                <Collapse>
                  {tablePermissions.map(table => (
                    <Panel 
                      header={`${table.display_name} (${table.table_name})`}
                      key={table.table_name}
                    >
                      {renderFieldPermissions(table.table_name)}
                    </Panel>
                  ))}
                </Collapse>
              </TabPane>
              
              <TabPane 
                tab={<span><FilterOutlined /> 数据过滤条件</span>}
                key="filters"
              >
                <Collapse>
                  {tablePermissions.map(table => (
                    <Panel 
                      header={`${table.display_name} (${table.table_name})`}
                      key={table.table_name}
                    >
                      {renderFilterConditions(table.table_name)}
                    </Panel>
                  ))}
                </Collapse>
              </TabPane>
            </Tabs>
          </>
        )}
      </Card>
    </div>
  );
};

export default UserPermissions;