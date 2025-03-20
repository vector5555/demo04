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
      console.log('发送查询请求:', value);  // 添加日志
      const response = await axios.post('http://localhost:8000/query', {
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
      const response = await axios.post('http://localhost:8000/query', {
        query_text: currentQuery,
        sql: currentSQL,
        context_id: contextId
      });
      
      const systemMessage = {
        type: 'system',
        sql: currentSQL,
        result: response.data.result,
        error: null,
        timestamp: new Date().toLocaleTimeString(),
        rated: false
      };
      setMessages(prev => [...prev.slice(0, -1), systemMessage]);
      setEditModalVisible(false);
    } catch (error) {
      const errorMessage = {
        type: 'system',
        sql: currentSQL,
        result: [],
        error: error.response?.data?.detail || '执行失败，请检查 SQL 语句',
        timestamp: new Date().toLocaleTimeString(),
        rated: false
      };
      setMessages(prev => [...prev.slice(0, -1), errorMessage]);
    } finally {
      setLoading(false);  // 确保在所有操作完成后关闭加载状态
      setEditModalVisible(false);  // 关闭编辑模态框
    }
  };

  const renderMessage = (msg, index) => {
    if (msg.type === 'user') {
      return (
        <div className="user-message">
          <Text>{msg.content}</Text>
          <Text type="secondary" className="message-time">{msg.timestamp}</Text>
        </div>
      );
    }
    
    // 系统消息渲染
    return (
      <div className="system-message">
        <Card 
          size="small" 
          title="生成的 SQL" 
          className="sql-card"
          extra={
            <Button 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => handleSQLEdit(msg.sql, messages[index - 1]?.content)}
            >
              编辑
            </Button>
          }
        >
          <pre>{msg.sql}</pre>
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
        await axios.post('http://localhost:8000/feedback', {
          query: userMessage.content,  // 从用户消息中获取查询内容
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