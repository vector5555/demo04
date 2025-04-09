import React, { useState } from 'react';
import { Card, Space, message, Modal, Input, Button } from 'antd';
import { LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import axios from '../utils/axios';  // 使用自定义的 axios 实例
import QueryInput from '../components/QueryInput';
import MessageList from '../components/MessageList';
import { handleSqlError } from '../utils/errorHandler';

function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [contextId, setContextId] = useState(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentSQL, setCurrentSQL] = useState('');
  const [currentQuery, setCurrentQuery] = useState('');
  
  // 添加 handleSQLEdit 函数
  const handleSQLEdit = (sql, query) => {
    setCurrentSQL(sql);
    setCurrentQuery(query);
    setEditModalVisible(true);
  };
  
  // 添加 handleRate 函数
  const handleRate = async (messageIndex, rating) => {
    const message = messages[messageIndex];
    try {
      await axios.post('/feedback', {
        query: message.content,
        sql: message.sql,
        rating: rating
      });
      
      const updatedMessages = [...messages];
      updatedMessages[messageIndex] = { ...message, rated: true };
      setMessages(updatedMessages);
      
      message.success('反馈提交成功');
    } catch (error) {
      message.error('反馈提交失败');
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
      // 修改为使用带权限控制的接口
      // 移除调试用的alert
      console.log('发送查询请求:', value);

      const response = await axios.post('/query_nl_with_auth', {
        query_text: value,
        context_id: contextId,
      }, {
        // 添加超时设置和详细日志
        timeout: 60000,
        onUploadProgress: (p) => console.log('上传进度:', p),
        onDownloadProgress: (p) => console.log('下载进度:', p),
      });
      
      console.log('API响应:', response);
      // 修正：使用response.data获取API返回的数据
      // const data = response.data;
      // console.log('响应数据:', data);
      
      // 检查响应数据
      // if (!data) {
      //   throw new Error('响应数据为空');
      // }
      
      const systemMessage = {
        type: 'system',
        content: value,
        sql: response.sql,
        result: response.result,
        error: null,
        timestamp: new Date().toLocaleTimeString(),
        rated: false
      };
      setMessages(prev => [...prev, systemMessage]);
      
      if (!contextId && response.context_id) {
        setContextId(response.context_id);
      }
      
    } catch (error) {
      console.error('查询错误:', error);
      
      // 使用错误处理工具处理SQL错误
      const errorInfo = handleSqlError(error);
      
      const errorMessage = {
        type: 'system',
        content: value,
        sql: '未能生成 SQL',
        result: [],
        error: errorInfo.errorMessage || '查询失败，请重试',
        errorSuggestion: errorInfo.suggestion,
        timestamp: new Date().toLocaleTimeString(),
        rated: false
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };
  
  // 同样修改 handleExecuteSQL 函数
  const handleExecuteSQL = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/execute_edited', {
        original_sql: currentSQL,
        edited_sql: currentSQL,
      });
      
      const systemMessage = {
        type: 'system',
        sql: currentSQL,
        result: response.data || [],
        error: null,
        timestamp: new Date().toLocaleTimeString(),
        rated: false,
        isEdited: true,
        editTime: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, systemMessage]);
      setEditModalVisible(false);
    } catch (error) {
      console.error('执行SQL错误:', error);
      
      // 使用错误处理工具处理SQL错误
      const errorInfo = handleSqlError(error);
      
      const errorMessage = {
        type: 'system',
        sql: currentSQL,
        result: [],
        error: errorInfo.errorMessage || '执行SQL失败',
        errorSuggestion: errorInfo.suggestion,
        timestamp: new Date().toLocaleTimeString(),
        rated: false,
        isEdited: true,
        editTime: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
      setEditModalVisible(false);
    } finally {
      setLoading(false);
    }
  };
  
  const handleLogout = () => {
    Cookies.remove('token');
    navigate('/login');
  };

  return (
    <div className="app-container">
      <Card 
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>自然语言数据库查询</span>
          </div>
        }
        className="chat-card"
      >
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
            messages={messages}
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

export default Dashboard;