import React, { useState } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import '../styles/Message.css';

const { TextArea } = Input;

function QueryInput({ loading, onSearch, messages = [] }) {
  const [inputValue, setInputValue] = useState('');
  const isEmpty = messages.length === 0;
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (inputValue.trim()) {
      onSearch(inputValue.trim());
      setInputValue('');
    }
  };

  return (
    <div className={isEmpty ? 'center-input' : 'query-input-container'}>
      <div className="query-input">
        <TextArea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="请输入你的查询..."
          onKeyPress={handleKeyPress}
          autoSize={{ minRows: 1, maxRows: 6 }}
        />
        <Button 
          type="primary"
          icon={<SendOutlined />}
          loading={loading}
          onClick={handleSubmit}
        >
          发送
        </Button>
      </div>
    </div>
  );
}

export default QueryInput;