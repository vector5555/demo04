import React from 'react';
import { List, Spin } from 'antd';
import MessageItem from './MessageItem';

function MessageList({ messages, loading, onEdit, onRate }) {
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