import React, { useState, useEffect } from 'react';
import { Card, Steps, Form, Select, Tree, Input, Button, message, Checkbox, Spin, Collapse } from 'antd';
import { useParams } from 'react-router-dom';
import axios from '../../utils/axios';

const { Step } = Steps;

const RolePermission = () => {
  const { roleId } = useParams();
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [databases, setDatabases] = useState([]);
  const [tables, setTables] = useState([]);
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dbConfig, setDbConfig] = useState({
    host: '',
    port: 3306,
    username: '',
    password: '',
  });

  // 添加保存和加载连接配置的函数
  const saveConnectionConfig = (config) => {
    try {
      // 将连接配置保存到 localStorage
      localStorage.setItem('dbConnectionConfig', JSON.stringify(config));
      console.log('数据库连接配置已保存到本地');
    } catch (error) {
      console.error('保存数据库连接配置失败:', error);
    }
  };

  const loadConnectionConfig = () => {
    try {
      // 从 localStorage 加载连接配置
      const savedConfig = localStorage.getItem('dbConnectionConfig');
      if (savedConfig) {
        const config = JSON.parse(savedConfig);
        console.log('从本地加载数据库连接配置:', config);
        return config;
      }
    } catch (error) {
      console.error('加载数据库连接配置失败:', error);
    }
    return null;
  };

  // 修改 handleTestConnection 函数，成功后保存配置
  const handleTestConnection = async () => {
    try {
      setLoading(true);
      await axios.post('/database/test-connection', dbConfig);
      message.success('数据库连接成功');
      
      // 连接成功后保存配置
      saveConnectionConfig(dbConfig);
      
      fetchDatabases();
    } catch (error) {
      message.error('数据库连接失败：' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 修改 fetchDatabases 函数，使用全局配置
  const fetchDatabases = async () => {
    try {
      console.log('开始获取数据库列表');
      
      // 获取全局数据库配置
      const configResponse = await axios.get('/database/config');
      let config;
      
      if (configResponse.status === 'success') {
        config = configResponse.data;
        // 更新本地配置
        setDbConfig(config);
        
        // 设置表单值
        form.setFieldsValue({
          host: config.host,
          port: config.port,
          username: config.username,
          password: config.password
        });
      } else {
        // 如果没有全局配置，使用本地配置
        config = dbConfig;
      }
      
      const response = await axios.post('/databases', config);
      console.log('获取到的响应:', response);
      
      if (response?.status === 'success' && Array.isArray(response.data)) {
        console.log('数据库列表:', response.data);
        // 直接从对象数组中提取 name 属性值
        const dbNames = response.data.map(db => db.name);
        setDatabases(dbNames);
      } else {
        console.log('没有获取到数据库列表');
        setDatabases([]);
      }
    } catch (error) {
      console.error('获取数据库列表失败:', error);
      message.error('获取数据库列表失败');
      setDatabases([]);
    }
  };

  // 修改 useEffect 钩子
  useEffect(() => {
    // 直接获取全局数据库配置
    fetchDatabases();
    
    // 获取角色已有权限
    fetchRolePermissions();
  }, []);

  // 修改 handleDatabaseChange 函数
  const handleDatabaseChange = async (dbName) => {
    try {
      console.log('开始获取表列表, 数据库名:', dbName);
      // 使用全局配置
      const response = await axios.post(`/databases/${dbName}/tables`, dbConfig);
      
      if (response.status === 'success') {
        const { tables = [], views = [] } = response.data;
        setTables([
          ...tables.map(tableName => ({ name: tableName, type: 'table' })),
          ...views.map(viewName => ({ name: viewName, type: 'view' }))
        ]);
      } else {
        console.log('响应格式不符合预期:', response);
        setTables([]);
      }
    } catch (error) {
      console.error('获取表列表失败:', error);
      message.error('获取表列表失败');
      setTables([]);
    }
  };
  
  // 修改 handleTableChange 函数，处理字段注释
  const handleTableChange = async (tableName) => {
    console.log('handleTableChange 被调用，表名:', tableName);
    try {
      const dbName = form.getFieldValue('db_name');
      console.log('当前选中的数据库:', dbName);
      
      if (!dbName) {
        message.error('请先选择数据库');
        return;
      }
      
      // 使用全局配置
      const params = {
        ...dbConfig,
        database: dbName
      };
      
      console.log('发送请求获取字段列表，URL:', `/databases/${dbName}/tables/${tableName}/fields`);
      console.log('请求参数:', params);
      
      // 添加超时处理
      const response = await axios.get(`/databases/${dbName}/tables/${tableName}/fields`, {
        params,
        timeout: 10000 // 10秒超时
      });
      
      console.log('获取字段列表响应类型:', typeof response);
      console.log('获取字段列表响应内容:', JSON.stringify(response, null, 2));
      
      // 检查响应格式
      if (response?.status === 'success') {
        console.log('字段列表数据:', response.data);
        // 使用正确的数据访问路径
        const fieldsData = response.data.fields || [];
        console.log('处理后的字段数据:', fieldsData);
        
        // 创建新的树节点，包含字段注释
        const newTreeNode = {
          title: tableName,
          key: `table-${tableName}`,
          children: fieldsData.map(field => ({
            title: `${field.name} (${field.type})${field.comment ? ` - ${field.comment}` : ''}`,
            key: `${tableName}.${field.name}`,
            // 存储字段的完整信息，包括注释
            fieldInfo: {
              name: field.name,
              type: field.type,
              comment: field.comment || ''
            }
          }))
        };
        
        // 更新字段列表，保留之前的字段
        setFields(prevFields => {
          // 检查是否已存在该表的节点
          const existingIndex = prevFields.findIndex(node => node.key === `table-${tableName}`);
          if (existingIndex >= 0) {
            // 替换已存在的节点
            const updatedFields = [...prevFields];
            updatedFields[existingIndex] = newTreeNode;
            return updatedFields;
          } else {
            // 添加新节点
            return [...prevFields, newTreeNode];
          }
        });
      } else {
        console.log('响应格式不符合预期');
        message.error('获取字段列表失败：响应格式不符合预期');
      }
    } catch (error) {
      console.error('获取字段列表失败:', error);
      console.error('错误详情:', error.response?.data || error.message);
      message.error('获取字段列表失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 保存权限设置
  // 修改状态管理，添加表过滤条件映射
  const [tableFilters, setTableFilters] = useState({});
  
  // 修改保存权限设置函数
  // 修改 handleSubmit 函数，保存字段注释信息
  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      // 获取当前选中的表
      const selectedTables = form.getFieldValue('table_name') || [];
      console.log('当前选中的表:', selectedTables);
      
      if (selectedTables.length === 0) {
        message.warning('请至少选择一个数据表或视图');
        setLoading(false);
        return;
      }
      
      // 获取数据库名称
      const dbName = form.getFieldValue('db_name');
      if (!dbName) {
        message.warning('请选择数据库');
        setLoading(false);
        return;
      }
      
      // 获取选中的字段
      const selectedFields = form.getFieldValue('field_list') || [];
      console.log('当前选中的字段:', selectedFields);
      
      // 为每个选中的表创建一个权限记录，包含字段注释
      const permissions = selectedTables.map(tableName => {
        // 过滤出属于当前表的字段
        const tableFieldKeys = selectedFields.filter(field => 
          typeof field === 'string' && field.startsWith(`${tableName}.`)
        );
        
        // 获取字段名部分
        const tableFieldNames = tableFieldKeys.map(field => field.split('.')[1]);
        
        // 获取字段的完整信息，包括注释
        const tableFieldsInfo = [];
        
        // 从字段树中查找对应表的节点
        const tableNode = fields.find(node => node.key === `table-${tableName}`);
        if (tableNode && tableNode.children) {
          // 遍历表节点的子节点（字段）
          tableNode.children.forEach(fieldNode => {
            // 如果字段被选中，添加到字段信息列表
            if (tableFieldKeys.includes(fieldNode.key) && fieldNode.fieldInfo) {
              tableFieldsInfo.push(fieldNode.fieldInfo);
            }
          });
        }
        
        // 从表单值或状态中获取过滤条件
        const filterValue = tableFilters[tableName] || '';
        
        return {
          db_name: dbName,
          table_name: tableName,
          field_list: tableFieldNames,
          field_info: tableFieldsInfo, // 添加字段完整信息，包括注释
          where_clause: filterValue
        };
      });
      
      console.log('提交的权限数据:', permissions);
      
      // 提交权限数据
      const response = await axios.post(`/roles/${roleId}/permissions`, permissions);
      
      console.log('保存权限响应:', response);
      message.success('权限设置成功');
    } catch (error) {
      console.error('保存权限失败:', error);
      message.error('保存权限失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 添加获取角色权限的函数和相关状态
  const [existingPermissions, setExistingPermissions] = useState([]);
  
  // 获取角色已有权限
  const fetchRolePermissions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/roles/${roleId}/permissions`);
      
      if (response.status === 'success' && Array.isArray(response.data)) {
        console.log('获取到的角色权限:', response.data);
        setExistingPermissions(response.data);
        
        // 如果有权限数据，预设表单值
        if (response.data.length > 0) {
          // 提取数据库名称（假设所有权限使用同一个数据库）
          const dbName = response.data[0].db_name;
          
          // 提取表名列表
          const tableNames = response.data.map(perm => perm.table_name);
          
          // 设置过滤条件
          const filters = {};
          response.data.forEach(perm => {
            // 确保过滤条件被正确保存
            if (perm.where_clause) {
              filters[perm.table_name] = perm.where_clause;
              console.log(`设置表 ${perm.table_name} 的过滤条件:`, perm.where_clause);
            }
          });
          setTableFilters(filters);
          
          // 优先使用本地保存的连接配置
          const savedConfig = loadConnectionConfig();
          const connectionConfig = savedConfig || response.data[0].connection_info || {
            host: 'localhost',
            port: 3306,
            username: 'root',
            password: ''
          };
          
          // 更新数据库配置
          setDbConfig(connectionConfig);
          
          // 设置表单初始值
          form.setFieldsValue({
            host: connectionConfig.host,
            port: connectionConfig.port,
            username: connectionConfig.username,
            password: connectionConfig.password,
            db_name: dbName,
            table_name: tableNames
          });
          
          // 为每个表添加过滤条件表单值
          tableNames.forEach(tableName => {
            if (filters[tableName]) {
              form.setFieldsValue({
                [`filter_${tableName}`]: filters[tableName]
              });
            }
          });
          
          // 使用连接配置测试连接
          try {
            await axios.post('/database/test-connection', connectionConfig);
            console.log('数据库连接成功');
            
            // 获取数据库列表
            const dbResponse = await axios.post('/databases', connectionConfig);
            if (dbResponse?.status === 'success' && Array.isArray(dbResponse.data)) {
              const dbNames = dbResponse.data.map(db => db.name);
              setDatabases(dbNames);
              
              // 加载数据库表
              const tablesResponse = await axios.post(`/databases/${dbName}/tables`, connectionConfig);
              if (tablesResponse.status === 'success') {
                const { tables = [], views = [] } = tablesResponse.data;
                setTables([
                  ...tables.map(tableName => ({ name: tableName, type: 'table' })),
                  ...views.map(viewName => ({ name: viewName, type: 'view' }))
                ]);
                
                // 加载每个表的字段
                for (const tableName of tableNames) {
                  await handleTableChange(tableName);
                }
                
                // 设置选中的字段
                setTimeout(() => {
                  const allSelectedFields = [];
                  response.data.forEach(perm => {
                    if (Array.isArray(perm.field_list)) {
                      perm.field_list.forEach(field => {
                        allSelectedFields.push(`${perm.table_name}.${field}`);
                      });
                    }
                  });
                  
                  form.setFieldsValue({
                    field_list: allSelectedFields
                  });
                }, 1000); // 给一点时间让字段加载完成
              }
            }
          } catch (error) {
            console.error('加载数据库信息失败:', error);
            message.error('加载数据库信息失败，请手动配置数据库连接');
          }
        }
      }
    } catch (error) {
      console.error('获取角色权限失败:', error);
      message.error('获取角色权限失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 修改 useEffect，添加加载保存的连接配置
  useEffect(() => {
    // 尝试从本地加载连接配置
    const savedConfig = loadConnectionConfig();
    if (savedConfig) {
      setDbConfig(savedConfig);
      
      // 使用加载的配置设置表单初始值
      form.setFieldsValue({
        host: savedConfig.host || '',
        port: savedConfig.port || 3306,
        username: savedConfig.username || '',
        password: savedConfig.password || ''
      });
      
      // 尝试使用保存的配置测试连接并获取数据库列表
      (async () => {
        try {
          setLoading(true);
          await axios.post('/database/test-connection', savedConfig);
          console.log('使用保存的配置连接数据库成功');
          
          // 获取数据库列表
          const response = await axios.post('/databases', savedConfig);
          if (response?.status === 'success' && Array.isArray(response.data)) {
            const dbNames = response.data.map(db => db.name);
            setDatabases(dbNames);
          }
        } catch (error) {
          console.error('使用保存的配置连接数据库失败:', error);
        } finally {
          setLoading(false);
        }
      })();
    } else {
      // 如果没有保存的配置，则正常获取数据库列表
      fetchDatabases();
    }
    
    // 获取角色已有权限
    fetchRolePermissions();
  }, []);

  // 添加 Collapse 面板的激活状态
  const [activeKeys, setActiveKeys] = useState([]); // 默认收起

  const steps = [
    {
      title: '选择数据库和表',
      content: (
        <Form.Item>
          <Collapse 
            activeKey={activeKeys} 
            onChange={setActiveKeys}
            style={{ marginBottom: 16 }}
          >
            <Collapse.Panel header="数据库连接配置（只读）" key="dbConfig">
              <Form.Item
                label="主机地址"
                name="host"
              >
                <Input 
                  placeholder="localhost"
                  disabled={true}
                  readOnly={true}
                  style={{ backgroundColor: '#f5f5f5' }}
                />
              </Form.Item>
              <Form.Item
                label="端口"
                name="port"
              >
                <Input 
                  placeholder="3306"
                  type="number"
                  disabled={true}
                  readOnly={true}
                  style={{ backgroundColor: '#f5f5f5' }}
                />
              </Form.Item>
              <Form.Item
                label="用户名"
                name="username"
              >
                <Input 
                  disabled={true}
                  readOnly={true}
                  style={{ backgroundColor: '#f5f5f5' }}
                />
              </Form.Item>
              <Form.Item
                label="密码"
                name="password"
              >
                <Input.Password 
                  disabled={true}
                  readOnly={true}
                  style={{ backgroundColor: '#f5f5f5' }}
                />
              </Form.Item>
            </Collapse.Panel>
          </Collapse>
          <Form.Item name="db_name" label="数据库">
            <Select onChange={handleDatabaseChange}>
              {databases.map(dbName => (
                <Select.Option key={dbName} value={dbName}>{dbName}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="table_name" label="数据表/视图">
            <Checkbox.Group 
              style={{ display: 'flex', flexDirection: 'column' }}
              onChange={(selectedTables) => {
                console.log('选中的表:', selectedTables);
                
                // 清空字段列表
                setFields([]);
                
                // 处理选中的表
                if (selectedTables.length > 0) {
                  selectedTables.forEach(table => {
                    console.log('准备获取表字段:', table);
                    handleTableChange(table);
                  });
                }
              }}
            >
              {tables.map(table => (
                <Checkbox key={table.name} value={table.name}>
                  {table.name} ({table.type === 'view' ? '视图' : '表'})
                </Checkbox>
              ))}
            </Checkbox.Group>
          </Form.Item>
        </Form.Item>
      )
    },
    {
      title: '配置字段权限',
      content: (
        <Form.Item name="field_list" label="可访问字段">
          <Tree
            checkable
            treeData={fields}
            defaultExpandAll
            checkedKeys={form.getFieldValue('field_list') || []}
            onCheck={(checkedKeys, info) => {
              console.log('选中的字段:', checkedKeys);
              // 确保 checkedKeys 是数组
              const fieldList = Array.isArray(checkedKeys) ? checkedKeys : checkedKeys.checked || [];
              
              // 直接设置表单值
              form.setFieldsValue({ field_list: fieldList });
              
              // 强制更新组件
              setFields([...fields]);
            }}
            selectable={false}
            titleRender={(nodeData) => {
              // 自定义标题渲染，突出显示注释
              if (nodeData.fieldInfo) {
                return (
                  <span>
                    <strong>{nodeData.fieldInfo.name}</strong> ({nodeData.fieldInfo.type})
                    {nodeData.fieldInfo.comment && (
                      <span style={{ color: '#1890ff', marginLeft: 8 }}>
                        {nodeData.fieldInfo.comment}
                      </span>
                    )}
                  </span>
                );
              }
              return nodeData.title;
            }}
          />
        </Form.Item>
      )
    },
    {
      title: '设置数据过滤',
      content: (
        <div>
          <h3>为每个表设置过滤条件</h3>
          {(() => {
            // 使用函数立即执行表达式确保每次渲染都获取最新值
            const selectedTables = form.getFieldValue('table_name') || [];
            
            if (selectedTables.length > 0) {
              return selectedTables.map(tableName => {
                // 获取当前表的过滤条件
                const filterValue = form.getFieldValue(`filter_${tableName}`) || tableFilters[tableName] || '';
                
                return (
                  <Form.Item 
                    key={tableName}
                    name={`filter_${tableName}`}
                    label={`${tableName} 过滤条件`}
                    initialValue={filterValue} // 设置初始值
                  >
                    <Input.TextArea
                      placeholder={`请输入 ${tableName} 表的 SQL WHERE 子句，例如: status = 'active'`}
                      rows={3}
                      defaultValue={filterValue} // 设置默认值
                      onChange={(e) => {
                        const newValue = e.target.value;
                        setTableFilters(prev => ({
                          ...prev,
                          [tableName]: newValue
                        }));
                      }}
                    />
                  </Form.Item>
                );
              });
            } else {
              return (
                <div style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                  请先在第一步选择数据表
                </div>
              );
            }
          })()}
        </div>
      )
    }
  ];
  // 修改 return 部分，修复对象渲染错误
  return (
    <Card title="数据权限配置">
      <Steps current={currentStep}>
        {steps.map(item => (
          <Step key={item.title} title={item.title} />
        ))}
      </Steps>
      <div style={{ marginTop: 24 }}>
        <Form form={form} layout="vertical">
          {steps[currentStep].content}
        </Form>
      </div>
      <div style={{ marginTop: 24 }}>
        {currentStep > 0 && (
          <Button style={{ marginRight: 8 }} onClick={() => {
            setCurrentStep(currentStep - 1);
          }}>
            上一步
          </Button>
        )}
        {currentStep < steps.length - 1 && (
          <Button type="primary" onClick={() => {
            const selectedTables = form.getFieldValue('table_name');
            if (currentStep === 0 && (!selectedTables || selectedTables.length === 0)) {
              message.warning('请至少选择一个数据表或视图');
              return;
            }
            setCurrentStep(currentStep + 1);
          }}>
            下一步
          </Button>
        )}
        {currentStep === steps.length - 1 && (
          <Button type="primary" onClick={handleSubmit} loading={loading}>
            保存
          </Button>
        )}
      </div>
    </Card>
  );
};

export default RolePermission;