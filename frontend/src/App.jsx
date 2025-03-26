import React, { useState } from 'react';
import { Card, Space, message, Modal, Input, Button, Typography, Rate } from 'antd';  // 添加缺失的组件
import { EditOutlined } from '@ant-design/icons';  // 添加图标
import axios from 'axios';
import './App.css';

const { Text } = Typography;  // 添加 Text 组件引用

import QueryInput from './components/QueryInput';
import MessageList from './components/MessageList';
import { detectChartType } from './utils/chartSelector';

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
        error: response.data.error,
        timestamp: new Date().toLocaleTimeString(),
        rated: false  // 添加 rated 字段
      };
      setMessages(prev => [...prev, systemMessage]);
      
    } catch (error) {
      // 添加错误消息，但保留生成的 SQL
      const errorMessage = {
        type: 'system',
        sql: error.response?.data?.sql || '未能生成 SQL',
        result: [],
        error: error.response?.data?.detail || '查询失败，请重试',
        timestamp: new Date().toLocaleTimeString(),
        rated: false  // 添加 rated 字段
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
        result: response.data.data || [],
        error: null,
        timestamp: new Date().toLocaleTimeString(),
        rated: false,
        isEdited: true,
        editTime: new Date().toLocaleTimeString()
      };
      
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
      message.error('SQL 执行出错');
    } finally {
      setLoading(false);
      setEditModalVisible(false);
    }
  };

  const handleRate = async (messageIndex, rating) => {
    const currentMessage = messages[messageIndex];
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
          sql: currentMessage.sql.replace(/\n/g, ' '), // 移除 SQL 中的换行符
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
          <MessageList 
            messages={messages}
            loading={loading}
            onEdit={handleSQLEdit}
            onRate={handleRate}
          />
          <QueryInput 
            loading={loading}
            onSearch={handleSearch}
          />
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