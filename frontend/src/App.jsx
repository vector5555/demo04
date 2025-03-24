import React, { useState } from 'react';
import { Input, Card, Space, message, List, Typography, Modal, Rate, Button, Alert, Spin } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import axios from 'axios';
import './App.css';

const { Search } = Input;
const { Text } = Typography;

function App() {
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [contextId, setContextId] = useState(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentSQL, setCurrentSQL] = useState('');
  const [currentQuery, setCurrentQuery] = useState('');
  
  const handleSQLEdit = (sql, content) => {
    try {
      if (!sql) {
        message.warning('SQL 语句不能为空');
        return;
      }
      setCurrentSQL(sql);
      setCurrentQuery(content || '');
      setEditModalVisible(true);
    } catch (error) {
      console.error('编辑 SQL 时出错:', error);
      message.error('编辑 SQL 时出错');
    }
  };

  const handleSearch = async (value) => {
    if (!value.trim()) {
      message.warning('请输入查询内容');
      return;
    }
    
    // 添加用户消息
    const userMessage = {
      type: 'user',
      content: value,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    setLoading(true);
    try {
      console.log('发送查询请求:', value);
      const response = await axios.post('http://localhost:8000/query_nl', {  // 修改为 query_nl
        query_text: value,
        context_id: contextId
      });
      console.log('收到后端响应:', response.data);  // 添加日志
      
      // 保存上下文ID
      if (!contextId) {
        setContextId(response.data.context_id);
      }
      
      // 添加系统响应
      const systemMessage = {
        type: 'system',
        sql: response.data.sql,
        result: response.data.result,
        error: response.data.error,  // 添加错误字段
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, systemMessage]);
      
    } catch (error) {
      // 添加错误消息，但保留生成的 SQL
      const errorMessage = {
        type: 'system',
        sql: error.response?.data?.sql || '未能生成 SQL',
        result: [],
        error: error.response?.data?.detail || '查询失败，请重试',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);  // 确保在所有操作完成后关闭加载状态
    }
  };

  const handleExecuteSQL = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/execute_edited', {
        original_sql: currentSQL,
        edited_sql: currentSQL,
      });
      
      // 创建新的消息，标记为人工编辑
      const systemMessage = {
        type: 'system',
        sql: currentSQL,
        result: response.data.data,
        error: null,
        timestamp: new Date().toLocaleTimeString(),
        rated: false,
        isEdited: true,  // 标记为编辑后的 SQL
        editTime: new Date().toLocaleTimeString()  // 记录编辑时间
      };
      
      // 添加新消息而不是覆盖
      setMessages(prev => [...prev, systemMessage]);
      setEditModalVisible(false);
    } catch (error) {
      const errorMessage = {
        type: 'system',
        sql: currentSQL,
        result: [],
        error: error.response?.data?.detail || '执行失败，请检查 SQL 语句',
        timestamp: new Date().toLocaleTimeString(),
        rated: false,
        isEdited: true,
        editTime: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setEditModalVisible(false);
    }
  };

  // 修改渲染逻辑，在 renderMessage 函数中添加编辑标记
  const renderMessage = (msg, index) => {
    if (msg.type === 'user') {
      return (
        <div className="user-message">
          <Text>{msg.content}</Text>
          <Text type="secondary" className="message-time">{msg.timestamp}</Text>
        </div>
      );
    }
    
    return (
      <div className="system-message">
        <Card 
          size="small" 
          title={msg.isEdited ? "编辑后的 SQL" : "AI 生成的 SQL"}  // 区分标题
          className={`sql-card ${msg.isEdited ? 'edited-sql' : ''}`}  // 添加样式类
          extra={
            !msg.isEdited && (  // 只在 AI 生成的 SQL 上显示编辑按钮
              <Button 
                icon={<EditOutlined />} 
                size="small"
                onClick={() => handleSQLEdit(msg.sql, messages[index - 1]?.content)}
              >
                编辑
              </Button>
            )
          }
        >
          <pre>{msg.sql}</pre>
          {msg.isEdited && (
            <Text type="secondary">编辑时间: {msg.editTime}</Text>
          )}
        </Card>
        
        {msg.error ? (
          <Alert
            message="执行错误"
            description={msg.error}
            type="error"
            showIcon
          />
        ) : (
          msg.result && Array.isArray(msg.result) && msg.result.length > 0 && (
            <>
              <div className="result-table">
                <table>
                  <thead>
                    <tr>
                      {Object.keys(msg.result[0]).map(key => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {msg.result.map((row, idx) => (
                      <tr key={idx}>
                        {Object.values(row).map((value, i) => (
                          <td key={i}>{value}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {!msg.rated && (
                <div className="feedback">
                  <Text>这个查询结果符合你的预期吗？</Text>
                  <Rate onChange={(value) => handleRate(index, value)} />
                </div>
              )}
            </>
          )
        )}
        <Text type="secondary" className="message-time">{msg.timestamp}</Text>
      </div>
    );
  };

  const handleRate = async (messageIndex, rating) => {
    const currentMessage = messages[messageIndex];
    // 获取对应的用户查询消息
    const userMessage = messages[messageIndex - 1];
    
    if (rating >= 4) {
      try {
        // 确保有查询内容
        let queryText;
        if (currentMessage.isEdited) {
          // 查找最近的用户查询消息
          for (let i = messageIndex - 1; i >= 0; i--) {
            if (messages[i].type === 'user') {
              queryText = `[编辑] ${messages[i].content}`;
              break;
            }
          }
        } else {
          queryText = userMessage?.content;
        }

        // 如果还是没有找到查询内容，使用默认值
        if (!queryText) {
          queryText = '[编辑] 手动编辑的SQL查询';
        }

        await axios.post('http://localhost:8000/feedback', {
          query: queryText,
          sql: currentMessage.sql,
          rating: rating
        });
        
        const updatedMessages = [...messages];
        updatedMessages[messageIndex] = {
          ...currentMessage,
          rated: true
        };
        setMessages(updatedMessages);
        message.success('感谢反馈！此查询将被添加到示例中');
      } catch (error) {
        message.error('反馈提交失败');
      }
    }
  };

  return (
    <div className="app-container">
      <Card title="自然语言数据库查询" className="chat-card">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div className="messages-container">
            <List
              dataSource={messages}
              renderItem={(item, index) => renderMessage(item, index)}
              locale={{ emptyText: '开始你的第一次查询吧！' }}
            />
            {loading && (
              <div className="loading-container">
                <Spin tip="正在查询..." />
              </div>
            )}
          </div>
          
          <div className="input-container">
            <Search
              placeholder="请输入自然语言查询，例如：查询所有监测站点的数据"
              enterButton="发送"
              size="large"
              loading={loading}
              onSearch={handleSearch}
            />
          </div>
        </Space>
      </Card>

      <Modal
        title="编辑 SQL 语句"
        open={editModalVisible}
        onOk={handleExecuteSQL}
        onCancel={() => {
           setEditModalVisible(false);
          setCurrentSQL('');
          setCurrentQuery('');
        }}
        confirmLoading={loading}
        destroyOnClose
      >
        <Input.TextArea
          value={currentSQL}
          onChange={(e) => setCurrentSQL(e.target.value)}
          rows={6}
          style={{ marginBottom: 16 }}
        />
      </Modal>
    </div>
  );
}

export default App;