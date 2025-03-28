import React from 'react';
import { List, Spin, Button } from 'antd';
import { LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import MessageItem from './MessageItem';
import '../styles/Message.css';  // 添加这行

function MessageList({ messages, loading, onEdit, onRate }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    Cookies.remove('token');
    navigate('/login');
  };

  return (
    <div className="messages-container">
      <List
        dataSource={messages}
        renderItem={(item, index) => (
          <MessageItem 
            message={item} 
            index={index} 
            messages={messages}
            onEdit={onEdit}
            onRate={onRate}
          />
        )}
        locale={{ emptyText: '开始你的第一次查询吧！' }}
      />
      {loading && (
        <div className="loading-container">
          <Spin tip="正在查询..." />
        </div>
      )}
    </div>
  );
}

export default MessageList;